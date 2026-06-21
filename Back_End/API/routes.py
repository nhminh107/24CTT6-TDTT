from fastapi import APIRouter, BackgroundTasks, HTTPException,status
import asyncio
import contextlib
from pydantic import BaseModel,Field
import os
import pandas as pd
from typing import List, Optional
import traceback
import json
import time
import uuid



from datetime import datetime,timezone
import firebase_admin
from firebase_admin import credentials, firestore


from Back_End.Core.parsing import LLMParser
from Back_End.Core.QA_Chatbot import ChatBot
from Back_End.Core.Filter import RestaurantFilter
from Back_End.Core.scoring_class import RestaurantScorer
from Back_End.Core.final_result import FinalResultLLM
from Back_End.Core.weight_update import Weight_Update
from Back_End.Core.Maps import suggest_locations, get_place_detail
from Back_End.Database.database import ChromaDBManager
from Back_End.Core.semantic_cache import SemanticCacheManager
from Back_End.Core.auth_handler import get_db
from Back_End.Core.user_manager import UserManager
from Back_End.Core.itinerary_manager import ItineraryManager
from Back_End.Core.health_mapping import HealthRiskDetector
from Back_End.Core.multimodal_prompt import MultimodalPromptTransformer
from typing import Literal

# Trả về giờ UTC có chứa thông tin múi giờ UTC rõ ràng (timezone-aware)
current_time = datetime.now(timezone.utc)

router = APIRouter(prefix="/api/v1", tags=["Main Pipeline"])

# KHỞI TẠO ĐỐI TƯỢNG CACHE MANAGER (Khởi tạo 1 lần dùng chung)
cache_manager = SemanticCacheManager()
user_manager = UserManager()
itinerary_manager = ItineraryManager()
last_results_by_user = {}
health_risk_detector = HealthRiskDetector()
_restaurant_df_cache = None
_restaurant_json_cache = None
_restaurant_data_mtime = None

def _api_log(request_id: str, message: str):
    print(f"[API_LOG][{request_id}] {message}")

def _elapsed_ms(start_time: float) -> int:
    return int((time.perf_counter() - start_time) * 1000)

def _restaurant_data_path() -> str:
    return os.path.join(os.getcwd(), 'Back_End', 'Database', 'data.json')

def _get_restaurant_df_cached() -> pd.DataFrame:
    global _restaurant_df_cache, _restaurant_json_cache, _restaurant_data_mtime

    data_path = _restaurant_data_path()
    if not os.path.exists(data_path):
        raise FileNotFoundError(data_path)

    current_mtime = os.path.getmtime(data_path)
    if _restaurant_df_cache is None or _restaurant_data_mtime != current_mtime:
        df = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
        _restaurant_df_cache = df
        _restaurant_json_cache = json.loads(df.to_json(orient='records', force_ascii=False))
        _restaurant_data_mtime = current_mtime
        print(f"[API_LOG][DATA_CACHE] Loaded {len(df)} restaurants from data.json")

    return _restaurant_df_cache.copy(deep=False)

def _get_restaurant_json_cached() -> list:
    global _restaurant_json_cache
    _get_restaurant_df_cached()
    return list(_restaurant_json_cache or [])

async def _save_assistant_message_background(user_id: str, chat_id: str | None, content: str, restaurants: list | None = None):
    if not chat_id:
        return
    try:
        metadata = {"restaurants": restaurants} if restaurants is not None else None
        await user_manager.add_message(user_id, chat_id, "assistant", content, metadata=metadata)
    except Exception as exc:
        print(f"[API_LOG][BACKGROUND] Failed to save assistant message: {exc}")

async def _save_user_message_background(user_id: str, chat_id: str | None, content: str):
    if not chat_id:
        return
    try:
        await user_manager.add_message(user_id, chat_id, "user", content)
    except Exception as exc:
        print(f"[API_LOG][BACKGROUND] Failed to save user message: {exc}")

async def _auto_save_itinerary_background(user_id: str, final_result_list: list):
    try:
        seen_meals = []
        for item in final_result_list:
            meal = item.get("meal")
            meal_key = str(meal).strip().lower()
            if not meal_key or meal_key in seen_meals:
                continue
            seen_meals.append(meal_key)
            first_res = item.copy()
            first_res["is_auto"] = True
            await itinerary_manager.select_restaurant(user_id, meal, first_res)
    except Exception as exc:
        print(f"[API_LOG][BACKGROUND] Failed to auto-save itinerary: {exc}")

def _empty_reason_and_suggestions(parsed_json: dict, filtered_data: dict, scored_candidates: pd.DataFrame, health_profile: dict):
    requested_meals = [m.get('meal') for m in parsed_json.get('meals_detail', []) if isinstance(m, dict)]
    available_meals = scored_candidates['meal'].unique().tolist() if scored_candidates is not None and not scored_candidates.empty else []
    missing_meals = [m for m in requested_meals if m not in available_meals]
    budget = parsed_json.get("budget") or 0
    forbidden_tags = health_profile.get("forbidden_tags", []) if isinstance(health_profile, dict) else []

    if not filtered_data or all(df is None or df.empty for df in filtered_data.values()):
        if forbidden_tags:
            return (
                "health_or_distance_too_strict",
                [
                    "Bạn có thể thử chuyển hồ sơ sức khỏe sang chế độ thoải mái hơn nếu không có dị ứng nghiêm trọng.",
                    "Thử mở rộng khu vực tìm kiếm hoặc chọn một địa điểm trung tâm hơn.",
                    "Giảm bớt yêu cầu về món/loại quán để BMI có thêm lựa chọn."
                ]
            )
        return (
            "too_far_or_no_candidates",
            [
                "Thử mở rộng bán kính tìm kiếm hoặc đổi sang khu vực gần trung tâm hơn.",
                "Bỏ bớt yêu cầu về loại quán hoặc món cụ thể.",
                "Thử nhập tên món phổ biến hơn."
            ]
        )

    if missing_meals:
        return (
            "missing_meal_candidates",
            [
                f"Không đủ quán phù hợp cho bữa: {', '.join(str(m) for m in missing_meals)}.",
                "Bạn có thể đổi loại quán cho bữa bị thiếu hoặc bỏ yêu cầu món quá cụ thể.",
                "Thử tăng khu vực tìm kiếm hoặc chọn vị trí khác."
            ]
        )

    if budget and budget < 100000:
        return (
            "budget_too_low",
            [
                "Ngân sách hiện khá thấp so với dữ liệu quán. Thử tăng ngân sách một chút.",
                "Chọn quán ăn nhanh, ăn vặt hoặc quán bình dân để có nhiều lựa chọn hơn."
            ]
        )

    return (
        "no_rankable_candidates",
        [
            "Thử mô tả yêu cầu ngắn gọn hơn, ví dụ món ăn + khu vực + ngân sách.",
            "Bỏ bớt tiêu chí không gian hoặc phong cách nếu đang quá cụ thể.",
            "Thử tìm một bữa trước, sau đó thêm các bữa còn lại."
        ]
    )

