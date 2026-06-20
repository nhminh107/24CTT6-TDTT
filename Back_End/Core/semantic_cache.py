import chromadb
import json
import hashlib
import os
import re #xử lý chuỗi Regex
from chromadb.utils import embedding_functions

class SemanticCacheManager:
    def __init__(self):
        # Sử dụng đường dẫn tuyệt đối để tránh xung đột
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_path = os.path.join(base_dir, "Database", "chroma_cache_db")
        if not os.path.exists(cache_path):
            os.makedirs(cache_path, exist_ok=True)
            
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

    
    def check_cache(self, prompt: str, lat: float, lng: float, budget: int, health_key: str, diet_mode: str):
        normalized_prompt = self._normalize_prompt(prompt) 
        zone = self._get_location_zone(lat, lng)
        
        # CẬP NHẬT: Nối thêm diet_mode vào cuối chuỗi trước khi encode và băm MD5
        doc_id = hashlib.md5(f"{normalized_prompt}_{zone}_{budget}_{health_key}_{diet_mode}".encode()).hexdigest()
        
        print(f"DEBUG: Checking ID: {doc_id}")

        existing_doc = self.collection.get(ids=[doc_id])

        if existing_doc and existing_doc['documents']:
            print("✅ [CACHE DEBUG] ID TRÙNG KHỚP! BẮN CACHE NGAY TỨC THÌ!")
            return json.loads(existing_doc['documents'][0])
        
        print("❌ [CACHE DEBUG] KHÔNG TÌM THẤY CACHE CHO ID NÀY!")
        return None

    def save_cache(self, prompt: str, lat: float, lng: float, budget: int, health_key: str, diet_mode: str, result_json: dict):
        normalized_prompt = self._normalize_prompt(prompt)
        budget = budget if budget is not None else 0
        zone = self._get_location_zone(lat, lng)
        
        # CẬP NHẬT: Nối thêm diet_mode vào cuối chuỗi trước khi encode và băm MD5
        doc_id = hashlib.md5(f"{normalized_prompt}_{zone}_{budget}_{health_key}_{diet_mode}".encode()).hexdigest()
        
        print(f"DEBUG: Saving ID: {doc_id}")
        
        self.collection.upsert(
            ids=[doc_id],
            documents=[json.dumps(result_json)],
            metadatas=[{"zone": zone, "budget": budget, "health_key": health_key, "diet_mode": diet_mode}]
        )
