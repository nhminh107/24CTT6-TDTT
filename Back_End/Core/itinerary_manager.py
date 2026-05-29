from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
from Back_End.Core.auth_handler import db

class ItineraryManager:
    def __init__(self):
        self._db = db

    def _get_collection(self, user_id: str):
        if self._db is None:
            raise Exception("Firestore client is not initialized.")
        return self._db.collection("users").document(user_id).collection("current_itinerary")

    async def get_itinerary(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lấy lộ trình hiện tại của người dùng.
        """
        return await asyncio.to_thread(self._get_itinerary_sync, user_id)

    def _get_itinerary_sync(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            col = self._get_collection(user_id)
            docs = col.order_by("timestamp").get()
            results = []
            for doc in docs:
                data = doc.to_dict()
                # Chuyển đổi timestamp sang string để JSON serializable
                if "timestamp" in data and hasattr(data["timestamp"], "isoformat"):
                    data["timestamp"] = data["timestamp"].isoformat()
                results.append(data)
            return results
        except Exception as e:
            print(f">>> ItineraryManager Error (get_itinerary): {e}")
            return []

    async def add_to_itinerary(self, user_id: str, meal_data: Dict[str, Any]) -> bool:
        """
        Thêm một quán ăn vào lộ trình cho một bữa cụ thể.
        Nếu bữa đó đã có quán, nó sẽ bị ghi đè (hoặc cập nhật).
        """
        return await asyncio.to_thread(self._add_to_itinerary_sync, user_id, meal_data)

    def _add_to_itinerary_sync(self, user_id: str, meal_data: Dict[str, Any]) -> bool:
        try:
            meal = meal_data.get("meal")
            if not meal:
                return False
            
            col = self._get_collection(user_id)
            # Dùng meal làm document ID để dễ quản lý (mỗi bữa 1 quán)
            doc_ref = col.document(meal)
            
            meal_data["timestamp"] = datetime.now()
            doc_ref.set(meal_data)
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (add_to_itinerary): {e}")
            return False

    async def remove_from_itinerary(self, user_id: str, meal: str) -> bool:
        """
        Xóa một bữa khỏi lộ trình.
        """
        return await asyncio.to_thread(self._remove_from_itinerary_sync, user_id, meal)

    def _remove_from_itinerary_sync(self, user_id: str, meal: str) -> bool:
        try:
            col = self._get_collection(user_id)
            col.document(meal).delete()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (remove_from_itinerary): {e}")
            return False

    async def clear_itinerary(self, user_id: str) -> bool:
        """
        Xóa toàn bộ lộ trình hiện tại.
        """
        return await asyncio.to_thread(self._clear_itinerary_sync, user_id)

    def _clear_itinerary_sync(self, user_id: str) -> bool:
        try:
            col = self._get_collection(user_id)
            docs = col.list_documents()
            for doc in docs:
                doc.delete()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (clear_itinerary): {e}")
            return False