def _extract_context_from_result(result):
    """
    Trích xuất thông tin tóm tắt (ID, Tên, Tags) để làm ngữ cảnh cho AI lượt sau.
    """
    if not isinstance(result, list):
        return []
    context_list = []
    seen_ids = set()
    for item in result:
        if not isinstance(item, dict):
            continue
        rid = str(item.get("id"))
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        context_list.append({
            "id": rid,
            "name": item.get("name"),
            "description": item.get("semantic_text", "")
        })
    return context_list


def _apply_exclusions(filtered_data: dict, exclude_ids: list):
    if not filtered_data or not exclude_ids:
        return filtered_data
    
    # Nếu exclude_ids là danh sách các dictionary (từ context mới), trích xuất lại ID
    if exclude_ids and isinstance(exclude_ids[0], dict):
        exclude_set = {str(item.get("id")) for item in exclude_ids if item.get("id") is not None}
    else:
        exclude_set = {str(rid) for rid in exclude_ids if rid is not None}

    if not exclude_set:
        return filtered_data
    result = {}
    for meal_tag, df in filtered_data.items():
        if df is None or df.empty or 'id' not in df.columns:
            result[meal_tag] = df
            continue
        filtered_df = df[~df['id'].astype(str).isin(exclude_set)]
        result[meal_tag] = filtered_df if not filtered_df.empty else df
    return result

def _normalize_parsed_intent(parsed_json: dict) -> dict:
    if not isinstance(parsed_json, dict):
        return parsed_json

    meals_detail = parsed_json.get("meals_detail")
    if not isinstance(meals_detail, list) or not meals_detail:
        return parsed_json

    snack_types = {
        "quan nuoc", "tiem banh", "an vat", "tra sua",
        "cafe", "quan ca phe"
    }

    normalized = []
    index_map = {}

    for item in meals_detail:
        if not isinstance(item, dict):
            continue

        meal_raw = item.get("meal")
        if not meal_raw:
            meal_raw = "any"

        meal_key = str(meal_raw).strip().lower()

        types_raw = item.get("type") or []
        if isinstance(types_raw, str):
            types_raw = [types_raw]
        types = [t for t in types_raw if t]

        semantic_raw = item.get("semantic_query")
        semantic = semantic_raw.strip() if isinstance(semantic_raw, str) else ""

        # Preserve the dish field
        dish = item.get("dish", "")

        is_snack = any(str(t).strip().lower() in snack_types for t in types)
        if is_snack and meal_key in {"any", "xế", "chiều"}:
            meal_key = "xế"

        if meal_key in index_map:
            existing = normalized[index_map[meal_key]]
            existing_types = existing.get("type") or []
            if isinstance(existing_types, str):
                existing_types = [existing_types]
            merged_types = list(existing_types)
            for t in types:
                if t not in merged_types:
                    merged_types.append(t)
            existing["type"] = merged_types

            existing_sem = existing.get("semantic_query")
            existing_sem = existing_sem.strip() if isinstance(existing_sem, str) else ""
            if existing_sem and semantic:
                if semantic not in existing_sem:
                    existing["semantic_query"] = f"{existing_sem}, {semantic}"
            else:
                existing["semantic_query"] = existing_sem or semantic or None
            
            # Merge dish if needed (though usually one dish per meal is expected)
            if dish:
                existing_dish = existing.get("dish", "")
                if existing_dish and dish not in existing_dish:
                    existing["dish"] = f"{existing_dish}, {dish}"
                else:
                    existing["dish"] = dish
        else:
            normalized.append({
                "meal": meal_key,
                "type": types,
                "semantic_query": semantic or None,
                "dish": dish
            })
            index_map[meal_key] = len(normalized) - 1

    if normalized:
        parsed_json["meals_detail"] = normalized
        parsed_json["num_meals"] = len(normalized)

    return parsed_json

#Định nghĩa cấu trúc dữ liệu (Pydantic Models)
class UserRequest(BaseModel):
    prompt: str
    place_id: Optional[str] = None  #ID địa điểm người dùng chọn từ Maps
    user_id: str
    chat_id: Optional[str] = None # ID session chat hiện tại

class MultimodalTransformRequest(BaseModel):
    prompt: str
    image_url: str

class ItinerarySelectRequest(BaseModel):
    user_id: str
    meal: str
    restaurant_data: dict

class ReorderItem(BaseModel):
    id: str
    meal: Optional[str] = None

class ItineraryReorderRequest(BaseModel):
    user_id: str
    ordered_items: List[ReorderItem]

class ItineraryImportRequest(BaseModel):
    user_id: str
    share_id: str

#Endpoints xử lý chính

