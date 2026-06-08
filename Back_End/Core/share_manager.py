import string
import random
from datetime import datetime
import asyncio
from typing import Dict, Any, Optional
from Back_End.Core.auth_handler import get_db

class ShareManager:
    def __init__(self):
        self.collection_name = "shared_itineraries"

    def _get_db(self):
        db = get_db()
        if db is None:
            raise Exception("Firestore client is not initialized.")
        return db

    def generate_share_id(self, length=6):
        """Tạo chuỗi ngẫu nhiên VD: GRL4U3"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    async def create_share_link(self, user_id: str, itinerary_data: list) -> Optional[str]:
        return await asyncio.to_thread(self._create_share_link_sync, user_id, itinerary_data)

    def _create_share_link_sync(self, user_id: str, itinerary_data: list) -> Optional[str]:
        try:
            db = self._get_db()
            share_id = self.generate_share_id()
            
            # Đảm bảo mã share_id là duy nhất (nếu trùng thì sinh lại)
            while db.collection(self.collection_name).document(share_id).get().exists:
                share_id = self.generate_share_id()
            
            share_data = {
                "share_id": share_id,
                "user_id": user_id,
                "itinerary": itinerary_data,
                "created_at": datetime.now().isoformat() + "Z"
            }
            
            # Lưu vào bảng/collection riêng biệt (shared_itineraries)
            db.collection(self.collection_name).document(share_id).set(share_data)
            return share_id
            
        except Exception as e:
            print(f">>> ShareManager Error (create_share_link): {e}")
            return None

    async def get_shared_itinerary(self, share_id: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_shared_itinerary_sync, share_id)

    def _get_shared_itinerary_sync(self, share_id: str) -> Optional[Dict[str, Any]]:
        try:
            db = self._get_db()
            doc = db.collection(self.collection_name).document(share_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f">>> ShareManager Error (get_shared_itinerary): {e}")
            return None
