from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
from Back_End.Core.auth_handler import db

class UserManager:
    def __init__(self):
        self._db = db

    def _get_collection(self):
        if self._db is None:
            raise Exception("Firestore client is not initialized.")
        return self._db.collection("users")

    async def sync_user(self, uid: str, email: str, name: Optional[str] = None, photo_url: Optional[str] = None) -> bool:
        """
        Đồng bộ hoặc tạo mới thông tin người dùng.
        Sử dụng asyncio.to_thread để không chặn event loop của FastAPI khi gọi Firestore SDK (đồng bộ).
        """
        return await asyncio.to_thread(self._sync_user_sync, uid, email, name, photo_url)

    def _sync_user_sync(self, uid: str, email: str, name: Optional[str], photo_url: Optional[str]) -> bool:
        try:
            col = self._get_collection()
            user_ref = col.document(uid)
            
            # Log để debug (có thể xóa sau khi ổn định)
            print(f">>> Syncing User: {uid}, Email: {email}, Name Provided: {name}")

            user_data = {
                "uid": uid,
                "email": email,
                "photo_url": photo_url,
                "last_login": datetime.now(),
                "updated_at": datetime.now()
            }

            # Xử lý Display Name thông minh hơn
            if name and name.strip():
                # Nếu có tên hợp lệ, luôn cập nhật
                user_data["display_name"] = name
            else:
                # Nếu không có tên truyền vào, kiểm tra xem trong DB đã có tên chưa
                doc = user_ref.get()
                if doc.exists:
                    existing_data = doc.to_dict()
                    # Nếu đã có tên rồi thì không ghi đè bằng email prefix nữa
                    if not existing_data.get("display_name"):
                        user_data["display_name"] = email.split("@")[0] if email else "User"
                else:
                    # Nếu là user mới hoàn toàn thì mới dùng fallback email
                    user_data["display_name"] = email.split("@")[0] if email else "User"
            
            # Merge=True: Chỉ cập nhật các trường có trong user_data
            user_ref.set(user_data, merge=True)
            return True
        except Exception as e:
            print(f">>> UserManager Error (sync_user): {e}")
            return False

    async def update_user_data(self, uid: str, data: Dict[str, Any]) -> bool:
        """
        Cập nhật các trường dữ liệu tùy chỉnh cho user.
        """
        return await asyncio.to_thread(self._update_user_data_sync, uid, data)

    def _update_user_data_sync(self, uid: str, data: Dict[str, Any]) -> bool:
        try:
            col = self._get_collection()
            data["updated_at"] = datetime.now()
            col.document(uid).update(data)
            return True
        except Exception as e:
            print(f">>> UserManager Error (update_user_data): {e}")
            return False

    async def get_user_profile(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin profile từ Firestore.
        """
        return await asyncio.to_thread(self._get_user_profile_sync, uid)

    def _get_user_profile_sync(self, uid: str) -> Optional[Dict[str, Any]]:
        try:
            col = self._get_collection()
            doc = col.document(uid).get()
            if doc.exists:
                data = doc.to_dict()
                
                # Lấy allergies từ subcollection user_health_profile
                health_doc = col.document(uid).collection("user_health_profile").document("profile").get()
                if health_doc.exists:
                    health_data = health_doc.to_dict()
                    data["allergies"] = health_data.get("raw_selections", {}).get("selected_allergies", [])
                else:
                    data["allergies"] = []
                    
                return data
            return None
        except Exception as e:
            print(f">>> UserManager Error (get_user_profile): {e}")
            return None

    async def update_user_profile(self, uid: str, update_data: dict) -> bool:
        """
        Cập nhật thông tin profile của user: name, avatar, allergies.
        """
        return await asyncio.to_thread(self._update_user_profile_sync, uid, update_data)

    def _update_user_profile_sync(self, uid: str, update_data: dict) -> bool:
        try:
            col = self._get_collection()
            
            # 1. Cập nhật thông tin cơ bản (name, avatar) vào document user
            data_to_update = {"updated_at": datetime.now()}
            if "name" in update_data and update_data["name"] is not None:
                data_to_update["display_name"] = update_data["name"]
            if "avatar" in update_data and update_data["avatar"] is not None:
                data_to_update["photo_url"] = update_data["avatar"]

            col.document(uid).set(data_to_update, merge=True)
            
            # 2. Cập nhật allergies vào subcollection user_health_profile/profile
            if "allergies" in update_data and update_data["allergies"] is not None:
                allergies = update_data["allergies"]
                health_ref = col.document(uid).collection("user_health_profile").document("profile")
                health_doc = health_ref.get()
                
                if health_doc.exists:
                    health_ref.update({
                        "raw_selections.selected_allergies": allergies,
                        "updated_at": datetime.utcnow().isoformat() + "Z"
                    })
                else:
                    health_ref.set({
                        "user_id": uid,
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                        "diet_mode": "strict",
                        "more_description": "",
                        "raw_selections": {
                            "selected_conditions": [],
                            "selected_allergies": allergies
                        },
                        "forbidden_tags": []
                    })
                    
            return True
        except Exception as e:
            print(f">>> UserManager Error (update_user_profile): {e}")
            return False
