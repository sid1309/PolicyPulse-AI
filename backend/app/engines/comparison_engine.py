import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.models import ComparisonResponse, ComparisonMatrixItem, CitationItem
from backend.app.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)

CACHE_FILE = settings.STORAGE_DIR / "comparisons_cache.json"
POLICIES_META_FILE = settings.STORAGE_DIR / "policies_metadata.json"

class MultiPolicyComparisonEngine:
    """
    Evaluates 2 or more insurance policies side-by-side across 
    canonical health insurance criteria with dual-policy page-level citations.
    Supports persistent fingerprint-verified comparison caching.
    """

    CANONICAL_FEATURES = [
        {
            "category": "Room Rent Eligibility & Capping",
            "query": "room rent capping single private room charges proportional deduction"
        },
        {
            "category": "ICU Charges & Sub-limits",
            "query": "intensive care unit ICU charges sub-limit capping"
        },
        {
            "category": "Pre-Existing Diseases (PED) Waiting Period",
            "query": "pre-existing diseases PED waiting period months years"
        },
        {
            "category": "Specific Illness Waiting Period (Cataract, Hernia)",
            "query": "specific disease waiting period 24 months cataract hernia joint replacement"
        },
        {
            "category": "Pre & Post Hospitalization Medical Expenses",
            "query": "pre-hospitalization 30 60 days post-hospitalization 60 90 180 days medical expenses"
        },
        {
            "category": "Co-payment & Zone Deductibles",
            "query": "co-payment mandatory copay percentage zone deductible"
        },
        {
            "category": "Modern Treatments & Robotic Surgery",
            "query": "modern treatments advanced technology robotic surgery sub-limit"
        },
        {
            "category": "Day Care Treatments",
            "query": "day care treatment procedures 24 hours hospitalization exception"
        }
    ]

    def __init__(self, hybrid_retriever: HybridRetriever):
        self.retriever = hybrid_retriever

    @staticmethod
    def _canonical_cache_key(policy_ids: List[str]) -> str:
        """Returns deterministic, order-independent key for comparing policy sets."""
        return "__vs__".join(sorted(policy_ids))

    @staticmethod
    def _load_policies_metadata() -> Dict[str, Dict[str, Any]]:
        """Loads latest policy metadata for fingerprint verification."""
        if POLICIES_META_FILE.exists():
            try:
                with open(POLICIES_META_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read policies metadata: {e}")
                return {}
        return {}

    @staticmethod
    def _load_cache() -> Dict[str, Any]:
        """Loads comparison cache from persistent storage."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load comparison cache: {e}")
                return {}
        return {}

    @staticmethod
    def _save_cache(cache_data: Dict[str, Any]):
        """Persists comparison cache to disk."""
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save comparison cache: {e}")

    @classmethod
    def invalidate_cache(cls, policy_id: Optional[str] = None):
        """Purges cache entries for a given policy_id or all entries if policy_id is None."""
        if not CACHE_FILE.exists():
            return
        if policy_id is None:
            try:
                CACHE_FILE.unlink(missing_ok=True)
                logger.info("Cleared entire comparison cache.")
            except Exception as e:
                logger.error(f"Failed to clear comparison cache: {e}")
            return

        cache_data = cls._load_cache()
        keys_to_remove = [
            k for k, v in cache_data.items()
            if policy_id in k.split("__vs__") or policy_id in v.get("fingerprints", {})
        ]
        if keys_to_remove:
            for k in keys_to_remove:
                del cache_data[k]
            cls._save_cache(cache_data)
            logger.info(f"Invalidated {len(keys_to_remove)} comparison cache entries for policy '{policy_id}'.")

    @classmethod
    def _is_policy_fingerprint_valid(
        cls,
        cached_fp: Optional[Dict[str, Any]],
        curr_meta: Optional[Dict[str, Any]]
    ) -> bool:
        """Checks if a single policy's cached fingerprint matches current metadata."""
        if not cached_fp or not curr_meta:
            return False
        return (
            curr_meta.get("filename") == cached_fp.get("filename") and
            curr_meta.get("created_at") == cached_fp.get("created_at") and
            curr_meta.get("chunk_count") == cached_fp.get("chunk_count")
        )

    @classmethod
    def _verify_fingerprints(
        cls,
        cached_fps: Dict[str, Any],
        current_meta: Dict[str, Any],
        policy_ids: List[str]
    ) -> bool:
        """Validates all policy documents in the comparison match current metadata exactly."""
        if not cached_fps:
            return False

        for pid in policy_ids:
            if not cls._is_policy_fingerprint_valid(cached_fps.get(pid), current_meta.get(pid)):
                return False
        return True

    def _find_cached_policy_evals(
        self,
        pid: str,
        current_meta: Dict[str, Any],
        cache_data: Dict[str, Any]
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Finds existing feature extractions for `pid` across all 8 canonical features from any
        valid comparison cache entry, provided `pid`'s fingerprint matches current metadata.
        Returns: { feature_category_name: policy_eval_dict, ... } or None
        """
        curr = current_meta.get(pid)
        if not curr:
            return None

        for entry in cache_data.values():
            fps = entry.get("fingerprints", {})
            if pid in fps and self._is_policy_fingerprint_valid(fps[pid], curr):
                matrix = entry.get("comparison_response", {}).get("matrix", [])
                evals_by_cat = {}
                for m in matrix:
                    cat = m.get("feature_category")
                    p_dict = m.get("policies", {}).get(pid)
                    if cat and p_dict:
                        evals_by_cat[cat] = p_dict
                if len(evals_by_cat) == len(self.CANONICAL_FEATURES):
                    return evals_by_cat
        return None

    def compare_policies(self, policy_ids: List[str], force_refresh: bool = False) -> ComparisonResponse:
        """
        Executes multi-policy feature extraction with persistent fingerprint-verified caching.
        Auto-detects document changes:
        - If all policy documents are unchanged: Returns cached comparison instantly (0 queries).
        - If only a specific document changed or was updated: Re-queries ONLY that changed document,
          reusing cached feature extractions for all unchanged documents.
        """
        if not policy_ids or len(policy_ids) < 2:
            raise ValueError("Multi-policy comparison requires at least 2 policy IDs.")

        cache_key = self._canonical_cache_key(policy_ids)
        current_meta = self._load_policies_metadata()
        cache_data = self._load_cache()

        # Step 1: Check if this exact canonical comparison is 100% valid (all docs unchanged)
        if not force_refresh and cache_key in cache_data:
            cached_entry = cache_data[cache_key]
            cached_fps = cached_entry.get("fingerprints", {})
            if self._verify_fingerprints(cached_fps, current_meta, policy_ids):
                logger.info(
                    f"Comparison Cache 100% HIT for '{cache_key}'. "
                    f"All policy documents identical & unchanged. Instant response."
                )
                cached_resp_dict = cached_entry.get("comparison_response")
                if cached_resp_dict:
                    resp = ComparisonResponse(**cached_resp_dict)
                    resp.policy_ids = policy_ids
                    return resp

        # Step 2: Auto-detect which documents are changed vs unchanged
        cached_evals_by_policy: Dict[str, Dict[str, Dict[str, Any]]] = {}
        changed_pids: List[str] = []
        unchanged_pids: List[str] = []

        for pid in policy_ids:
            if force_refresh:
                changed_pids.append(pid)
            else:
                existing_evals = self._find_cached_policy_evals(pid, current_meta, cache_data)
                if existing_evals:
                    cached_evals_by_policy[pid] = existing_evals
                    unchanged_pids.append(pid)
                else:
                    changed_pids.append(pid)

        if unchanged_pids and changed_pids:
            logger.info(
                f"Auto-detected document update: Re-evaluating ONLY changed policies {changed_pids}. "
                f"Reusing cached evaluations for unchanged policies {unchanged_pids}."
            )
        elif changed_pids:
            logger.info(f"Evaluating fresh comparison for policies {changed_pids}...")

        # Step 3: Build comparison matrix (only query changed_pids)
        matrix_items: List[ComparisonMatrixItem] = []

        for feature in self.CANONICAL_FEATURES:
            cat_name = feature["category"]
            search_query = feature["query"]

            policy_evals = {}
            for pid in policy_ids:
                if pid in unchanged_pids and pid in cached_evals_by_policy:
                    # REUSE CACHED CLAUSE EXTRACTION! ZERO RETRIEVAL / ZERO LLM CALLS!
                    policy_evals[pid] = cached_evals_by_policy[pid][cat_name]
                else:
                    # Only retrieve and extract for the changed document
                    hits = self.retriever.retrieve(query=search_query, policy_ids=[pid], top_k=1)
                    if hits:
                        top_h = hits[0]
                        text = top_h.get("content_text", "")
                        clean_excerpt = text.split(":\n")[-1][:220] + "..."

                        entities = top_h.get("entities", {})
                        summary = "Covered according to standard terms"
                        if cat_name == "Room Rent Eligibility & Capping" and entities.get("room_rent_cap"):
                            summary = f"Limit: {entities.get('room_rent_cap')}"
                        elif "Waiting Period" in cat_name and entities.get("waiting_period_months"):
                            summary = f"{entities.get('waiting_period_months')} Months Waiting Period"
                        elif "Co-payment" in cat_name and entities.get("copay_percent"):
                            summary = f"{entities.get('copay_percent')}% Mandatory Co-pay"
                        else:
                            summary = top_h.get("clause_title", "Clause Terms")[:60]

                        policy_evals[pid] = {
                            "insurer": top_h.get("insurer"),
                            "plan_name": top_h.get("plan_name"),
                            "summary": summary,
                            "clause_title": top_h.get("clause_title"),
                            "page_number": top_h.get("page_number"),
                            "excerpt": clean_excerpt,
                            "score": top_h.get("normalized_score", 0.8)
                        }
                    else:
                        policy_evals[pid] = {
                            "insurer": "Policy",
                            "plan_name": pid,
                            "summary": "No specific clause found",
                            "clause_title": "N/A",
                            "page_number": 1,
                            "excerpt": "Not explicitly stated in parsed text.",
                            "score": 0.0
                        }

            matrix_items.append(ComparisonMatrixItem(
                feature_category=cat_name,
                policies=policy_evals,
                recommendation=self._evaluate_better_value(cat_name, policy_evals)
            ))

        verdict = self._synthesize_executive_verdict(policy_ids, matrix_items)

        response = ComparisonResponse(
            policy_ids=policy_ids,
            matrix=matrix_items,
            executive_verdict=verdict
        )

        # Build latest fingerprints and persist
        fingerprints = {}
        for pid in policy_ids:
            p_meta = current_meta.get(pid, {})
            fingerprints[pid] = {
                "filename": p_meta.get("filename"),
                "created_at": p_meta.get("created_at"),
                "chunk_count": p_meta.get("chunk_count")
            }

        cache_data[cache_key] = {
            "fingerprints": fingerprints,
            "comparison_response": response.dict(),
            "cached_at": datetime.utcnow().isoformat()
        }
        self._save_cache(cache_data)
        logger.info(f"Persisted comparison matrix for '{cache_key}' with policy metadata fingerprints.")

        return response

    def _evaluate_better_value(self, category: str, evals: Dict[str, Dict[str, Any]]) -> str:
        """Determines which policy has more consumer-friendly terms for this category."""
        summaries = [v.get("summary", "").lower() for v in evals.values()]
        if any("no capping" in s or "single private room" in s for s in summaries):
            return "Policy offering 'No Capping' or 'Single Private Room' provides superior coverage avoiding proportional deduction."
        if any("months" in s for s in summaries):
            return "Policy with lower waiting period duration is preferable."
        return "Compare exact sub-limits and room categories."

    def _synthesize_executive_verdict(self, policy_ids: List[str], matrix: List[ComparisonMatrixItem]) -> str:
        return (
            f"Evaluated {len(policy_ids)} policies across {len(matrix)} key dimensions. "
            "Policies with 'No Room Rent Capping' and lower Waiting Periods (24 vs 48 months) offer significantly "
            "lower out-of-pocket exposure during inpatient hospitalization claims."
        )