@router.post("/multimodal/transform")
async def transform_multimodal_prompt(request: MultimodalTransformRequest):
    text_prompt = request.prompt.strip()
    image_url = request.image_url.strip()

    if not text_prompt:
        raise HTTPException(status_code=400, detail="Bạn cần nhập yêu cầu bằng chữ khi gửi kèm ảnh.")
    if not image_url:
        raise HTTPException(status_code=400, detail="Thiếu ảnh để phân tích.")

    try:
        transformer = MultimodalPromptTransformer()
        result = await transformer.transform(text_prompt, image_url)
        return {
            "status": "success",
            "transformed_prompt": result["transformed_prompt"],
            "image_summary": result.get("image_summary"),
            "confidence": result.get("confidence"),
            "beta_notice": "Tính năng phân tích ảnh đang ở giai đoạn beta. OCR/nhận diện món có thể sai nếu ảnh mờ hoặc menu khó đọc."
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Không thể phân tích ảnh: {str(exc)}")

@router.get("/itinerary/{user_id}")
async def get_itinerary(user_id: str):
    itinerary = await itinerary_manager.get_itinerary(user_id)
    return {"status": "success", "itinerary": itinerary}

@router.post("/itinerary/select")
async def select_restaurant(request: ItinerarySelectRequest):
    success = await itinerary_manager.select_restaurant(request.user_id, request.meal, request.restaurant_data)
    if success:
        return {"status": "success", "message": f"Đã thêm quán vào bữa {request.meal}."}
    else:
        raise HTTPException(status_code=500, detail="Không thể lưu lựa chọn.")

@router.post("/itinerary/reorder")
async def reorder_itinerary(request: ItineraryReorderRequest):
    success = await itinerary_manager.reorder_itinerary(request.user_id, [item.model_dump() for item in request.ordered_items])
    if success:
        return {"status": "success", "message": "Đã cập nhật thứ tự lịch trình."}
    else:
        raise HTTPException(status_code=500, detail="Không thể cập nhật thứ tự.")

@router.post("/itinerary/import-shared")
async def import_shared_itinerary(request: ItineraryImportRequest):
    success = await itinerary_manager.import_shared_itinerary(request.user_id, request.share_id)
    if success:
        # Tự động tạo một session chat mới khi import thành công
        chat_id = await user_manager.create_chat_session(request.user_id)
        
        # Lấy lại dữ liệu itinerary vừa import để gửi kèm vào chat metadata
        itinerary_data = await itinerary_manager.get_itinerary(request.user_id)
        
        # Thêm tin nhắn chào mừng kèm bối cảnh và danh sách quán
        welcome_msg = "Chào bạn! Tôi đã nhập lộ trình mà bạn chia sẻ vào tài khoản. Đây là danh sách các quán trong lộ trình. Bạn có muốn điều chỉnh hay hỏi thêm gì không?"
        await user_manager.add_message(
            request.user_id, 
            chat_id, 
            "assistant", 
            welcome_msg, 
            metadata={"restaurants": itinerary_data}
        )
        
        return {
            "status": "success", 
            "message": "Đã nhập lộ trình thành công.",
            "chat_id": chat_id
        }
    else:
        raise HTTPException(status_code=500, detail="Không thể nhập lộ trình.")

@router.delete("/itinerary/{user_id}/{item_id}")
async def delete_meal(user_id: str, item_id: str):
    success = await itinerary_manager.delete_meal(user_id, item_id)
    if success:
        return {"status": "success", "message": f"Đã xóa bữa ăn khỏi lịch trình."}
    else:
        raise HTTPException(status_code=500, detail="Không thể xóa bữa ăn.")

@router.delete("/itinerary/{user_id}")
async def reset_itinerary(user_id: str):
    success = await itinerary_manager.reset_itinerary(user_id)
    if success:
        return {"status": "success", "message": "Đã đặt lại lịch trình."}
    else:
        raise HTTPException(status_code=500, detail="Không thể đặt lại lịch trình.")

@router.post("/prompt")
async def process_prompt(request: UserRequest, background_tasks: BackgroundTasks):
    """
    Kết nối toàn bộ luồng xử lý từ Prompt đến Lịch trình.
    """
    request_id = uuid.uuid4().hex[:10]
    total_start = time.perf_counter()
    print(f"\n[API_LOG][{request_id}] Starting /prompt process for user_id: {request.user_id}")
    _api_log(request_id, f"User prompt: '{request.prompt}'")
    if request.place_id:
        _api_log(request_id, f"Specified place_id: {request.place_id}")

    try:
        # Lấy lịch trình hiện tại và các kết quả gợi ý gần nhất để cung cấp ngữ cảnh cho AI
        current_itinerary = await itinerary_manager.get_itinerary(request.user_id)
        last_suggestions = last_results_by_user.get(request.user_id, [])
        
        itinerary_context = ""
        if current_itinerary:
            itinerary_context += f"\nĐây là lịch trình hiện tại của người dùng (đã chọn): {json.dumps(current_itinerary, ensure_ascii=False)}"
        
        if last_suggestions:
            itinerary_context += f"\nĐây là các quán ăn bạn vừa gợi ý ở lượt trước (nhưng người dùng chưa chọn hoặc có thể không thích): {json.dumps(last_suggestions, ensure_ascii=False)}"
            itinerary_context += "\nNếu người dùng nói 'quán này', 'chỗ này', 'ở đây' kèm theo thái độ tiêu cực, hãy hiểu là họ đang nói về các quán vừa gợi ý trên."

        if itinerary_context:
            itinerary_context = f"\n[CONTEXT]{itinerary_context}\n[END CONTEXT]"

        formatted_history = []
        if request.chat_id:
            # Lấy lịch sử chat trước đó để cung cấp ngữ cảnh; prompt hiện tại đã được truyền riêng.
            raw_history = await user_manager.get_chat_messages(request.user_id, request.chat_id)
            if raw_history:
                for msg in raw_history:
                    formatted_history.append({
                        "role": msg.get("role"),
                        "content": msg.get("content")
                    })
                formatted_history = formatted_history[-10:]
                print(f"[API_LOG] Chat history loaded: {len(formatted_history)} messages.")
                for i, m in enumerate(formatted_history):
                    print(f"  - [{m['role']}] {m['content'][:50]}...")
            background_tasks.add_task(
                _save_user_message_background,
                request.user_id,
                request.chat_id,
                request.prompt
            )

        # 0. Intent Routing: Phân luồng ý định
        step_start = time.perf_counter()
        _api_log(request_id, "Step 0: Intent Routing started...")
        chatbot = ChatBot()
        routing_res_json = await chatbot.routing(request.prompt, history=formatted_history)
        routing_res = json.loads(routing_res_json)
        
        user_intent = routing_res.get("user_intent")
        is_poor_info = routing_res.get("isPoorInfo", 0)
        _api_log(request_id, f"Intent detected: {user_intent} | isPoorInfo: {is_poor_info} | ms={_elapsed_ms(step_start)}")

        if user_intent == "Search" and is_poor_info == 1:
            _api_log(request_id, "User intent: Search, but info is poor. Asking for more info.")
            poor_info_msg = "Dạ, tôi chưa hiểu rõ ý định tìm kiếm của bạn. Bạn có thể cho tôi thêm thông tin như: bạn muốn ăn món gì, ở đâu, hoặc ngân sách khoảng bao nhiêu không ạ?"
            if request.chat_id:
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, poor_info_msg)
            return {
                "status": "poor_info",
                "message": poor_info_msg,
                "result": [],
                "request_id": request_id
            }
            
        if user_intent == "System_QA":
            step_start = time.perf_counter()
            _api_log(request_id, "User intent: System_QA. Handling system guidance...")
            system_qa_response = await chatbot.handle_system_qa(request.prompt)
            if request.chat_id:
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, system_qa_response)
            _api_log(request_id, f"System_QA completed | ms={_elapsed_ms(step_start)} | total_ms={_elapsed_ms(total_start)}")
            return {
                "status": "success_qa",
                "message": system_qa_response,
                "result": [],
                "request_id": request_id
            }

        if user_intent == "Knowledge_QA":
            step_start = time.perf_counter()
            _api_log(request_id, "User intent: Knowledge_QA. Handling nutrition/food knowledge...")
            knowledge_qa_response = await chatbot.handle_knowledge_qa(
                request.prompt, 
                history=formatted_history,
                system_context=itinerary_context
            )
            if request.chat_id:
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, knowledge_qa_response)
            _api_log(request_id, f"Knowledge_QA completed | ms={_elapsed_ms(step_start)} | total_ms={_elapsed_ms(total_start)}")
            return {
                "status": "success_qa",
                "message": knowledge_qa_response,
                "result": [],
                "request_id": request_id
            }
            

        if user_intent == "Out_Scope":
            _api_log(request_id, "User intent: Out_Scope. Refusing to answer...")
            out_scope_msg = "Dạ, hiện tại tôi là trợ lý chuyên sâu về ẩm thực, sức khỏe và du lịch. Tôi xin phép không trả lời các nội dung ngoài phạm vi này ạ. Bạn có muốn tìm quán ăn hay hỏi gì về dinh dưỡng không?"
            if request.chat_id:
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, out_scope_msg)
            return {
                "status": "out_scope",
                "message": out_scope_msg,
                "result": [],
                "request_id": request_id
            }

        # 1. LLM Parsing: Hiểu ý định người dùng
        step_start = time.perf_counter()
        _api_log(request_id, "Step 1: LLM Parsing started...")
        parser = LLMParser()
        parse_task = asyncio.create_task(parser.JSON_response(
            user_prompt=request.prompt,
            history=formatted_history,
            system_context=itinerary_context
        )) 

        # Kiểm tra nếu là tọa độ GPS trực tiếp (định dạng geo_lat_lng)
        is_gps_location = request.place_id and request.place_id.startswith("geo_")
        
        loc_task = (
            asyncio.create_task(get_place_detail(request.place_id))
            if request.place_id and not is_gps_location
            else None
        )

        parsed_json = await parse_task
        if not parsed_json:
            print("[API_LOG] Error: LLM Parsing failed to return a result.")
            raise HTTPException(status_code=400, detail="AI không thể phân tích yêu cầu này.")

        parsed_json = _normalize_parsed_intent(parsed_json)
        _api_log(request_id, f"LLM Parsing completed | ms={_elapsed_ms(step_start)} | result={json.dumps(parsed_json, ensure_ascii=False)}")

        # 2. Xử lý vị trí người dùng (User Location)
        user_lat, user_lng = 10.774773681750506, 106.72470566530203 

        if is_gps_location:
            try:
                # Trích xuất lat, lng từ chuỗi "geo_lat_lng"
                parts = request.place_id.split("_")
                if len(parts) >= 3:
                    user_lat = float(parts[1])
                    user_lng = float(parts[2])
                    print(f"[API_LOG] Extracted GPS coordinates: ({user_lat}, {user_lng})")
                else:
                    print(f"[API_LOG] Warning: Invalid GPS format '{request.place_id}', using default.")
            except (ValueError, IndexError) as e:
                print(f"[API_LOG] Error parsing GPS coordinates: {e}, using default.")
        elif loc_task:
            print("[API_LOG] Fetching place details from Maps API...")
            loc_detail = await loc_task
            if loc_detail.get("status") == "success":
                user_lat = loc_detail["data"]["lat"]
                user_lng = loc_detail["data"]["lng"]
                print(f"[API_LOG] Maps API coordinates: ({user_lat}, {user_lng})")
            else:
                print(f"[API_LOG] Warning: Could not fetch place details, using default coordinates.")
        else:
            print(f"[API_LOG] Using default coordinates: ({user_lat}, {user_lng})")

        # --- CHIẾN LƯỢC CÁCH 1: GEOCODING LOCATION PREFERENCE ---
        # Nếu AI phát hiện người dùng yêu cầu một khu vực cụ thể (location_pref)
        location_pref = parsed_json.get("location_pref")
        if location_pref:
            print(f"[API_LOG] User specified a location preference: '{location_pref}'. Geocoding...")
            # Bỏ qua các từ quá chung chung
            ignored_broad = ["tp hcm", "hồ chí minh", "sài gòn", "tp.hcm", "việt nam", "hà nội", "đà nẵng"]
            if location_pref.lower().strip() not in ignored_broad:
                try:
                    # 1. Tìm place_id cho khu vực này
                    suggestions = await suggest_locations(location_pref)
                    if suggestions:
                        # Lấy gợi ý đầu tiên
                        first_place_id = suggestions[0][1]
                        # 2. Lấy tọa độ chi tiết
                        loc_detail = await get_place_detail(first_place_id)
                        if loc_detail.get("status") == "success":
                            user_lat = loc_detail["data"]["lat"]
                            user_lng = loc_detail["data"]["lng"]
                            print(f"[API_LOG] Geocoded '{location_pref}' to: ({user_lat}, {user_lng}). Overriding search base.")
                        else:
                            print(f"[API_LOG] Could not get details for '{location_pref}'. Keeping current base.")
                    else:
                        print(f"[API_LOG] No suggestions found for '{location_pref}'. Keeping current base.")
                except Exception as e:
                    print(f"[API_LOG] Error during geocoding location_pref: {e}")

        # Normalize budget
        budget_value = parsed_json.get("budget", 0)
        if budget_value is None: budget_value = 0
        elif isinstance(budget_value, str):
            try: budget_value = int(budget_value)
            except ValueError: budget_value = 0
        elif isinstance(budget_value, float):
            budget_value = int(budget_value)
        _api_log(request_id, f"Normalized budget: {budget_value}")

        # Fetch health profile
        step_start = time.perf_counter()
        _api_log(request_id, f"Fetching health profile for user: {request.user_id}")
        user_health_profile = await fetch_user_health_profile(request.user_id)
        forbidden_tags = user_health_profile.get("forbidden_tags", [])
        
        detected_tags = health_risk_detector.detect(request.prompt) 
        
        total_tags_set = set(forbidden_tags) | set(detected_tags)

        # Sắp xếp lại danh sách đã gộp tổng hợp
        forbidden_tags_final = sorted(list(total_tags_set))
        
        print(f"USER HEALTH FILLER MODE: {user_health_profile["diet_mode"]}" )
        
        # Dùng `forbidden_tags_final` để nối thành chuỗi health_key mới nhất
        health_key = ",".join(forbidden_tags_final) if forbidden_tags_final else "none"
        
        _api_log(request_id, f"Health profile/tags completed | ms={_elapsed_ms(step_start)} | detected={detected_tags} | final={forbidden_tags_final} | health_key={health_key}")
        
        user_health_profile["forbidden_tags"] = forbidden_tags_final

        wants_alternative = parsed_json.get("wants_alternative", False)
        feedback_reason = parsed_json.get("feedback_reason")
        
        weight_engine = Weight_Update(user_lat=user_lat, user_lng=user_lng, feedback_reason=feedback_reason)
        weight_task = asyncio.create_task(weight_engine.build_buff_weights())

        exclude_ids = last_results_by_user.get(request.user_id, []) if wants_alternative else []
        bypass_cache = wants_alternative and bool(exclude_ids)
        _api_log(request_id, f"Wants alternative: {wants_alternative}, Feedback reason: {feedback_reason}, Bypass cache: {bypass_cache}")

        diet_mode = user_health_profile.get("diet_mode", "casual")

        print(f"USER HEALTH FILTER MODE: {diet_mode}")

        # Check cache
        step_start = time.perf_counter()
        _api_log(request_id, "Checking semantic cache...")
        cache_task = asyncio.to_thread(
            cache_manager.check_cache,
            prompt=request.prompt,
            lat=user_lat,
            lng=user_lng,
            budget=budget_value,
            health_key=health_key,
            diet_mode=diet_mode
        )

        df_task = asyncio.create_task(asyncio.to_thread(_get_restaurant_df_cached))

        cached_result = await cache_task
        if cached_result and not bypass_cache:
            _api_log(request_id, f"Cache hit | ms={_elapsed_ms(step_start)}")
            weight_task.cancel()
            df_task.cancel()
            with contextlib.suppress(asyncio.CancelledError): await weight_task
            with contextlib.suppress(asyncio.CancelledError): await df_task
            last_results_by_user[request.user_id] = _extract_context_from_result(cached_result)

            # Lưu tin nhắn của assistant nếu có chat_id (cho Cache Hit)
            if request.chat_id:
                msg_content = f"Dạ, tôi đã tìm thấy kết quả phù hợp từ bộ nhớ tạm cho bạn."
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, msg_content, cached_result)

            _api_log(request_id, f"/prompt completed from cache | total_ms={_elapsed_ms(total_start)}")

            return {
                "status": "success",
                "parsed_intent": parsed_json,
                "result": cached_result,
                "request_id": request_id,
                "meta": {"cache_hit": True}
            }
        
        _api_log(request_id, f"Cache miss | ms={_elapsed_ms(step_start)}. Proceeding with filtering and scoring.")
        
        # 3. Data Filtering
        step_start = time.perf_counter()
        _api_log(request_id, "Step 3: Filtering restaurants...")
        df_raw = await df_task
        _api_log(request_id, f"Total restaurants in DB: {len(df_raw)}")
        
        # Chiến lược mở rộng bán kính: Bắt đầu nhỏ, nếu rỗng thì tăng dần
        search_distance = 3.0 if location_pref else 10.0
        _api_log(request_id, f"Initial search distance: {search_distance}km")

        filter_engine = RestaurantFilter(
            df=df_raw, 
            prompt=parsed_json, 
            user_lat=user_lat, 
            user_lng=user_lng,
            user_health_profie=user_health_profile,
            max_distance=search_distance
        )
        filtered_data = await asyncio.to_thread(filter_engine.run_filter_pipeline)
        
        # Kiểm tra nếu rỗng hoàn toàn trên tất cả bữa ăn
        is_completely_empty = all(df.empty for df in filtered_data.values()) if filtered_data else True
        
        if is_completely_empty:
            expanded_distance = 5.0 if location_pref else 15.0
            _api_log(request_id, f"No results at {search_distance}km. Expanding search to {expanded_distance}km...")
            
            # Cập nhật bán kính mới và chạy lại pipeline
            filter_engine.max_distance = expanded_distance
            filtered_data = await asyncio.to_thread(filter_engine.run_filter_pipeline)

        for m_tag, m_df in filtered_data.items():
            _api_log(request_id, f"Meal '{m_tag}': found {len(m_df)} candidates.")

        if exclude_ids:
            _api_log(request_id, f"Applying exclusions for {len(exclude_ids)} IDs.")
            filtered_data = _apply_exclusions(filtered_data, exclude_ids)
        
        buff_weights = await weight_task
        _api_log(request_id, f"Filtering completed | ms={_elapsed_ms(step_start)} | weight_buffers={json.dumps(buff_weights, ensure_ascii=False)}")

        # 4. Scoring & Optimization
        step_start = time.perf_counter()
        _api_log(request_id, "Step 4: Scoring candidates...")
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        scored_candidates = scorer.run_scoring_pipeline(filtered_data, parsed_json, buff_weights, diet_mode=user_health_profile.get('diet_mode', None))
        
        if not scored_candidates.empty:
            for m_tag in filtered_data.keys():
                count = len(scored_candidates[scored_candidates['meal'] == m_tag])
                _api_log(request_id, f"Meal '{m_tag}': {count} candidates scored.")
        else:
            _api_log(request_id, "Warning: scored_candidates is empty!")
        _api_log(request_id, f"Scoring completed | ms={_elapsed_ms(step_start)}")

        step_start = time.perf_counter()
        _api_log(request_id, "LLM Selection for final itinerary...")
        selector = FinalResultLLM()
        final_itinerary = await selector.run_final_selection(
            scored_candidates,
            request.prompt,
            parsed_json,
            max_per_meal = 3 if wants_alternative else 1
        )
        _api_log(request_id, f"Final selection completed | ms={_elapsed_ms(step_start)}")

        # 5. Result processing
        if final_itinerary.empty:
            _api_log(request_id, "Result: No suitable restaurants found (Final itinerary empty).")
            # Check why it might be empty
            requested_meals = [m.get('meal') for m in parsed_json.get('meals_detail', [])]
            available_meals = scored_candidates['meal'].unique().tolist() if not scored_candidates.empty else []
            missing_meals = [m for m in requested_meals if m not in available_meals]
            if missing_meals:
                _api_log(request_id, f"Reason: No candidates found for meals: {missing_meals}")
            
            empty_reason, empty_suggestions = _empty_reason_and_suggestions(
                parsed_json,
                filtered_data,
                scored_candidates,
                user_health_profile
            )
            error_msg = "Không tìm thấy quán ăn nào phù hợp với yêu cầu và ngân sách của bạn."
            if request.chat_id:
                background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, error_msg)
            _api_log(request_id, f"Empty response | reason={empty_reason} | total_ms={_elapsed_ms(total_start)}")

            return {
                "status": "empty",
                "message": error_msg,
                "result": [],
                "reason": empty_reason,
                "suggestions": empty_suggestions,
                "request_id": request_id
            }
        
        final_result_json_str = final_itinerary.to_json(orient='records', force_ascii=False)
        final_result_list = json.loads(final_result_json_str)
        _api_log(request_id, f"Final itinerary contains {len(final_result_list)} items.")

        # Save to cache
        if not bypass_cache:
            _api_log(request_id, "Saving result to cache...")
            cache_manager.save_cache(
                prompt=request.prompt,
                lat=user_lat,
                lng=user_lng,
                budget=budget_value,
                health_key=health_key,
                diet_mode=diet_mode,
                result_json=final_result_list
            )

        last_results_by_user[request.user_id] = _extract_context_from_result(final_result_list)
        _api_log(request_id, f"/prompt process completed successfully for user_id: {request.user_id} | total_ms={_elapsed_ms(total_start)}")

        # Tự động cập nhật Lịch trình với kết quả đầu tiên của mỗi bữa ăn
        background_tasks.add_task(_auto_save_itinerary_background, request.user_id, final_result_list)

        # Lưu tin nhắn của assistant nếu có chat_id
        if request.chat_id:
            meals_found = final_itinerary['meal'].unique().tolist()
            meals_str = ", ".join(meals_found)
            msg_content = f"Dạ, tôi đã tìm thấy các quán ăn phù hợp cho bữa {meals_str} theo yêu cầu của bạn. Bạn xem qua nhé!"
            background_tasks.add_task(_save_assistant_message_background, request.user_id, request.chat_id, msg_content, final_result_list)

        return {
            "status": "success",
            "parsed_intent": parsed_json,
            "result": final_result_list,
            "request_id": request_id,
            "meta": {"cache_hit": False}
        }
        
    except Exception as e:
        _api_log(request_id, f"!!! CRITICAL ERROR in /prompt after {_elapsed_ms(total_start)}ms: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# --- Các Endpoints hỗ trợ Maps ---

@router.get("/restaurants/all")
async def get_all_restaurants():
    """
    Trả về toàn bộ danh sách quán ăn để hiển thị trên bản đồ.
    """
    try:
        data = await asyncio.to_thread(_get_restaurant_json_cached)
        return {"status": "success", "data": data}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Không tìm thấy cơ sở dữ liệu quán ăn.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc dữ liệu: {str(e)}")

@router.get("/maps/suggestions")
async def get_map_suggestions(q: str):
    results = await suggest_locations(q)
    return [{"description": d, "place_id": p} for d, p in results]

@router.get("/maps/place-detail")
async def get_map_place_detail(place_id: str):
    result = await get_place_detail(place_id)
    return result


current_dir = os.path.dirname(os.path.abspath(__file__))
# Quay lại 1 cấp vào Back_End, sau đó vào Database
json_path = os.path.join(os.path.dirname(current_dir), "Database", "serviceAccountKey.json")


# Khởi tạo Firebase Admin SDK (Chỉ khởi tạo một lần duy nhất)
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", json_path))
    firebase_admin.initialize_app(cred)

db = firestore.client()
user_router = APIRouter(prefix="/api/user", tags=["Health Profile"])

# BẢNG ÁNH XẠ CỐ ĐỊNH ĐỂ TỐI ƯU TOKEN

CONDITION_MAP = {
    "Gout": {"main": ["Red_Meat"], "potential": ["Seafood", "Shellfish", "Alcohol_Pub"]},
    "Dạ dày": {"main": ["Spicy"], "potential": ["DeepFried_Oily", "Alcohol_Pub"]},
    "Dạ dày / Đại tràng": {"main": ["Spicy"], "potential": ["DeepFried_Oily", "Alcohol_Pub"]},
    "Tiểu đường (Diabetes)": {"main": ["High_Sugar", "Refined_Carbs"], "potential": ["DeepFried_Oily"]},
    "Béo phì / Giảm cân": {"main": ["DeepFried_Oily", "High_Sugar", "Refined_Carbs"], "potential": ["Alcohol_Pub"]},
    "Cao huyết áp": {
    "main": [
        "High_Sodium",
        "DeepFried_Oily",
        "Processed_Food"
    ],
    "potential": [
        "Alcohol_Pub",
        "High_Sugar"
    ]
    }
}

ALLERGY_MAP = {
    "Đậu phộng": {"main": ["Peanuts_Nuts"], "potential": []},
    "Bột mì": {"main": ["Gluten_Present"], "potential": ["Refined_Carbs"]},
    "Dị ứng Hải sản": {"main": ["Seafood"], "potential": ["Shellfish"]},
    "Dị ứng Hải sản vỏ cứng": {"main": ["Shellfish"], "potential": ["Seafood"]},
    "Dị ứng Đậu phộng / Hạt": {"main": ["Peanuts_Nuts"], "potential": []},
    "Bất dung nạp Lactose": {"main": ["Dairy_Product"], "potential": []},
    "Dị ứng Gluten (Celiac)": {"main": ["Gluten_Present"], "potential": ["Refined_Carbs"]},
    "Dị ứng Hạt cây (Hạnh nhân/Óc chó)": {"main": ["Peanuts_Nuts"], "potential": []},
    "Dị ứng Đạm sữa động vật": {"main": ["Dairy_Product"], "potential": []}
}

ALL_AVAILABLE_TAGS = [
    "Red_Meat", "Seafood", "Alcohol_Pub", "Shellfish", "Spicy", "DeepFried_Oily",
    "High_Sugar", "Refined_Carbs", "Low_GI_Diet", "Peanuts_Nuts", "Dairy_Product", "Gluten_Present","High_Sodium"
]


class ProfileCreateRequest(BaseModel):
    user_id: str
    diet_mode: str
    selected_conditions: List[str] = Field(default_factory=list)
    selected_allergies: List[str] = Field(default_factory=list)
    more_descriptions: Optional[str] = ""


async def call_llm_to_extract_tags(description: str) -> List[str]:

    llm = LLMParser()

    print("Đang gọi LLM")
    
    llm_forbidden_tags = await llm.phrase_health_description(description)

    if llm_forbidden_tags != []:
        return llm_forbidden_tags

    return []

@user_router.post("/health-profile/{user_id}", status_code=status.HTTP_200_OK)
async def save_user_health_profile(user_id: str, payload: ProfileCreateRequest):
    forbidden_set = set()
    
    has_selections = len(payload.selected_conditions) > 0 or len(payload.selected_allergies) > 0
    has_description = payload.more_descriptions and payload.more_descriptions.strip() != ""
    
    if has_selections:
        for condition in payload.selected_conditions:
            if condition in CONDITION_MAP:
                forbidden_set.update(CONDITION_MAP[condition]["main"])
                forbidden_set.update(CONDITION_MAP[condition]["potential"])
                
        for allergy in payload.selected_allergies:
            if allergy in ALLERGY_MAP:
                forbidden_set.update(ALLERGY_MAP[allergy]["main"])
                forbidden_set.update(ALLERGY_MAP[allergy]["potential"])
                
    elif not has_selections and has_description:
        llm_tags = await call_llm_to_extract_tags(payload.more_descriptions)
        forbidden_set.update(llm_tags)
        
    db_data = {
        "user_id": user_id,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "diet_mode": payload.diet_mode,
        "more_description": payload.more_descriptions,
        "raw_selections": {
            "selected_conditions": payload.selected_conditions,
            "selected_allergies": payload.selected_allergies
        },
        "forbidden_tags": list(forbidden_set)
    }
    
    try:
        # ✅ Sửa: subcollection của user
        db.collection("users").document(user_id) \
          .collection("user_health_profile").document("profile") \
          .set(db_data)
        
        return {
            "status": "success",
            "message": "Cập nhật hồ sơ sức khỏe lên Firebase thành công.",
            "forbidden_tags_generated": list(forbidden_set)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firestore error: {str(e)}")


@user_router.get("/health-profile/{user_id}")
async def get_user_health_profile(user_id: str):
    try:
        # ✅ Sửa: subcollection của user
        doc_ref = db.collection("users").document(user_id) \
                    .collection("user_health_profile").document("profile")
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy hồ sơ sức khỏe trên Firebase cho user_id: {user_id}"
            )
            
        record = doc.to_dict()
        
        return {
            "user_id": record.get("user_id"),
            "updated_at": record.get("updated_at"),
            "diet_mode": record.get("diet_mode"),
            "more_description": record.get("more_description"),
            "raw_selections": record.get("raw_selections"),
            "forbidden_tags": record.get("forbidden_tags")
        }
        
    except HTTPException as he:
        if he.status_code == 404:
            return {
                "user_id": user_id,
                "diet_mode": "casual",
                "more_description": "",
                "raw_selections": {
                    "selected_conditions": [],
                    "selected_allergies": []
                },
                "forbidden_tags": []
            }
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi tải hồ sơ từ Firebase: {str(e)}")


async def fetch_user_health_profile(user_id: str):
    # ✅ Sửa: subcollection của user
    doc_ref = db.collection("users").document(user_id) \
                .collection("user_health_profile").document("profile")
    doc = doc_ref.get()

    if not doc.exists:
        return {
            "user_id": user_id,
            "diet_mode": "casual",
            "more_description": "",
            "raw_selections": {
                "selected_conditions": [],
                "selected_allergies": []
            },
            "forbidden_tags": []
        }

    return doc.to_dict()

# --- Chat History Endpoints ---

@user_router.post("/chat/new/{user_id}")
async def create_new_chat(user_id: str):
    # Reset lịch trình khi tạo cuộc trò chuyện mới
    await itinerary_manager.reset_itinerary(user_id)
    chat_id = await user_manager.create_chat_session(user_id)
    if chat_id:
        return {"status": "success", "chat_id": chat_id}
    else:
        raise HTTPException(status_code=500, detail="Không thể tạo cuộc trò chuyện mới.")

@user_router.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str):
    history = await user_manager.get_chat_history(user_id)
    return {"status": "success", "history": history}

