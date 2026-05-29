import chromadb
import json
import hashlib
import os
import re #xử lý chuỗi Regex
from chromadb.utils import embedding_functions

class SemanticCacheManager:
    def __init__(self):
        cache_path = os.path.join(os.getcwd(), "Back_End", "Database", "chroma_cache_db")
        self.client = chromadb.PersistentClient(path=cache_path)
        
        # Đổi model sang all-mpnet-base-v2 (chính xác cao hơn)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2" 
        )
        
        # Đổi tên collection thành 'route_cache_v2' để tránh xung đột với data cũ
        self.collection = self.client.get_or_create_collection(
            name="route_cache_v2",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.ef
        )

    # Hàm chuẩn hoá prompt để Hash ID đúng
    def _normalize_prompt(self, prompt: str) -> str:
        prompt = prompt.lower() # 1. Đưa về chữ thường
        prompt = re.sub(r'[^\w\s]', '', prompt) # 2. Xóa sạch dấu câu
        prompt = " ".join(prompt.split()) # 3. Gom các khoảng trắng thừa thành 1
        return prompt
    
    def _get_location_zone(self, lat: float, lng: float) -> str:
        zone_lat = round(lat, 2)
        zone_lng = round(lng, 2)
        return f"zone_{zone_lat}_{zone_lng}"

    
    def check_cache(self, prompt: str, lat: float, lng: float, budget: int, health_key: str):
        normalized_prompt = self._normalize_prompt(prompt) 
        zone = self._get_location_zone(lat, lng)
        
        # Băm ID từ chuỗi ĐÃ chuẩn hóa
        doc_id = hashlib.md5(f"{normalized_prompt}_{zone}_{budget}_{health_key}".encode()).hexdigest()
        
        print(f"DEBUG: Checking ID: {doc_id}")

        existing_doc = self.collection.get(ids=[doc_id])

        if existing_doc and existing_doc['documents']:
            print("✅ [CACHE DEBUG] ID TRÙNG KHỚP! BẮN CACHE NGAY TỨC THÌ!")
            return json.loads(existing_doc['documents'][0])
        
        print("❌ [CACHE DEBUG] KHÔNG TÌM THẤY CACHE CHO ID NÀY!")
        return None

    def save_cache(self, prompt: str, lat: float, lng: float, budget: int, health_key: str, result_json: dict):
        normalized_prompt = self._normalize_prompt(prompt)
        budget = budget if budget is not None else 0
        zone = self._get_location_zone(lat, lng)
        
        # Băm ID từ chuỗi ĐÃ chuẩn hóa
        doc_id = hashlib.md5(f"{normalized_prompt}_{zone}_{budget}_{health_key}".encode()).hexdigest()

        self.collection.upsert(
            documents=[json.dumps(result_json)],
            metadatas=[{"zone": zone, "budget": budget, "health_filters": health_key}],
            ids=[doc_id]
        )
        print("💾 [CACHE DEBUG] ĐÃ LƯU THÀNH CÔNG VÀO DATABASE!")
