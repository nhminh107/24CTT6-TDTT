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
from Back_End.Core.Filter import RestaurantFilter
from Back_End.Core.scoring_class import RestaurantScorer
from Back_End.Core.final_result import FinalResultLLM
from Back_End.Core.weight_update import Weight_Update
from Back_End.Core.Maps import suggest_locations, get_place_detail
from Back_End.Database.database import ChromaDBManager
from Back_End.Core.semantic_cache import SemanticCacheManager

router = APIRouter(prefix="/api/v1", tags=["Main Pipeline"])

# KHỞI TẠO ĐỐI TƯỢNG CACHE MANAGER (Khởi tạo 1 lần dùng chung)
cache_manager = SemanticCacheManager()
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


def _wants_alternative(prompt: str) -> bool:
    if not prompt:
        return False
    text = prompt.strip().lower()
    keywords = [
        "khác", "khác đi", "khác nữa", "quán khác",
        "đổi quán", "đổi chỗ", "tìm quán khác", "thêm quán"
    ]
    return any(keyword in text for keyword in keywords)


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
    
    
    user_id:str # cái này tôi không biết ae làm login lấy từ đâu

#Endpoints xử lý chính

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
        # 1. LLM Parsing: Hiểu ý định người dùng
        print("[API_LOG] Step 1: LLM Parsing started...")
        parser = LLMParser()
        parse_task = asyncio.create_task(parser.JSON_response(request.prompt))
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

        weight_engine = Weight_Update(user_lat=user_lat, user_lng=user_lng)
        weight_task = asyncio.create_task(weight_engine.build_buff_weights())

        wants_alternative = _wants_alternative(request.prompt)
        exclude_ids = last_results_by_user.get(request.user_id, []) if wants_alternative else []
        bypass_cache = wants_alternative and bool(exclude_ids)
        print(f"[API_LOG] Wants alternative: {wants_alternative}, Bypass cache: {bypass_cache}")

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
            parsed_json
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
            
            return {
                "status": "empty",
                "message": "Không tìm thấy quán ăn nào phù hợp với yêu cầu và ngân sách của bạn.",
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