@user_router.get("/chat/{user_id}/{chat_id}/messages")
async def get_chat_messages(user_id: str, chat_id: str):
    messages = await user_manager.get_chat_messages(user_id, chat_id)
    return {"status": "success", "messages": messages}

@user_router.delete("/chat/{user_id}/{chat_id}")
async def delete_chat(user_id: str, chat_id: str):
    success = await user_manager.delete_chat_session(user_id, chat_id)
    if success:
        return {"status": "success", "message": "Đã xóa cuộc trò chuyện."}
    else:
        raise HTTPException(status_code=500, detail="Không thể xóa cuộc trò chuyện.")


class RestaurantCommentRequest(BaseModel):
    user_id: str
    # username đã bị loại bỏ: Backend tự lấy từ collection `users` (Denormalization)
    content: str

class EditCommentRequest(BaseModel):
    user_id: str
    content: str

class DeleteCommentRequest(BaseModel):
    user_id: str

@user_router.post("/restaurant-comment/{restaurant_id}", status_code=status.HTTP_200_OK)
async def create_restaurant_comment(restaurant_id: str, payload: RestaurantCommentRequest):
    """
    Tạo một bình luận mới cho nhà hàng.

    Chiến lược Denormalization:
    - Thay vì để Frontend gửi username/avatar/role lên (dễ bị giả mạo),
      Backend tự truy vấn collection `users` để lấy thông tin chính xác
      rồi ghi thẳng vào document comment.
    - Frontend (onSnapshot) sẽ tự nhận dữ liệu mới ngay lập tức.
    """
    try:
        # ── 1. LẤY THÔNG TIN USER TỪ FIRESTORE (Nguồn dữ liệu tin cậy) ──
        user_ref = db.collection("users").document(payload.user_id)
        user_doc = user_ref.get()

        # Giá trị mặc định phòng trường hợp user chưa có profile đầy đủ
        display_name = "Người dùng"
        photo_url = None
        user_role = "user"

        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            display_name = user_data.get("display_name") or display_name
            photo_url    = user_data.get("photo_url")
            user_role    = user_data.get("role", "user")

        # ── 2. ĐẢM BẢO DOCUMENT GỐC CỦA NHÀ HÀNG TỒN TẠI ──
        restaurant_ref = db.collection("restaurant_comments").document(restaurant_id)
        if not restaurant_ref.get().exists:
            restaurant_ref.set({
                "restaurant_id": restaurant_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
            })

        # ── 3. GHI COMMENT KÈM DỮ LIỆU ĐÃ DENORMALIZE ──
        comment_data = {
            "user_id":       payload.user_id,
            # Thông tin được denormalize — Frontend không cần gọi thêm
            "username":      display_name,
            "user_avatar":   photo_url,
            "user_role":     user_role,
            # Nội dung bình luận
            "content":       payload.content,
            "like_count":    0,
            "dislike_count": 0,
            "edited":        False,
            "created_at":    datetime.utcnow().isoformat() + "Z",
            "updated_at":    None,
        }

        restaurant_ref.collection("comments").add(comment_data)

        # onSnapshot ở Frontend sẽ tự nhận document mới này ngay lập tức
        return {
            "status": "success",
            "message": "Comment created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi tạo comment: {str(e)}")

