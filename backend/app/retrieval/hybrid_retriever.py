from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.retrieval.vector_store import VectorStoreManager
from backend.app.retrieval.bm25_search import BM25SearchManager
from backend.app.retrieval.reranker import CrossEncoderReranker
from backend.app.retrieval.query_router import QueryRouter

class HybridRetriever:
    """
    Hybrid retriever combining Dense Vector + BM25 Sparse Search 
    using Reciprocal Rank Fusion (RRF) and Cross-Encoder Reranking,
    with multi-policy balanced retrieval guarantees.
    """

    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.bm25 = BM25SearchManager()
        self.reranker = CrossEncoderReranker()
        self.router = QueryRouter()

    def retrieve(
        self,
        query: str,
        policy_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval pipeline:
        Query Expansion -> Parallel Dense+Sparse -> Multi-Policy RRF -> Cross-Encoder Reranking
        """
        processed = self.router.process_query(query, policy_ids)
        expanded_query = processed["expanded_query"]
        
        # If multiple policies are provided, retrieve per policy to guarantee balance
        if policy_ids and len(policy_ids) > 1:
            all_candidates = []
            per_policy_limit = max(settings.TOP_CANDIDATES_K // len(policy_ids), 10)
            
            for pid in policy_ids:
                dense_hits = self.vector_store.search(expanded_query, policy_ids=[pid], limit=per_policy_limit)
                sparse_hits = self.bm25.search(expanded_query, policy_ids=[pid], limit=per_policy_limit)
                fused = self._reciprocal_rank_fusion(dense_hits, sparse_hits)
                all_candidates.extend(fused[:per_policy_limit])
                
            # Rerank combined balanced candidates
            final_top = self.reranker.rerank(expanded_query, all_candidates, top_k=top_k)
            return final_top
        else:
            # Single policy or global search
            dense_hits = self.vector_store.search(expanded_query, policy_ids=policy_ids, limit=settings.TOP_CANDIDATES_K)
            sparse_hits = self.bm25.search(expanded_query, policy_ids=policy_ids, limit=settings.TOP_CANDIDATES_K)
            fused = self._reciprocal_rank_fusion(dense_hits, sparse_hits)
            
            final_top = self.reranker.rerank(expanded_query, fused[:settings.TOP_CANDIDATES_K], top_k=top_k)

        # Resilient fallback: If filter yielded 0 candidates, search across all available policies
        if not final_top and policy_ids:
            dense_hits = self.vector_store.search(expanded_query, policy_ids=None, limit=settings.TOP_CANDIDATES_K)
            sparse_hits = self.bm25.search(expanded_query, policy_ids=None, limit=settings.TOP_CANDIDATES_K)
            fused = self._reciprocal_rank_fusion(dense_hits, sparse_hits)
            final_top = self.reranker.rerank(expanded_query, fused[:settings.TOP_CANDIDATES_K], top_k=top_k)

        return final_top

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Computes Reciprocal Rank Fusion (RRF) scores:
        RRF_Score(d) = w_dense / (k + rank_dense) + w_sparse / (k + rank_sparse)
        """
        w_dense = settings.DENSE_WEIGHT
        w_sparse = settings.SPARSE_WEIGHT
        
        chunk_map: Dict[str, Dict[str, Any]] = {}
        rrf_scores: Dict[str, float] = {}
        
        # Process dense ranks
        for rank, item in enumerate(dense_results):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (w_dense / (k + rank + 1))
            
        # Process sparse ranks
        for rank, item in enumerate(sparse_results):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (w_sparse / (k + rank + 1))
            
        fused = []
        for cid, score in rrf_scores.items():
            entry = chunk_map[cid].copy()
            entry["rrf_score"] = round(score, 5)
            fused.append(entry)
            
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused
