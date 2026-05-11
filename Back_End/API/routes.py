from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import pandas as pd
from typing import List, Optional

from Back_End.Core.parsing import LLMParser
from Back_End.Core.Filter import RestaurantFilter
from Back_End.Core.scoring_class import RestaurantScorer
from Back_End.Core.final_result import FinalResultLLM
from Back_End.Core.Maps import suggest_locations, get_place_detail
from Back_End.Database.database import ChromaDBManager

router = APIRouter(prefix="/api/v1", tags=["Main Pipeline"])

#Định nghĩa cấu trúc dữ liệu (Pydantic Models)
class UserRequest(BaseModel):
    prompt: str
    place_id: Optional[str] = None  #ID địa điểm người dùng chọn từ Maps

#Endpoints xử lý chính

@router.post("/prompt")
async def process_prompt(request: UserRequest):
    """
    Kết nối toàn bộ luồng xử lý từ Prompt đến Lịch trình.
    """
    try:
        # 1. LLM Parsing: Hiểu ý định người dùng
        parser = LLMParser()
        parsed_json = parser.JSON_response(request.prompt)
        if not parsed_json:
            raise HTTPException(status_code=400, detail="AI không thể phân tích yêu cầu này.")

        # 2. Xử lý vị trí người dùng (User Location)
        # Mặc định tọa độ trung tâm nếu người dùng không chọn địa điểm cụ thể
        user_lat, user_lng = 10.7769, 106.7009 
        if request.place_id:
            loc_detail = get_place_detail(request.place_id)
            if loc_detail.get("status") == "success":
                user_lat = loc_detail["data"]["lat"]
                user_lng = loc_detail["data"]["lng"]

        # 3. Data Filtering: Lọc quán ăn phù hợp
        data_path = os.path.join(os.getcwd(), 'Back_End', 'Database', 'data.json')
        if not os.path.exists(data_path):
            raise HTTPException(status_code=500, detail="Không tìm thấy cơ sở dữ liệu quán ăn.")
            
        df_raw = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
        filter_engine = RestaurantFilter(df=df_raw, prompt=parsed_json, user_lat=user_lat, user_lng=user_lng)
        filtered_data = filter_engine.run_filter_pipeline()

        # 4. Scoring & Optimization: Tính lịch trình tối ưu
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        scored_candidates = scorer.run_scoring_pipeline(filtered_data, parsed_json)

        selector = FinalResultLLM()
        final_itinerary = selector.run_final_selection(
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

        return {
            "status": "success",
            "parsed_intent": parsed_json,
            "result": final_itinerary.to_dict(orient='records')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# --- Các Endpoints hỗ trợ Maps ---

@router.get("/maps/suggestions")
async def get_map_suggestions(q: str):
    results = suggest_locations(q)
    return [{"description": d, "place_id": p} for d, p in results]
