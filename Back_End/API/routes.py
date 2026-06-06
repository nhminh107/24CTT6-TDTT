from fastapi import APIRouter, HTTPException,status
import asyncio
import contextlib
from pydantic import BaseModel,Field
import os
import pandas as pd
from typing import List, Optional
import traceback
import json



from datetime import datetime
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

router = APIRouter(prefix="/api/v1", tags=["Main Pipeline"])

# KHỞI TẠO ĐỐI TƯỢNG CACHE MANAGER (Khởi tạo 1 lần dùng chung)
cache_manager = SemanticCacheManager()
user_manager = UserManager()
itinerary_manager = ItineraryManager()
last_results_by_user = {}


def _extract_ids_from_result(result):
    if not isinstance(result, list):
        return []
    ids = []
    for item in result:
        if not isinstance(item, dict):
            continue
        rid = item.get("id")
        if rid is None:
            continue
        ids.append(str(rid))
    return list(dict.fromkeys(ids))


def _apply_exclusions(filtered_data: dict, exclude_ids: list):
    if not filtered_data or not exclude_ids:
        return filtered_data
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
            continue

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
        if meal_key in index_map and is_snack:
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

class ItinerarySelectRequest(BaseModel):
    user_id: str
    meal: str
    restaurant_data: dict

#Endpoints xử lý chính

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

