from fastapi import APIRouter, HTTPException,status
import asyncio
import contextlib
from pydantic import BaseModel,Field
import os
import pandas as pd
from typing import List, Optional
import traceback



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

user_health_profile_mockup={
        "user_id": "24120417",
        "updated_at": "2026-05-21T15:50:00Z",
        "diet_mode": "strict", 
        "more_description": "Đôi khi tôi hay bị nóng trong người và mọc mụn",
        "raw_selections": {
            "selected_conditions": [
            "Gout",
            "Dạ dày"
            ],
            "selected_allergies": [
            "Đậu phộng",
            "Bột mì"
            ]
        },
        "forbidden_tags": [
            "DeepFried_Oily",
            "Peanuts_Nuts",
            "Alcohol_Pub",
            "Shellfish",
            "Spicy"
        ]
    } 


router = APIRouter(prefix="/api/v1", tags=["Main Pipeline"])

# KHỞI TẠO ĐỐI TƯỢNG CACHE MANAGER (Khởi tạo 1 lần dùng chung)
cache_manager = SemanticCacheManager()

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
    try:
        # 1. LLM Parsing: Hiểu ý định người dùng
        parser = LLMParser()
        parse_task = asyncio.create_task(parser.JSON_response(request.prompt))
        loc_task = (
            asyncio.create_task(get_place_detail(request.place_id))
            if request.place_id
            else None
        )

        parsed_json = await parse_task
        if not parsed_json:
            raise HTTPException(status_code=400, detail="AI không thể phân tích yêu cầu này.")

        # 2. Xử lý vị trí người dùng (User Location)
        # Mặc định tọa độ trung tâm nếu người dùng không chọn địa điểm cụ thể
        user_lat, user_lng = 10.7769, 106.7009 
        if loc_task:
            loc_detail = await loc_task
            if loc_detail.get("status") == "success":
                user_lat = loc_detail["data"]["lat"]
                user_lng = loc_detail["data"]["lng"]
        # KIỂM TRA BỘ NHỚ ĐỆM
        #Xử lý lấy budget từ parsed_json an toàn
        budget_value = parsed_json.get("budget", 0)

        # Trường hợp 1: Nếu LLM trả về khóa "budget" nhưng giá trị là None/null
        if budget_value is None:
            budget_value = 0
            
        # Trường hợp 2: Nếu LLM trả về dạng chuỗi (ví dụ: "50000")
        elif isinstance(budget_value, str):
            try:
                budget_value = int(budget_value)
            except ValueError:
                budget_value = 0
                
        # Trường hợp 3: Nếu nó là float (ví dụ: 150000.0), ép về int luôn cho đồng bộ với ChromaDB
        elif isinstance(budget_value, float):
            budget_value = int(budget_value)

        weight_engine = Weight_Update(user_lat=user_lat, user_lng=user_lng)
        weight_task = asyncio.create_task(weight_engine.build_buff_weights())

        cache_task = asyncio.to_thread(
            cache_manager.check_cache,
            prompt=request.prompt,
            lat=user_lat,
            lng=user_lng,
            budget=budget_value
        )

        data_path = os.path.join(os.getcwd(), 'Back_End', 'Database', 'data.json')
        if not os.path.exists(data_path):
            raise HTTPException(status_code=500, detail="Không tìm thấy cơ sở dữ liệu quán ăn.")

        df_task = asyncio.to_thread(pd.read_json, data_path, encoding='utf-8', dtype={'id': str})

        cached_result = await cache_task
        if cached_result:
            weight_task.cancel()
            df_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await weight_task
            with contextlib.suppress(asyncio.CancelledError):
                await df_task
            return {
                "status": "success",
                "parsed_intent": parsed_json,
                "result": cached_result
            }

        
        
        # 3. Data Filtering: Lọc quán ăn phù hợp
        
        #Lấy hồ sơ sức khỏe của user
        # user_health_profile= await fetch_user_health_profile(request.user_id)
        user_health_profile=user_health_profile_mockup
        
        df_raw = await df_task
        filter_engine = RestaurantFilter(df=df_raw, prompt=parsed_json, user_lat=user_lat, user_lng=user_lng,user_health_profie=user_health_profile)
        filtered_data = await asyncio.to_thread(filter_engine.run_filter_pipeline)

        buff_weights = await weight_task

        # 4. Scoring & Optimization: Tính lịch trình tối ưu
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        scored_candidates = scorer.run_scoring_pipeline(filtered_data, parsed_json, buff_weights,diet_mode=user_health_profile.get('diet_mode',None))

        selector = FinalResultLLM()
        final_itinerary = await selector.run_final_selection(
            scored_candidates,
            request.prompt,
            parsed_json
        )

        # 5. Trả kết quả về cho FrontEnd
        if final_itinerary.empty:
            return {
                "status": "empty",
                "message": "Không tìm thấy quán ăn nào phù hợp với yêu cầu và ngân sách của bạn.",
                "result": []
            }

        # Chuyển đổi kết quả thành dạng danh sách từ điển
        final_result_list = final_itinerary.to_dict(orient='records')

        # LƯU LẠI CACHE CHO LẦN DÙNG SAU
        cache_manager.save_cache(
            prompt=request.prompt,
            lat=user_lat,
            lng=user_lng,
            budget=budget_value,
            result_json=final_result_list
        )

        return {
            "status": "success",
            "parsed_intent": parsed_json,
            "result": final_result_list
        }
        
    except Exception as e:
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


def call_llm_to_extract_tags(description: str) -> List[str]:
    # VIết một hàm trong class paring.py
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
        llm_tags = call_llm_to_extract_tags(payload.more_descriptions)
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
        # Lưu hoặc ghi đè (upsert) tài liệu trong Firestore với ID là user_id
        db.collection("user_health_profile").document(user_id).set(db_data)
        
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
        doc_ref = db.collection("user_health_profile").document(user_id)
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
        if he.status_code==404:
            user_health_profile = {
                "user_id": user_id,
                "diet_mode": "strict",          # Hoặc "casual" 
                "more_description": "",
                "raw_selections": {
                    "selected_conditions": [],
                    "selected_allergies": []
                },
                "forbidden_tags": []            # Không cấm tag nào
            }
            return user_health_profile
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi tải hồ sơ từ Firebase: {str(e)}")
    
    
async def fetch_user_health_profile(user_id: str):
    doc_ref = db.collection("user_health_profile").document(user_id)
    doc = doc_ref.get()

    if not doc.exists:
        
        user_health_profile = {
            "user_id": user_id,
            "diet_mode": "strict",          # Hoặc "casual" 
            "more_description": "",
            "raw_selections": {
                "selected_conditions": [],
                "selected_allergies": []
            },
            "forbidden_tags": []            # Không cấm tag nào
        }
        return user_health_profile

    return doc.to_dict()