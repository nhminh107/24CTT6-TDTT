from Back_End.CONFIG import DB_PATH
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd 
import os 

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