@router.delete("/itinerary/{user_id}/{meal}")
async def delete_meal(user_id: str, meal: str):
    success = await itinerary_manager.delete_meal(user_id, meal)
    if success:
        return {"status": "success", "message": f"Đã xóa bữa {meal}."}
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
async def process_prompt(request: UserRequest):
    """
    Kết nối toàn bộ luồng xử lý từ Prompt đến Lịch trình.
    """
    print(f"\n[API_LOG] Starting /prompt process for user_id: {request.user_id}")
    print(f"[API_LOG] User prompt: '{request.prompt}'")
    if request.place_id:
        print(f"[API_LOG] Specified place_id: {request.place_id}")

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
            await user_manager.add_message(request.user_id, request.chat_id, "user", request.prompt)
            # Lấy lịch sử chat để cung cấp ngữ cảnh (lấy 10 tin nhắn gần nhất)
            raw_history = await user_manager.get_chat_messages(request.user_id, request.chat_id)
            if raw_history:
                for msg in raw_history[:-1]: 
                    formatted_history.append({
                        "role": msg.get("role"),
                        "content": msg.get("content")
                    })
                formatted_history = formatted_history[-10:]
                print(f"[API_LOG] Chat history loaded: {len(formatted_history)} messages.")
                for i, m in enumerate(formatted_history):
                    print(f"  - [{m['role']}] {m['content'][:50]}...")

        # 0. Intent Routing: Phân luồng ý định
        print("[API_LOG] Step 0: Intent Routing started...")
        chatbot = ChatBot()
        routing_res_json = await chatbot.routing(request.prompt, history=formatted_history)
        routing_res = json.loads(routing_res_json)
        
        user_intent = routing_res.get("user_intent")
        is_poor_info = routing_res.get("isPoorInfo", 0)

        if user_intent == "Search" and is_poor_info == 1:
            print("[API_LOG] User intent: Search, but info is poor. Asking for more info.")
            poor_info_msg = "Dạ, tôi chưa hiểu rõ ý định tìm kiếm của bạn. Bạn có thể cho tôi thêm thông tin như: bạn muốn ăn món gì, ở đâu, hoặc ngân sách khoảng bao nhiêu không ạ?"
            if request.chat_id:
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", poor_info_msg)
            return {
                "status": "poor_info",
                "message": poor_info_msg,
                "result": []
            }
            
        if user_intent == "System_QA":
            print("[API_LOG] User intent: System_QA. Handling system guidance...")
            system_qa_response = await chatbot.handle_system_qa(request.prompt)
            if request.chat_id:
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", system_qa_response)
            return {
                "status": "success_qa",
                "message": system_qa_response,
                "result": []
            }

        if user_intent == "Knowledge_QA":
            print("[API_LOG] User intent: Knowledge_QA. Handling nutrition/food knowledge...")
            knowledge_qa_response = await chatbot.handle_knowledge_qa(
                request.prompt, 
                history=formatted_history,
                system_context=itinerary_context
            )
            if request.chat_id:
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", knowledge_qa_response)
            return {
                "status": "success_qa",
                "message": knowledge_qa_response,
                "result": []
            }
            

        if user_intent == "Out_Scope":
            print("[API_LOG] User intent: Out_Scope. Refusing to answer...")
            out_scope_msg = "Dạ, hiện tại tôi là trợ lý chuyên sâu về ẩm thực, sức khỏe và du lịch. Tôi xin phép không trả lời các nội dung ngoài phạm vi này ạ. Bạn có muốn tìm quán ăn hay hỏi gì về dinh dưỡng không?"
            if request.chat_id:
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", out_scope_msg)
            return {
                "status": "out_scope",
                "message": out_scope_msg,
                "result": []
            }

        # 1. LLM Parsing: Hiểu ý định người dùng
        print("[API_LOG] Step 1: LLM Parsing started...")
        parser = LLMParser()
        parse_task = asyncio.create_task(parser.JSON_response(
        user_prompt=request.prompt, 
        system_context=itinerary_context
        )) 
        loc_task = (
            asyncio.create_task(get_place_detail(request.place_id))
            if request.place_id
            else None
        )

        parsed_json = await parse_task
        if not parsed_json:
            print("[API_LOG] Error: LLM Parsing failed to return a result.")
            raise HTTPException(status_code=400, detail="AI không thể phân tích yêu cầu này.")

        parsed_json = _normalize_parsed_intent(parsed_json)
        print(f"[API_LOG] LLM Parsing result: {json.dumps(parsed_json, ensure_ascii=False)}")

        # 2. Xử lý vị trí người dùng (User Location)
        user_lat, user_lng = 10.7769, 106.7009 
        if loc_task:
            print("[API_LOG] Fetching place details...")
            loc_detail = await loc_task
            if loc_detail.get("status") == "success":
                user_lat = loc_detail["data"]["lat"]
                user_lng = loc_detail["data"]["lng"]
                print(f"[API_LOG] Place coordinates: ({user_lat}, {user_lng})")
            else:
                print(f"[API_LOG] Warning: Could not fetch place details, using default coordinates.")
        else:
            print(f"[API_LOG] Using default coordinates: ({user_lat}, {user_lng})")

        # Normalize budget
        budget_value = parsed_json.get("budget", 0)
        if budget_value is None: budget_value = 0
        elif isinstance(budget_value, str):
            try: budget_value = int(budget_value)
            except ValueError: budget_value = 0
        elif isinstance(budget_value, float):
            budget_value = int(budget_value)
        print(f"[API_LOG] Normalized budget: {budget_value}")

        # Fetch health profile
        print(f"[API_LOG] Fetching health profile for user: {request.user_id}")
        user_health_profile = await fetch_user_health_profile(request.user_id)
        forbidden_tags = user_health_profile.get("forbidden_tags", [])
        health_key = ",".join(sorted(forbidden_tags)) if forbidden_tags else "none"
        print(f"[API_LOG] Health key: {health_key}")

        wants_alternative = parsed_json.get("wants_alternative", False)
        feedback_reason = parsed_json.get("feedback_reason")
        
        weight_engine = Weight_Update(user_lat=user_lat, user_lng=user_lng, feedback_reason=feedback_reason)
        weight_task = asyncio.create_task(weight_engine.build_buff_weights())

        exclude_ids = last_results_by_user.get(request.user_id, []) if wants_alternative else []
        bypass_cache = wants_alternative and bool(exclude_ids)
        print(f"[API_LOG] Wants alternative: {wants_alternative}, Feedback reason: {feedback_reason}, Bypass cache: {bypass_cache}")

        # Check cache
        print("[API_LOG] Checking semantic cache...")
        cache_task = asyncio.to_thread(
            cache_manager.check_cache,
            prompt=request.prompt,
            lat=user_lat,
            lng=user_lng,
            budget=budget_value,
            health_key=health_key
        )

        data_path = os.path.join(os.getcwd(), 'Back_End', 'Database', 'data.json')
        if not os.path.exists(data_path):
            print(f"[API_LOG] Error: Database file not found at {data_path}")
            raise HTTPException(status_code=500, detail="Không tìm thấy cơ sở dữ liệu quán ăn.")

        df_task = asyncio.create_task(asyncio.to_thread(pd.read_json, data_path, encoding='utf-8', dtype={'id': str}))

        cached_result = await cache_task
        if cached_result and not bypass_cache:
            print("[API_LOG] ⚡ CACHE HIT! Returning cached result.")
            weight_task.cancel()
            df_task.cancel()
            with contextlib.suppress(asyncio.CancelledError): await weight_task
            with contextlib.suppress(asyncio.CancelledError): await df_task
            last_results_by_user[request.user_id] = _extract_ids_from_result(cached_result)

            # Lưu tin nhắn của assistant nếu có chat_id (cho Cache Hit)
            if request.chat_id:
                msg_content = f"Dạ, tôi đã tìm thấy kết quả phù hợp từ bộ nhớ tạm cho bạn."
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", msg_content, metadata={"restaurants": cached_result})

            return {
                "status": "success",
                "parsed_intent": parsed_json,
                "result": cached_result
            }
        
        print("[API_LOG] CACHE MISS. Proceeding with filtering and scoring.")
        
        # 3. Data Filtering
        print("[API_LOG] Step 3: Filtering restaurants...")
        df_raw = await df_task
        print(f"[API_LOG] Total restaurants in DB: {len(df_raw)}")
        
        filter_engine = RestaurantFilter(df=df_raw, prompt=parsed_json, user_lat=user_lat, user_lng=user_lng,user_health_profie=user_health_profile)
        filtered_data = await asyncio.to_thread(filter_engine.run_filter_pipeline)
        
        for m_tag, m_df in filtered_data.items():
            print(f"[API_LOG] Meal '{m_tag}': found {len(m_df)} candidates after initial filter.")

        if exclude_ids:
            print(f"[API_LOG] Applying exclusions for {len(exclude_ids)} IDs.")
            filtered_data = _apply_exclusions(filtered_data, exclude_ids)
        
        buff_weights = await weight_task
        print(f"[API_LOG] Weight buffers calculated: {json.dumps(buff_weights, ensure_ascii=False)}")

        # 4. Scoring & Optimization
        print("[API_LOG] Step 4: Scoring candidates...")
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        scored_candidates = scorer.run_scoring_pipeline(filtered_data, parsed_json, buff_weights, diet_mode=user_health_profile.get('diet_mode', None))
        
        if not scored_candidates.empty:
            for m_tag in filtered_data.keys():
                count = len(scored_candidates[scored_candidates['meal'] == m_tag])
                print(f"[API_LOG] Meal '{m_tag}': {count} candidates scored.")
        else:
            print("[API_LOG] Warning: scored_candidates is empty!")

        print("[API_LOG] LLM Selection for final itinerary...")
        selector = FinalResultLLM()
        final_itinerary = await selector.run_final_selection(
            scored_candidates,
            request.prompt,
            parsed_json,
            max_per_meal = 3 if wants_alternative else 1
        )

        # 5. Result processing
        if final_itinerary.empty:
            print("[API_LOG] Result: No suitable restaurants found (Final itinerary empty).")
            # Check why it might be empty
            requested_meals = [m.get('meal') for m in parsed_json.get('meals_detail', [])]
            available_meals = scored_candidates['meal'].unique().tolist() if not scored_candidates.empty else []
            missing_meals = [m for m in requested_meals if m not in available_meals]
            if missing_meals:
                print(f"[API_LOG] Reason: No candidates found for meals: {missing_meals}")
            
            error_msg = "Không tìm thấy quán ăn nào phù hợp với yêu cầu và ngân sách của bạn."
            if request.chat_id:
                await user_manager.add_message(request.user_id, request.chat_id, "assistant", error_msg)

            return {
                "status": "empty",
                "message": error_msg,
                "result": []
            }
        
        final_result_json_str = final_itinerary.to_json(orient='records', force_ascii=False)
        final_result_list = json.loads(final_result_json_str)
        print(f"[API_LOG] Final itinerary contains {len(final_result_list)} items.")

        # Save to cache
        if not bypass_cache:
            print("[API_LOG] Saving result to cache...")
            cache_manager.save_cache(
                prompt=request.prompt,
                lat=user_lat,
                lng=user_lng,
                budget=budget_value,
                health_key=health_key,
                result_json=final_result_list
            )

        last_results_by_user[request.user_id] = _extract_ids_from_result(final_result_list)
        print(f"[API_LOG] /prompt process completed successfully for user_id: {request.user_id}\n")

        # Tự động cập nhật Lịch trình với kết quả đầu tiên của mỗi bữa ăn
        for meal in final_itinerary['meal'].unique():
            meal_results = [r for r in final_result_list if r.get('meal') == meal]
            if meal_results:
                first_res = meal_results[0]
                await itinerary_manager.select_restaurant(request.user_id, meal, first_res)

        # Lưu tin nhắn của assistant nếu có chat_id
        if request.chat_id:
            meals_found = final_itinerary['meal'].unique().tolist()
            meals_str = ", ".join(meals_found)
            msg_content = f"Dạ, tôi đã tìm thấy các quán ăn phù hợp cho bữa {meals_str} theo yêu cầu của bạn. Bạn xem qua nhé!"
            await user_manager.add_message(request.user_id, request.chat_id, "assistant", msg_content, metadata={"restaurants": final_result_list})

        return {
            "status": "success",
            "parsed_intent": parsed_json,
            "result": final_result_list
        }
        
    except Exception as e:
        print(f"[API_LOG] !!! CRITICAL ERROR in /prompt: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# --- Các Endpoints hỗ trợ Maps ---

@router.get("/maps/suggestions")
async def get_map_suggestions(q: str):
    results = await suggest_locations(q)
    return [{"description": d, "place_id": p} for d, p in results]


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
    "Low GI Diet": {"main": [], "potential": ["Low_GI_Diet"]}
}

ALLERGY_MAP = {
    "Đậu phộng": {"main": ["Peanuts_Nuts"], "potential": []},
    "Bột mì": {"main": ["Gluten_Present"], "potential": ["Refined_Carbs"]},
    "Dị ứng Hải sản": {"main": ["Seafood"], "potential": ["Shellfish"]},
    "Dị ứng Hải sản vỏ cứng": {"main": ["Shellfish"], "potential": ["Seafood"]},
    "Dị ứng Đậu phộng / Hạt": {"main": ["Peanuts_Nuts"], "potential": []},
    "Bất dung nạp Lactose": {"main": ["Dairy_Product"], "potential": []},
    "Dị ứng Gluten (Celiac)": {"main": ["Gluten_Present"], "potential": ["Refined_Carbs"]}
}

ALL_AVAILABLE_TAGS = [
    "Red_Meat", "Seafood", "Alcohol_Pub", "Shellfish", "Spicy", "DeepFried_Oily",
    "High_Sugar", "Refined_Carbs", "Low_GI_Diet", "Peanuts_Nuts", "Dairy_Product", "Gluten_Present"
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
                "diet_mode": "strict",
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
            "diet_mode": "strict",
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
