import chromadb
import json
import hashlib
import os

class SemanticCacheManager:
    def __init__(self):
        cache_path = os.path.join(os.getcwd(), "Back_End", "Database", "chroma_cache_db")
        self.client = chromadb.PersistentClient(path=cache_path)
        self.collection = self.client.get_or_create_collection(
            name="route_cache",
            metadata={"hnsw:space": "cosine"} 
        )

    def _get_location_zone(self, lat: float, lng: float) -> str:
        zone_lat = round(lat, 2)
        zone_lng = round(lng, 2)
        return f"zone_{zone_lat}_{zone_lng}"

    def check_cache(self, prompt: str, lat: float, lng: float, budget: int):
        if lat is None or lng is None:
            return None
        if budget is None:
            budget = 0
        zone = self._get_location_zone(lat, lng)

        results = self.collection.query(
            query_texts=[prompt],
            n_results=1,
            where={
                "$and": [
                    {"zone": {"$eq": zone}},
                    {"budget": {"$eq": budget}}
                ]
            }
        )

        if results['distances'] and len(results['distances'][0]) > 0:
            distance = results['distances'][0][0]
            if distance < 0.15: 
                cached_data = results['documents'][0][0]
                return json.loads(cached_data)

        return None

    def save_cache(self, prompt: str, lat: float, lng: float, budget: int, result_json: dict):
        zone = self._get_location_zone(lat, lng)
        doc_id = hashlib.md5(f"{prompt}_{zone}_{budget}".encode()).hexdigest()

        self.collection.upsert(
            documents=[json.dumps(result_json)],
            metadatas=[{"zone": zone, "budget": budget, "health_filters": "null"}],
            ids=[doc_id]
        )
