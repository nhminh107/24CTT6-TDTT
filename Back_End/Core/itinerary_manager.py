from datetime import datetime
from typing import Optional, Dict, Any, List
import asyncio
from firebase_admin import firestore
from Back_End.Core.auth_handler import get_db

class ItineraryManager:
    def __init__(self):
        pass

    def _get_db(self):
        db = get_db()
        if db is None:
            raise Exception("Firestore client is not initialized.")
        return db

    def _get_itinerary_collection(self, user_id: str):
        return self._get_db().collection("users").document(user_id).collection("current_itinerary")

    async def get_itinerary(self, user_id: str) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_itinerary_sync, user_id)

    def _get_itinerary_sync(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            col = self._get_itinerary_collection(user_id)
            docs = col.stream()
            
            itinerary = []
            for doc in docs:
                data = doc.to_dict()
                if "timestamp" in data and isinstance(data["timestamp"], datetime):
                    data["timestamp"] = data["timestamp"].isoformat()
                itinerary.append(data)
            
            # Sắp xếp: Ưu tiên trường 'order', sau đó mới đến thứ tự bữa ăn mặc định
            meal_order = {"Sáng": 1, "Trưa": 2, "Xế": 3, "Tối": 4}
            itinerary.sort(key=lambda x: (x.get("order", 999), meal_order.get(x.get("meal", ""), 99)))
            
            return itinerary
        except Exception as e:
            print(f">>> ItineraryManager Error (get_itinerary): {e}")
            return []

    async def select_restaurant(self, user_id: str, meal: str, restaurant_data: Dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._select_restaurant_sync, user_id, meal, restaurant_data)

    def _select_restaurant_sync(self, user_id: str, meal: str, restaurant_data: Dict[str, Any]) -> bool:
        try:
            col = self._get_itinerary_collection(user_id)
            restaurant_data["meal"] = meal
            restaurant_data["timestamp"] = datetime.now()
            # Nếu chưa có order, gán theo mặc định
            if "order" not in restaurant_data:
                meal_order = {"Sáng": 1, "Trưa": 2, "Xế": 3, "Tối": 4}
                restaurant_data["order"] = meal_order.get(meal, 99)
            col.document(meal).set(restaurant_data)
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (select_restaurant): {e}")
            return False

    async def reorder_itinerary(self, user_id: str, ordered_meals: List[str]) -> bool:
        return await asyncio.to_thread(self._reorder_itinerary_sync, user_id, ordered_meals)

    def _reorder_itinerary_sync(self, user_id: str, ordered_meals: List[str]) -> bool:
        try:
            db = self._get_db()
            col = self._get_itinerary_collection(user_id)
            
            batch = db.batch()
            for index, meal in enumerate(ordered_meals):
                doc_ref = col.document(meal)
                batch.update(doc_ref, {"order": index})
            
            batch.commit()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (reorder_itinerary): {e}")
            return False
    async def delete_meal(self, user_id: str, meal: str) -> bool:
        return await asyncio.to_thread(self._delete_meal_sync, user_id, meal)

    def _delete_meal_sync(self, user_id: str, meal: str) -> bool:
        try:
            col = self._get_itinerary_collection(user_id)
            col.document(meal).delete()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (delete_meal): {e}")
            return False

    async def reset_itinerary(self, user_id: str) -> bool:
        return await asyncio.to_thread(self._reset_itinerary_sync, user_id)

    def _reset_itinerary_sync(self, user_id: str) -> bool:
        try:
            col = self._get_itinerary_collection(user_id)
            docs = col.stream()
            for doc in docs:
                doc.reference.delete()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (reset_itinerary): {e}")
            return False
