from Back_End.CONFIG import DB_PATH
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os
import math

class ChromaDBManager: 
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")
        self.collection = self.client.get_or_create_collection(
            name="restaurants_collection_vn",
            embedding_function=self.ef
        )
    
    def search(self, query_text, n_results=5):
        return self.collection.query(
            query_texts=[query_text], 
            n_results=n_results
        )

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
            result = self.collection.get(ids=ids, include=["embeddings"])
        except Exception:
            return {rid: 0.0 for rid in ids}

        embeddings = result.get("embeddings") or []
        if not embeddings:
            return {rid: 0.0 for rid in ids}

        query_embedding = self.ef([query_text])[0]
        scores = {}
        result_ids = result.get("ids") or ids
        for rid, emb in zip(result_ids, embeddings):
            similarity = self._cosine_similarity(query_embedding, emb)
            scores[rid] = (similarity + 1.0) / 2.0
        return scores
    
    def add(self): 
        data_path = os.path.join(DB_PATH, "data.json")
        df = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
        ids = df['id'].tolist()
        documents = df['semantic_text'].tolist()

        self.collection.add(
            documents=documents,
            ids=ids
        )

if __name__ == "__main__": 
    db_mng = ChromaDBManager() 
    db_mng.add()
    res = db_mng.search("Quán ăn lãng mạn")
    print(res)
