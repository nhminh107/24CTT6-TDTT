import random
import string
import asyncio
from Back_End.Core.auth_handler import get_db

class ShareManager:
    def __init__(self):
        pass

    def _get_db(self):
        return get_db()

    def generate_share_id(self, length=6):
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    async def create_share_link(self, user_id: str, itinerary_data: list) -> str:
        return await asyncio.to_thread(self._create_share_link_sync, user_id, itinerary_data)
        
    def _create_share_link_sync(self, user_id: str, itinerary_data: list) -> str:
        db = self._get_db()
        col = db.collection("shared_itineraries")
        
        while True:
            share_id = self.generate_share_id()
            doc_ref = col.document(share_id)
            if not doc_ref.get().exists:
                doc_ref.set({
                    "user_id": user_id,
                    "itinerary": itinerary_data
                })
                return share_id

    async def get_shared_itinerary(self, share_id: str) -> dict:
        return await asyncio.to_thread(self._get_shared_itinerary_sync, share_id)
        
    def _get_shared_itinerary_sync(self, share_id: str) -> dict:
        db = self._get_db()
        doc_ref = db.collection("shared_itineraries").document(share_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
