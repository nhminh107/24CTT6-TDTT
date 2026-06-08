from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from Back_End.Core.share_manager import ShareManager

router = APIRouter()
share_manager = ShareManager()

class ShareRequest(BaseModel):
    user_id: str
    itinerary_data: list

@router.post("/api/v1/itinerary/share")
async def create_share_link(request: ShareRequest):
    try:
        share_id = await share_manager.create_share_link(request.user_id, request.itinerary_data)
        return {"success": True, "share_id": share_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public/{share_id}")
async def get_shared_itinerary(share_id: str):
    try:
        data = await share_manager.get_shared_itinerary(share_id)
        if data:
            return {"success": True, "data": data}
        else:
            raise HTTPException(status_code=404, detail="Shared itinerary not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
