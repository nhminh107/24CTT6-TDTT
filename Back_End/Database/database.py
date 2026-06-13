from Back_End.CONFIG import DB_PATH
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os
import math

class ChromaDBManager: 
    _client = None
    _ef = None
    _collection = None
    _menu_collection = None

    def __init__(self):
        if ChromaDBManager._client is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_main_path = os.path.join(base_dir, "chroma_main_db")
            
            # Khởi tạo client
            ChromaDBManager._client = chromadb.PersistentClient(path=chroma_main_path)

        if ChromaDBManager._ef is None:
            ChromaDBManager._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )

        # Thử lấy hoặc tạo collection, reset nếu lỗi
        base_dir = os.path.dirname(os.path.abspath(__file__))
        chroma_main_path = os.path.join(base_dir, "chroma_main_db")
        
        try:
            if ChromaDBManager._collection is None:
                ChromaDBManager._collection = ChromaDBManager._client.get_or_create_collection(
                    name="restaurants_collection_vn",
                    embedding_function=ChromaDBManager._ef
                )
                ChromaDBManager._collection.count() # Kiểm tra corruption
            
            if ChromaDBManager._menu_collection is None:
                ChromaDBManager._menu_collection = ChromaDBManager._client.get_or_create_collection(
                    name="menu_collection_vn",
                    embedding_function=ChromaDBManager._ef
                )
                ChromaDBManager._menu_collection.count() # Kiểm tra corruption
        except Exception as e:
            print(f"⚠️ ChromaDB corrupted: {e}. Resetting...")
            ChromaDBManager._client = None
            ChromaDBManager._collection = None
            ChromaDBManager._menu_collection = None
            import shutil
            import time
            if os.path.exists(chroma_main_path):
                try:
                    shutil.rmtree(chroma_main_path)
                    time.sleep(2)
                except: pass
            
            os.makedirs(chroma_main_path, exist_ok=True)
            ChromaDBManager._client = chromadb.PersistentClient(path=chroma_main_path)
            ChromaDBManager._collection = ChromaDBManager._client.get_or_create_collection(
                name="restaurants_collection_vn",
                embedding_function=ChromaDBManager._ef
            )
            ChromaDBManager._menu_collection = ChromaDBManager._client.get_or_create_collection(
                name="menu_collection_vn",
                embedding_function=ChromaDBManager._ef
            )

        self.client = ChromaDBManager._client
        self.ef = ChromaDBManager._ef
        self.collection = ChromaDBManager._collection
        self.menu_collection = ChromaDBManager._menu_collection
    
    def search(self, query_text, n_results=5):
        try:
            return self.collection.query(
                query_texts=[query_text], 
                n_results=n_results
            )
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"ids": [], "distances": [], "documents": []}

    def search_menu(self, query_text, n_results=5, where=None):
        try:
            query_kwargs = {
                "query_texts": [query_text],
                "n_results": n_results
            }
            if where is not None:
                query_kwargs["where"] = where
            return self.menu_collection.query(**query_kwargs)
        except Exception as e:
            print(f"❌ Search menu error: {e}")
            return {"ids": [], "distances": [], "documents": []}

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0
        for val_a, val_b in zip(vec_a, vec_b):
            dot += val_a * val_b
            norm_a += val_a * val_a
            norm_b += val_b * val_b
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def semantic_similarity(self, query_text, ids):
        if not query_text or not ids:
            return {rid: 0.0 for rid in ids}

        try:
            count = self.collection.count()
        except Exception:
            count = 0
        if count == 0:
            raise RuntimeError("ChromaDB collection is empty. Run database.py add() to build embeddings.")

        try:
            result = self.collection.get(ids=ids, include=["embeddings"])
        except Exception:
            return {rid: 0.0 for rid in ids}

        embeddings = result.get("embeddings")
        if embeddings is None:
            return {rid: 0.0 for rid in ids}

        # embeddings có thể là list hoặc numpy array
        if getattr(embeddings, "size", None) == 0:
            return {rid: 0.0 for rid in ids}
        if hasattr(embeddings, "__len__") and len(embeddings) == 0:
            return {rid: 0.0 for rid in ids}

        query_embedding = self.ef([query_text])[0]
        scores = {}
        result_ids = result.get("ids") or ids
        for rid, emb in zip(result_ids, embeddings):
            similarity = self._cosine_similarity(query_embedding, emb)
            scores[rid] = (similarity + 1.0) / 2.0
        return scores
    
    def add(self, force=False): 
        data_path = os.path.join(DB_PATH, "data.json")
        if not os.path.exists(data_path):
            print(f"❌ Error: {data_path} not found.")
            return

        df = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
        ids = df['id'].tolist()
        documents = df['semantic_text'].tolist()

        try:
            restaurant_count = self.collection.count()
        except Exception:
            restaurant_count = 0
        
        if restaurant_count == 0 or force:
            print(f"Adding {len(ids)} restaurants to collection...")
            try:
                self.collection.upsert( # Dùng upsert để tránh trùng và cho phép cập nhật
                    documents=documents,
                    ids=ids
                )
            except Exception as e:
                print(f"⚠️ Warning: Failed to add restaurants due to ChromaDB error: {e}")
        else:
            print(f"Restaurant collection already has {restaurant_count} items. Skipping.")

        if "menu" not in df.columns:
            print("No 'menu' column found in data.json")
            return

        try:
            menu_count = self.menu_collection.count()
        except Exception:
            menu_count = 0
            
        if menu_count > 0 and not force:
            print(f"Menu collection already has {menu_count} items. Skipping.")
            return

        print(f"Processing menu items from {len(df)} restaurants...")
        menu_documents = []
        menu_ids = []
        menu_metadatas = []
        for _, row in df.iterrows():
            restaurant_id = str(row.get("id")).strip() # Clean ID
            restaurant_name = row.get("name")
            menu_items = row.get("menu")
            if not isinstance(menu_items, list):
                continue
            for idx, item in enumerate(menu_items):
                item_text = str(item).strip()
                if not item_text:
                    continue
                menu_ids.append(f"{restaurant_id}__menu__{idx}")
                menu_documents.append(item_text)
                menu_metadatas.append({
                    "restaurant_id": restaurant_id,
                    "restaurant_name": restaurant_name
                })

        if menu_documents:
            print(f"Adding {len(menu_documents)} menu items to menu_collection_vn...")
            # Chia nhỏ để add nếu dữ liệu quá lớn (ChromaDB có limit batch size)
            batch_size = 1000
            for i in range(0, len(menu_documents), batch_size):
                try:
                    self.menu_collection.upsert(
                        documents=menu_documents[i:i+batch_size],
                        ids=menu_ids[i:i+batch_size],
                        metadatas=menu_metadatas[i:i+batch_size]
                    )
                except Exception as e:
                    print(f"⚠️ Warning: Failed to add batch {i} due to ChromaDB error: {e}")
                    # Nếu lỗi là HNSW, có thể bỏ qua batch này để server vẫn chạy được
            print("✅ Menu addition process finished!")

if __name__ == "__main__": 
    db_mng = ChromaDBManager() 
    # Thêm tham số force=True nếu muốn nạp lại dữ liệu mới nhất
    db_mng.add(force=False) 
    print(f"Final Restaurant count: {db_mng.collection.count()}")
    print(f"Final Menu count: {db_mng.menu_collection.count()}")
    
    print("\nTesting search:")
    res = db_mng.search_menu("bún chả", n_results=3)
    print(f"Search 'bún chả' results: {res['ids']}")