# ── API GET /restaurant-comment/{restaurant_id} ĐÃ BỊ XÓA ──
# Frontend giờ dùng Firebase Client SDK (onSnapshot) để lắng nghe
# sub-collection `comments` trực tiếp theo thời gian thực.
# Việc gộp dữ liệu user (username, avatar, role) được xử lý bằng
# chiến lược Denormalization tại thời điểm tạo comment (POST).
# Không cần endpoint này nữa.

@user_router.put("/restaurant-comment/{restaurant_id}/{comment_id}", status_code=status.HTTP_200_OK)
async def edit_restaurant_comment(restaurant_id: str, comment_id: str, payload: EditCommentRequest):
    try:
        comment_ref = (
            db.collection("restaurant_comments")
              .document(restaurant_id)
              .collection("comments")
              .document(comment_id)
        )

        comment_doc = comment_ref.get()
        if not comment_doc.exists:
            raise HTTPException(status_code=404, detail="Comment không tồn tại")

        stored = comment_doc.to_dict() or {}
        if stored.get("user_id") != payload.user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền sửa comment này")

        comment_ref.update({
            "content": payload.content,
            "edited": True,
            "updated_at": datetime.utcnow().isoformat() + "Z",
        })

        return {
            "status": "success",
            "message": "Comment updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi sửa comment: {str(e)}")

