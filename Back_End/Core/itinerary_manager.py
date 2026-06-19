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
            
            # Chuẩn hóa nhãn bữa ăn một cách nghiêm ngặt
            meal_raw = str(meal).strip().lower()
            if "sáng" in meal_raw: meal = "Sáng"
            elif "trưa" in meal_raw: meal = "Trưa"
            elif "tối" in meal_raw: meal = "Tối"
            elif "xế" in meal_raw or "phụ" in meal_raw or "snack" in meal_raw: meal = "Xế"
            else: meal = meal.capitalize()
            
            restaurant_data["meal"] = meal
            restaurant_data["timestamp"] = datetime.now()
            
            is_auto = restaurant_data.get("is_auto", False)
            existing_order = None
            
            # 1. Tìm và xóa quán cũ, đồng thời lấy lại vị trí (order) của nó
            # Truy vấn cả bản viết hoa và viết thường để đảm bảo dọn dẹp sạch sẽ
            meal_variants = [meal, meal.lower(), meal.upper()]
            docs = col.where("meal", "in", meal_variants).stream()
            
            items_to_delete = []
            for doc in docs:
                data = doc.to_dict()
                # Đối với Xế, chỉ tự động thay thế nếu cả hai đều là bản do AI thêm (is_auto)
                if meal == "Xế" and is_auto:
                    if data.get("is_auto"):
                        if existing_order is None: existing_order = data.get("order")
                        items_to_delete.append(doc.reference)
                elif meal != "Xế":
                    # Sáng, Trưa, Tối luôn bị thay thế
                    if existing_order is None: existing_order = data.get("order")
                    items_to_delete.append(doc.reference)

            # Thực hiện xóa các quán cũ
            for ref in items_to_delete:
                ref.delete()
            
            # 2. Gán vị trí cho quán mới
            if existing_order is not None:
                restaurant_data["order"] = existing_order
            elif "order" not in restaurant_data:
                meal_order = {"Sáng": 0, "Trưa": 1, "Xế": 2, "Tối": 3}
                restaurant_data["order"] = meal_order.get(meal, 99)
                
            doc_id = str(restaurant_data.get("id"))
            col.document(doc_id).set(restaurant_data)
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (select_restaurant): {e}")
            return False

    async def reorder_itinerary(self, user_id: str, ordered_items: List[Dict[str, Any]]) -> bool:
        return await asyncio.to_thread(self._reorder_itinerary_sync, user_id, ordered_items)

    def _reorder_itinerary_sync(self, user_id: str, ordered_items: List[Dict[str, Any]]) -> bool:
        try:
            db = self._get_db()
            col = self._get_itinerary_collection(user_id)
            
            batch = db.batch()
            for index, item in enumerate(ordered_items):
                doc_ref = col.document(item["id"])
                batch.update(doc_ref, {"order": index})
            
            batch.commit()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (reorder_itinerary): {e}")
            return False

    async def delete_meal(self, user_id: str, item_id: str) -> bool:
        return await asyncio.to_thread(self._delete_meal_sync, user_id, item_id)

    def _delete_meal_sync(self, user_id: str, item_id: str) -> bool:
        try:
            col = self._get_itinerary_collection(user_id)
            col.document(item_id).delete()
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

    async def import_shared_itinerary(self, user_id: str, share_id: str) -> bool:
        return await asyncio.to_thread(self._import_shared_itinerary_sync, user_id, share_id)

    def _import_shared_itinerary_sync(self, user_id: str, share_id: str) -> bool:
        try:
            db = self._get_db()
            share_doc = db.collection("shared_itineraries").document(share_id).get()
            if not share_doc.exists:
                return False
            
            shared_data = share_doc.to_dict()
            itinerary_data = shared_data.get("itinerary", [])
            
            self._reset_itinerary_sync(user_id)
            
            col = self._get_itinerary_collection(user_id)
            batch = db.batch()
            
            for index, item in enumerate(itinerary_data):
                meal = item.get("meal", f"Meal_{index}")
                item["timestamp"] = datetime.now()
                if "order" not in item:
                    item["order"] = index
                
                doc_id = str(item.get("id"))
                doc_ref = col.document(doc_id)
                batch.set(doc_ref, item)
            
            batch.commit()
            return True
        except Exception as e:
            print(f">>> ItineraryManager Error (import_shared_itinerary): {e}")
            return False
