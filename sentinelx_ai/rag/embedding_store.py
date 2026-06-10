import faiss
import numpy as np
import os
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("SentinelX.RAG")

class EmbeddingStore:
    def __init__(self, model_name='all-MiniLM-L6-v2', index_path="rag/faiss_index.bin"):
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path
        self.dimension = 384 # Dimension for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        
        if os.path.exists(self.index_path):
            self.load_index()

    def add_documents(self, docs):
        if not docs:
            return
        
        self.documents.extend(docs)
        embeddings = self.model.encode(docs)
        self.index.add(np.array(embeddings).astype('float32'))
        self.save_index()

    def query(self, text, k=3):
        if self.index.ntotal == 0:
            return []
        
        query_embedding = self.model.encode([text])
        distances, indices = self.index.search(np.array(query_embedding).astype('float32'), k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.documents):
                results.append(self.documents[idx])
        return results

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".docs", "w", encoding="utf-8") as f:
            for doc in self.documents:
                f.write(doc.replace("\n", " ") + "\n")

    def load_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            doc_path = self.index_path + ".docs"
            if os.path.exists(doc_path):
                with open(doc_path, "r", encoding="utf-8") as f:
                    self.documents = [line.strip() for line in f.readlines()]
