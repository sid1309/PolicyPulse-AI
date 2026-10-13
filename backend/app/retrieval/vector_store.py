import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny
)
from backend.app.core.config import settings
from backend.app.core.models import ClauseChunk

class VectorStoreManager:
    """
    Manages dense vector storage and retrieval using Qdrant with local persistence 
    and fast embedding generation.
    """

    COLLECTION_NAME = "insurance_policy_clauses"
    _shared_client = None
    _shared_embedder = None
    _shared_embed_type = None

    def __init__(self):
        # Initialize local persistent Qdrant client or reuse shared singleton
        if VectorStoreManager._shared_client is not None:
            self.client = VectorStoreManager._shared_client
        else:
            storage_path = str(settings.QDRANT_DIR)
            try:
                self.client = QdrantClient(path=storage_path)
                VectorStoreManager._shared_client = self.client
            except Exception as e:
                print(f"Notice: Qdrant client disk init notice: {e}")
                if VectorStoreManager._shared_client is not None:
                    self.client = VectorStoreManager._shared_client
                else:
                    self.client = QdrantClient(":memory:")
                    VectorStoreManager._shared_client = self.client
            
        self.embedding_dimension = 384  # Default for BAAI/bge-small-en-v1.5 / all-MiniLM-L6-v2
        self.embedder = VectorStoreManager._shared_embedder
        self.embed_type = VectorStoreManager._shared_embed_type
        self._ensure_collection()

    def _ensure_embedder(self):
        """Lazy initialization of embedder to guarantee sub-second server startup."""
        if self.embedder is None:
            self._init_embedder()

    def _init_embedder(self):
        """Initializes embedder with fastembed for speed and zero GPU requirement, with fallback."""
        if VectorStoreManager._shared_embedder is not None:
            self.embedder = VectorStoreManager._shared_embedder
            self.embed_type = VectorStoreManager._shared_embed_type
            self.embedding_dimension = 384
            return

        try:
            from fastembed import TextEmbedding
            # Restrict ONNX to 1 thread to cap memory under 150MB on Render Free tier
            self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=1)
            self.embedding_dimension = 384
            self.embed_type = "fastembed"
        except Exception:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                self.embedding_dimension = 384
                self.embed_type = "sentence_transformers"
            except Exception:
                self.embedder = None
                self.embed_type = "dummy"

        VectorStoreManager._shared_embedder = self.embedder
        VectorStoreManager._shared_embed_type = self.embed_type

    def _get_embedding(self, text: str) -> List[float]:
        """Generates dense vector for a single text."""
        self._ensure_embedder()
        if self.embed_type == "fastembed":
            vectors = list(self.embedder.embed([text]))
            return vectors[0].tolist()
        elif self.embed_type == "sentence_transformers":
            vec = self.embedder.encode(text)
            return vec.tolist()
        else:
            # Fallback pseudo-vector for testing if dependencies not yet installed
            import hashlib
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            import random
            rng = random.Random(seed)
            return [rng.uniform(-1, 1) for _ in range(self.embedding_dimension)]

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation."""
        self._ensure_embedder()
        if self.embed_type == "fastembed":
            vectors = list(self.embedder.embed(texts))
            return [v.tolist() for v in vectors]
        elif self.embed_type == "sentence_transformers":
            vecs = self.embedder.encode(texts)
            return [v.tolist() for v in vecs]
        else:
            return [self._get_embedding(t) for t in texts]

    def _ensure_collection(self):
        """Creates the Qdrant collection if not already existing."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=self.embedding_dimension, distance=Distance.COSINE)
            )

    def upsert_chunks(self, chunks: List[ClauseChunk]) -> int:
        """Stores clause chunks into Qdrant collection with micro-batching for low RAM footprint."""
        if not chunks:
            return 0
            
        import gc
        # Micro-batching in blocks of 16 chunks to keep memory usage under 200MB on Render Free tier
        batch_size = 16
        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i:i + batch_size]
            texts = [c.content_text for c in chunk_batch]
            vectors = self._get_embeddings_batch(texts)
            
            points = []
            for idx, chunk in enumerate(chunk_batch):
                point_id = chunk.chunk_id
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "policy_id": chunk.policy_id,
                    "insurer": chunk.insurer,
                    "plan_name": chunk.plan_name,
                    "version": chunk.version,
                    "section_name": chunk.section_name,
                    "clause_id": chunk.clause_id,
                    "clause_title": chunk.clause_title,
                    "page_number": chunk.page_number,
                    "page_range": chunk.page_range,
                    "chunk_type": chunk.chunk_type,
                    "content_text": chunk.content_text,
                    "bbox": chunk.bbox,
                    "entities": chunk.entities
                }
                points.append(PointStruct(id=point_id, vector=vectors[idx], payload=payload))
                
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points
            )
            del points, vectors, texts
            gc.collect()
            
        return len(chunks)

    def search(
        self,
        query: str,
        policy_ids: Optional[List[str]] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Dense vector search with policy filtering."""
        query_vector = self._get_embedding(query)
        
        query_filter = None
        if policy_ids and len(policy_ids) > 0:
            if len(policy_ids) == 1:
                query_filter = Filter(
                    must=[FieldCondition(key="policy_id", match=MatchValue(value=policy_ids[0]))]
                )
            else:
                query_filter = Filter(
                    must=[FieldCondition(key="policy_id", match=MatchAny(any=policy_ids))]
                )
                
        response = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit
        )
        results = response.points
        
        candidates = []
        for r in results:
            candidates.append({
                "chunk_id": r.payload.get("chunk_id"),
                "policy_id": r.payload.get("policy_id"),
                "insurer": r.payload.get("insurer"),
                "plan_name": r.payload.get("plan_name"),
                "section_name": r.payload.get("section_name"),
                "clause_id": r.payload.get("clause_id"),
                "clause_title": r.payload.get("clause_title"),
                "page_number": r.payload.get("page_number"),
                "chunk_type": r.payload.get("chunk_type"),
                "content_text": r.payload.get("content_text"),
                "bbox": r.payload.get("bbox"),
                "entities": r.payload.get("entities", {}),
                "score": r.score
            })
            
        return candidates

    def delete_policy(self, policy_id: str):
        """Deletes all chunks belonging to a policy."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="policy_id", match=MatchValue(value=policy_id))]
            )
        )
