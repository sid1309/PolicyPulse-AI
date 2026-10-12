import os
import re
import pickle
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from backend.app.core.config import settings
from backend.app.core.models import ClauseChunk

class BM25SearchManager:
    """
    Sparse lexical search engine tailored for insurance policies, 
    preserving alphanumeric clause codes (Excl01, PED), numbers, and percentages.
    """

    _shared_instance = None

    def __new__(cls, *args, **kwargs):
        if cls._shared_instance is None:
            cls._shared_instance = super(BM25SearchManager, cls).__new__(cls)
            cls._shared_instance._initialized = False
        return cls._shared_instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.index_file = settings.BM25_DIR / "bm25_index.pkl"
        self.chunks_data: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._load_index()
        self._initialized = True

    def _tokenize(self, text: str) -> List[str]:
        """Custom tokenizer preserving insurance-critical tokens."""
        text = text.lower()
        # Keep alphanumeric tokens, percentages, and hyphenated terms (e.g. co-pay, pre-existing)
        tokens = re.findall(r"\b[a-z0-9]+(?:[\-\.][a-z0-9]+)*%?\b", text)
        return tokens

    def _load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "rb") as f:
                    data = pickle.load(f)
                    self.chunks_data = data.get("chunks_data", [])
                    self.tokenized_corpus = [self._tokenize(c["content_text"]) for c in self.chunks_data]
                    if self.tokenized_corpus:
                        self.bm25 = BM25Okapi(self.tokenized_corpus)
            except Exception as e:
                print(f"Notice: BM25 index load warning: {e}")

    def _save_index(self):
        try:
            with open(self.index_file, "wb") as f:
                pickle.dump({"chunks_data": self.chunks_data}, f)
        except Exception as e:
            print(f"Notice: BM25 index save warning: {e}")

    def add_chunks(self, chunks: List[ClauseChunk]):
        """Adds new chunks to the BM25 index."""
        if not chunks:
            return
            
        new_entries = []
        for c in chunks:
            entry = {
                "chunk_id": c.chunk_id,
                "policy_id": c.policy_id,
                "insurer": c.insurer,
                "plan_name": c.plan_name,
                "section_name": c.section_name,
                "clause_id": c.clause_id,
                "clause_title": c.clause_title,
                "page_number": c.page_number,
                "chunk_type": c.chunk_type,
                "content_text": c.content_text,
                "bbox": c.bbox,
                "entities": c.entities
            }
            new_entries.append(entry)
            
        self.chunks_data.extend(new_entries)
        self.tokenized_corpus = [self._tokenize(c["content_text"]) for c in self.chunks_data]
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        self._save_index()

    def search(
        self,
        query: str,
        policy_ids: Optional[List[str]] = None,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Executes BM25 sparse keyword search with policy filtering."""
        if not self.bm25 or not self.chunks_data:
            return []
            
        tokens = self._tokenize(query)
        if not tokens:
            return []
            
        scores = self.bm25.get_scores(tokens)
        
        # Filter and rank candidates
        scored_candidates = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue
            chunk = self.chunks_data[idx]
            
            # Policy filter
            if policy_ids and chunk["policy_id"] not in policy_ids:
                continue
                
            scored_candidates.append({
                **chunk,
                "score": float(score)
            })
            
        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:limit]

    def delete_policy(self, policy_id: str):
        """Removes all chunks for a policy and rebuilds index."""
        self.chunks_data = [c for c in self.chunks_data if c["policy_id"] != policy_id]
        if self.chunks_data:
            self.tokenized_corpus = [self._tokenize(c["content_text"]) for c in self.chunks_data]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.tokenized_corpus = []
            self.bm25 = None
        self._save_index()
