from fastapi import APIRouter, HTTPException
from Back_End.Core.share_manager import ShareManager
from Back_End.Core.itinerary_manager import ItineraryManager

share_router = APIRouter(prefix="/api/v1/itinerary", tags=["Share Itinerary"])
share_manager = ShareManager()
itinerary_manager = ItineraryManager()

@share_router.post("/share/{user_id}")
async def create_shared_itinerary(user_id: str):
    """
    Tạo link chia sẻ cho lịch trình hiện tại của user_id.
    """
    # Lấy lịch trình hiện tại (Sử dụng code có sẵn)
    current_itinerary = await itinerary_manager.get_itinerary(user_id)
    
    if not current_itinerary:
        raise HTTPException(status_code=400, detail="Không có lộ trình nào để chia sẻ.")
        
    # Tạo mã share (GRL4U3)
    share_id = await share_manager.create_share_link(user_id, current_itinerary)
    
    if share_id:
        return {
            "status": "success", 
            "share_id": share_id,
            "message": "Đã tạo mã chia sẻ thành công."
        }
    else:
        raise HTTPException(status_code=500, detail="Không thể tạo mã chia sẻ.")

@share_router.get("/public/{share_id}")
async def get_public_itinerary(share_id: str):
    """
    Lấy dữ liệu lộ trình dựa trên mã chia sẻ (không cần đăng nhập).
    """
    shared_data = await share_manager.get_shared_itinerary(share_id)
    
    if shared_data:
        return {"status": "success", "data": shared_data}
    else:
        raise HTTPException(status_code=404, detail="Không tìm thấy lộ trình này hoặc đã bị xóa.")
