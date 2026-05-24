from fastapi import APIRouter, Depends, HTTPException
from Back_End.Core.auth_handler import get_current_user
from Back_End.Core.user_manager import UserManager
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
user_manager = UserManager()

class SyncUserRequest(BaseModel):
    email: str
    name: Optional[str] = None
    photo_url: Optional[str] = None

@router.post("/sync")
async def sync_user(data: SyncUserRequest, current_user: dict = Depends(get_current_user)):
    """
    Đồng bộ thông tin người dùng từ Firebase vào Firestore thông qua UserManager.
    """
    uid = current_user.get("uid")
    
    success = await user_manager.sync_user(
        uid=uid,
        email=data.email or current_user.get("email"),
        name=data.name or current_user.get("name"),
        photo_url=data.photo_url or current_user.get("picture")
    )

    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Không thể đồng bộ dữ liệu người dùng vào hệ thống."
        )

    return {
        "status": "success",
        "message": "Đồng bộ người dùng thành công",
        "uid": uid
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Trả về thông tin người dùng hiện tại từ Token.
    Có thể mở rộng để lấy thêm data từ Firestore bằng user_manager.get_user_profile(uid)
    """
    return {
        "status": "success",
        "user": current_user
    }
