from fastapi import APIRouter, HTTPException
import asyncio
import contextlib
from pydantic import BaseModel
import os
import pandas as pd
from typing import List, Optional

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
        if isinstance(budget_value, str):
            try:
                budget_value = int(budget_value)
            except ValueError:
                budget_value = 0

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
        df_raw = await df_task
        filter_engine = RestaurantFilter(df=df_raw, prompt=parsed_json, user_lat=user_lat, user_lng=user_lng)
        filtered_data = await asyncio.to_thread(filter_engine.run_filter_pipeline)

        buff_weights = await weight_task

        # 4. Scoring & Optimization: Tính lịch trình tối ưu
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        scored_candidates = scorer.run_scoring_pipeline(filtered_data, parsed_json, buff_weights)

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
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# --- Các Endpoints hỗ trợ Maps ---

@router.get("/maps/suggestions")
async def get_map_suggestions(q: str):
    results = await suggest_locations(q)
    return [{"description": d, "place_id": p} for d, p in results]
