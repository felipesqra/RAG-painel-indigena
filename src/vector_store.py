import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any
import os
from .config import settings
from google import genai

class VectorStore:
    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(name="dengue_evidence")
        try:
            self.genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception:
            self.genai_client = None

    def get_embedding(self, text: str) -> List[float]:
        if not self.genai_client:
            return [0.0] * 768 # Dummy fallback
        try:
            response = self.genai_client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=text
            )
            return response.embeddings[0].values
        except Exception:
            return [0.0] * 768 # Dummy fallback

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
            
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for chunk in chunks:
            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])
            metadatas.append({
                "filename": chunk["filename"],
                "page": chunk["page"]
            })
            embeddings.append(self.get_embedding(chunk["text"]))

        # Batch add to avoid hitting limits
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.collection.count() == 0:
            return []
            
        query_embedding = self.get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        retrieved = []
        if results and results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                retrieved.append({
                    "document": results["metadatas"][0][i]["filename"],
                    "page": results["metadatas"][0][i]["page"],
                    "text": results["documents"][0][i],
                    "score": results["distances"][0][i] if results["distances"] else 0.0
                })
        return retrieved

vector_store = VectorStore()