@user_router.delete("/restaurant-comment/{restaurant_id}/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_restaurant_comment(restaurant_id: str, comment_id: str, payload: DeleteCommentRequest):
    try:
        # 1. Lấy thông tin comment từ Firestore
        comment_ref = (
            db.collection("restaurant_comments")
              .document(restaurant_id)
              .collection("comments")
              .document(comment_id)
        )

        comment_doc = comment_ref.get()
        if not comment_doc.exists:
            raise HTTPException(status_code=404, detail="Comment không tồn tại")

        stored = comment_doc.to_dict() or {}
        comment_owner_id = stored.get("user_id") # ID của người viết comment

        # 2. KIỂM TRA QUYỀN ADMIN CỦA NGƯỜI GỬI REQUEST
        is_admin = False
        if payload.user_id:
            user_ref = db.collection("users").document(payload.user_id)
            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict() or {}
                # Nếu trường role trong document user là "admin" thì set True
                if user_data.get("role") == "admin":
                    is_admin = True

        # 3. ĐIỀU KIỆN XÓA: Phải là CHỦ COMMENT hoặc là ADMIN
        # Nếu KHÔNG PHẢI chủ comment VÀ CŨNG KHÔNG PHẢI admin -> Chặn lại bắn lỗi 403
        if comment_owner_id != payload.user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xóa comment này")

        # Hợp lệ thì tiến hành xóa
        comment_ref.delete()

        # Nếu hệ thống của bạn có dùng Realtime Socket (Socket.IO) để đồng bộ UI, 
        # await sio.emit("comment_deleted", {"comment_id": comment_id}, room=restaurant_id)

        return {
            "status": "success",
            "message": "Comment deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi xóa comment: {str(e)}")

class VoteRequest(BaseModel):
    user_id: str
    vote_type: Literal["like", "dislike"]  # chỉ nhận 2 giá trị này

@user_router.post("/restaurant-comment/{restaurant_id}/{comment_id}/vote", status_code=status.HTTP_200_OK)
async def vote_restaurant_comment(
    restaurant_id: str,
    comment_id: str,
    payload: VoteRequest
):
    try:
        comment_ref = (
            db.collection("restaurant_comments")
              .document(restaurant_id)
              .collection("comments")
              .document(comment_id)
        )
        vote_ref = comment_ref.collection("votes").document(payload.user_id)

        comment_doc = comment_ref.get()
        if not comment_doc.exists:
            raise HTTPException(status_code=404, detail="Comment không tồn tại")

        existing_vote_doc = vote_ref.get()
        existing_vote = existing_vote_doc.to_dict() if existing_vote_doc.exists else None
        previous_type = existing_vote.get("vote_type") if existing_vote else None

        # --- Xác định thay đổi cần thực hiện ---
        # Case 1: Bấm lại cùng loại → hủy vote
        # Case 2: Bấm loại mới (hoặc lần đầu) → ghi vote mới

        like_delta = 0
        dislike_delta = 0
        new_vote_type = None  # None = xóa vote

        if previous_type == payload.vote_type:
            # Hủy vote: trừ đi 1
            if payload.vote_type == "like":
                like_delta = -1
            else:
                dislike_delta = -1
            new_vote_type = None
        else:
            # Thêm vote mới
            if payload.vote_type == "like":
                like_delta = 1
            else:
                dislike_delta = 1
            # Nếu trước đó đã vote loại khác thì trừ loại cũ
            if previous_type == "like":
                like_delta -= 1
            elif previous_type == "dislike":
                dislike_delta -= 1
            new_vote_type = payload.vote_type

        # --- Thực thi transaction ---
        @firestore.transactional
        
        
        def run_transaction(transaction):
            transaction.update(comment_ref, {
                "like_count": firestore.Increment(like_delta),
                "dislike_count": firestore.Increment(dislike_delta),
            })
            if new_vote_type is None:
                transaction.delete(vote_ref)
            else:
                transaction.set(vote_ref, {
                "vote_type": new_vote_type,
                "voted_at": datetime.now(timezone.utc).isoformat()
            })

        transaction = db.transaction()
        run_transaction(transaction)

        # Lấy lại comment sau khi transaction hoàn tất để trả về số lượng chính xác
        updated_comment_doc = comment_ref.get()
        updated_comment = updated_comment_doc.to_dict() or {}

        # --- Trả về trạng thái mới ---
        action_map = {
            ("like", None):     "like",     # lần đầu like
            ("dislike", None):  "dislike",  # lần đầu dislike
            (None, "like"):     "unliked",  # hủy like
            (None, "dislike"):  "undisliked",
            ("like", "dislike"): "like",    # đổi từ dislike → like
            ("dislike", "like"): "dislike", # đổi từ like → dislike
        }
        action = action_map.get((new_vote_type, previous_type), "updated")

        return {
            "status": "success",
            "action": action,
            "current_vote": new_vote_type,  # null nếu đã hủy
            "like_count": updated_comment.get("like_count", 0),
            "dislike_count": updated_comment.get("dislike_count", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi vote: {str(e)}")


# ── REPORT COMMENT ENDPOINTS ──

class ReportCommentRequest(BaseModel):
    restaurant_id: str
    comment_id: str
    comment_text: str
    reason: str
    user_id: str

class UpdateReportStatusRequest(BaseModel):
    status: Literal["pending", "resolved"]
    type_resolve:Literal["deleted" , "dismissed" ]

@user_router.post("/report-comment", status_code=status.HTTP_201_CREATED)
async def report_comment(payload: ReportCommentRequest):
    """
    Tạo báo cáo bình luận vi phạm.
    
    Dữ liệu được lưu trữ trong collection `reports` ở Firestore.
    """
    try:
        report_id = str(uuid.uuid4())
        
        report_data = {
            "report_id": report_id,
            "restaurant_id": payload.restaurant_id,
            "comment_id": payload.comment_id,
            "comment_text": payload.comment_text,
            "reason": payload.reason,
            "user_id": payload.user_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "type_resolve":"None"
        }
        
        # Lưu báo cáo vào Firestore
        db.collection("reports").document(report_id).set(report_data)
        
        return {
            "status": "success",
            "message": "Báo cáo của bạn đã được gửi. Cảm ơn vì giúp chúng tôi duy trì cộng đồng sạch!",
            "report_id": report_id,
        }
    except Exception as e:
        print(f"[ERROR] Report comment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi gửi báo cáo: {str(e)}")

@user_router.get("/reports")
async def get_reports(status_filter: Optional[str] = None):
    """
    Lấy danh sách báo cáo bình luận (Admin only).
    
    Query params:
    - status: "pending" | "resolved" (optional)
    """
    try:
        # TODO: Thêm kiểm tra admin role tại đây (nên từ JWT token)
        
        query = db.collection("reports")
        
        if status_filter and status_filter in ["pending", "resolved"]:
            query = query.where("status", "==", status_filter)
        
        # Sắp xếp theo ngày tạo (mới nhất trước)
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        
        docs = query.stream()
        reports = []
        
        for doc in docs:
            report = doc.to_dict()
            reports.append(report)
        
        return {
            "status": "success",
            "data": reports,
        }
    except Exception as e:
        print(f"[ERROR] Get reports failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi tải báo cáo: {str(e)}")

@user_router.patch("/reports/{report_id}")
async def update_report_status(report_id: str, payload: UpdateReportStatusRequest):
    """
    Cập nhật trạng thái báo cáo (Admin only).
    
    Status: "pending" -> "resolved"
    """
    try:
        # TODO: Thêm kiểm tra admin role tại đây (nên từ JWT token)
        
        report_ref = db.collection("reports").document(report_id)
        report_doc = report_ref.get()
        
        if not report_doc.exists:
            raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
        
        # Cập nhật status
        report_ref.update({
            "status": payload.status,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "type_resolve":payload.type_resolve
        })
        
        return {
            "status": "success",
            "message": f"Cập nhật trạng thái báo cáo thành '{payload.status}' thành công.",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Update report status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi cập nhật báo cáo: {str(e)}")
# 1. Định nghĩa model để nhận dữ liệu từ Frontend
class DeleteReportRequest(BaseModel):
    report_id: str

# 2. Endpoint xử lý xóa báo cáo
@user_router.post("/reports/delete")
async def delete_report(payload: DeleteReportRequest):
    """
    Xóa báo cáo vĩnh viễn khỏi Firestore (Admin only).
    """
    try:
        report_id = payload.report_id
        
        # Tham chiếu đến document báo cáo
        report_ref = db.collection("reports").document(report_id)
        
        # Kiểm tra xem báo cáo có tồn tại không
        if not report_ref.get().exists:
            raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
        
        # Thực hiện xóa
        report_ref.delete()
        
        return {
            "status": "success",
            "message": "Đã xóa báo cáo thành công."
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[ERROR] Delete report failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi xóa báo cáo")