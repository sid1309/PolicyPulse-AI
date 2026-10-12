import os
from typing import List, Dict, Any
from backend.app.core.config import settings

class CrossEncoderReranker:
    """
    Reranks candidate clauses using deep token-level cross-attention.
    Eliminates semantic false positives and scores legal clause relevance.
    """

    def __init__(self):
        self.model = None
        self._init_model()

    def _init_model(self):
        """Attempts to load fast cross-encoder, with graceful fallback."""
        try:
            from sentence_transformers import CrossEncoder
            # Use light cross-encoder for instant low-latency inference
            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            self.model = CrossEncoder(model_name)
        except Exception as e:
            # Fallback to local heuristic ranker if weights are not downloaded
            self.model = None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Reranks candidate chunks for high legal relevance."""
        if not candidates:
            return []
            
        q_lower = query.lower()
        coverage_query = any(w in q_lower for w in [
            "room rent", "covered", "coverage", "surgery", "treatment", 
            "limit", "waiting period", "claim", "icu", "hospital", "maternity", "cataract", "ayush",
            "copay", "co-pay", "deductible", "nursing", "cashless", "organ donor", "ambulance"
        ])
        non_medical_signals = [
            "ombudsman", "grievance", "bimalokpal", "shoe cover", "comb", 
            "gown", "slipper", "tooth paste", "face mask", "hand wash",
            "room freshner", "bed pan", "cradle", "tissue paper",
            "non-payable", "schedule iii", "guwahati", "bhubaneswar", "chandigarh",
            "ahmedabad", "bengaluru", "bhopal", "kolkata", "lucknow"
        ]

        from backend.app.retrieval.medical_ontology import InsuranceMedicalOntology
        med_match = InsuranceMedicalOntology.match_condition(q_lower)
        is_ped = med_match and med_match.get("type") == "PED"
        is_specified = med_match and med_match.get("type") == "SPECIFIED"

        if self.model is not None:
            pairs = [[query, c["content_text"]] for c in candidates]
            scores = self.model.predict(pairs)
            
            reranked = []
            for idx, raw_score in enumerate(scores):
                cand = candidates[idx].copy()
                score = float(raw_score)
                cand_text = (
                    f"{cand.get('clause_title', '')} "
                    f"{cand.get('section_name', '')} "
                    f"{cand.get('content_text', '')}"
                ).lower()

                # Penalize non-medical chunks on coverage queries
                if coverage_query and any(sig in cand_text for sig in non_medical_signals):
                    score -= 5.0

                # Strongly prioritize exact room rent clauses if asking about room rent
                if "room rent" in q_lower:
                    if any(term in cand_text for term in ["room rent", "room, board", "single private room", "room category"]):
                        score += 3.0

                # Strongly prioritize Pre-Existing Disease (Excl01) clauses if query is about a PED condition
                if is_ped:
                    if any(term in cand_text for term in ["pre-existing", "ped", "excl01"]):
                        score += 4.0
                    # Penalize cataract from matching diabetes queries
                    if "cataract" in cand.get("section_name", "").lower() or "cataract" in cand.get("clause_title", "").lower():
                        score -= 4.0

                # Strongly prioritize specified disease matching
                if is_specified and med_match:
                    if med_match.get("name", "").lower() in cand_text:
                        score += 3.0

                cand["rerank_score"] = float(score)
                # Normalize logit to roughly 0-1 range for UI
                import math
                cand["normalized_score"] = round(1 / (1 + math.exp(-max(min(score, 10.0), -10.0))), 3)
                reranked.append(cand)
                
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            return reranked[:top_k]
        else:
            # Intelligent fallback heuristic combining RRF, clean token overlap & domain boosting
            import re
            STOPWORDS = {
                "a", "an", "the", "is", "it", "in", "on", "of", "to", "for", "and", "or",
                "my", "your", "our", "this", "that", "be", "as", "at", "by", "from", "with",
                "what", "how", "does", "do", "can", "if", "any", "are", "which", "will",
                "there", "has", "have", "had", "should", "would", "me", "he", "she", "they"
            }
            GENERIC_SKIP = {"limit", "table", "general", "standard", "schedule", "provision", "section", "clause"}

            all_q_words = re.findall(r"\b[a-z0-9]+\b", q_lower)
            meaningful_tokens = [w for w in all_q_words if w not in STOPWORDS]
            if not meaningful_tokens:
                meaningful_tokens = all_q_words

            reranked = []
            for c in candidates:
                cand = c.copy()
                title_lower = cand.get('clause_title', '').lower()
                sec_lower = cand.get('section_name', '').lower()
                body_lower = cand.get('content_text', '').lower()
                text_corpus = f"{title_lower} {sec_lower} {body_lower}"
                
                # Check overlap of meaningful tokens
                matched = [t for t in meaningful_tokens if t in text_corpus]
                overlap_ratio = len(matched) / max(len(meaningful_tokens), 1)
                
                # Priority boost for high-salience terms (skip generic words like 'limit')
                boost = 0.0
                for token in meaningful_tokens:
                    if len(token) > 4 and token not in GENERIC_SKIP and token in text_corpus:
                        boost += 0.15
                
                # Boost if clause title or section name specifically matches domain query tokens
                domain_tokens = [t for t in meaningful_tokens if len(t) > 3 and t not in GENERIC_SKIP]
                if any(t in title_lower or t in sec_lower for t in domain_tokens):
                    boost += 0.25

                # Penalize non-medical chunks on coverage queries
                if coverage_query and any(sig in text_corpus for sig in non_medical_signals):
                    boost -= 0.60

                # Strongly prioritize exact room rent clauses if asking about room rent
                if "room rent" in q_lower:
                    if any(term in text_corpus for term in ["room rent", "room, board", "single private room", "room category"]):
                        boost += 0.35

                # Strongly prioritize Pre-Existing Disease (Excl01) clauses if query is about a PED condition
                if is_ped:
                    if any(term in text_corpus for term in ["pre-existing", "ped", "excl01"]):
                        boost += 0.50
                    if "cataract" in sec_lower or "cataract" in title_lower:
                        boost -= 0.60

                # Strongly prioritize specified disease matching
                if is_specified and med_match:
                    if med_match.get("name", "").lower() in text_corpus:
                        boost += 0.35

                base_score = cand.get("rrf_score", 0.5)
                final_score = (base_score * 0.35) + (overlap_ratio * 0.45) + boost
                
                cand["rerank_score"] = round(final_score, 4)
                cand["normalized_score"] = round(min(max(final_score, 0.05), 0.99), 3)
                reranked.append(cand)
                
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            return reranked[:top_k]
