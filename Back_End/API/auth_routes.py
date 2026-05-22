from fastapi import APIRouter, Depends, HTTPException
from Back_End.Core.auth_handler import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class SyncUserRequest(BaseModel):
    email: str
    name: Optional[str] = None
    photo_url: Optional[str] = None

@router.post("/sync")
async def sync_user(data: SyncUserRequest, current_user: dict = Depends(get_current_user)):
    """
    Đồng bộ thông tin người dùng từ Firebase vào hệ thống backend.
    """
    uid = current_user.get("uid")
    email = current_user.get("email")
    
    # Ở đây bạn có thể lưu thông tin vào data.json hoặc Database (ChromaDB)
    # Ví dụ: Lưu profile người dùng để cá nhân hóa lịch trình
    
    return {
        "status": "success",
        "message": "User synced successfully",
        "uid": uid,
        "email": email
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Trả về thông tin người dùng hiện tại đang đăng nhập.
    """
    return {
        "status": "success",
        "user": current_user
    }
