from typing import List, Dict, Any
from backend.app.core.models import PolicyDiffResponse, PolicyDiffItem
from backend.app.retrieval.hybrid_retriever import HybridRetriever

class PolicyDiffEngine:
    """
    Detects semantic differences, coverage expansions, and added restrictions 
    between old and new versions of an insurance policy.
    """

    DIFF_CATEGORIES = [
        {"category": "Room Rent & ICU Limits", "query": "room rent capping ICU limit single room"},
        {"category": "Pre-Existing Diseases Waiting Period", "query": "pre-existing diseases PED waiting period months"},
        {"category": "Specific Illness Waiting Period", "query": "specific disease waiting period cataract hernia"},
        {"category": "Co-payment & Deductibles", "query": "co-payment mandatory copay deductible percentage"},
        {"category": "Modern Treatments & Robotic Surgery", "query": "modern treatments advanced robotic surgery sublimit"},
        {"category": "Claim Notification Window", "query": "claim intimation notification within hours days"}
    ]

    def __init__(self, hybrid_retriever: HybridRetriever):
        self.retriever = hybrid_retriever

    def diff_policies(self, old_policy_id: str, new_policy_id: str) -> PolicyDiffResponse:
        """Compares two policy versions and highlights clause deltas."""
        changes: List[PolicyDiffItem] = []
        
        for item in self.DIFF_CATEGORIES:
            cat = item["category"]
            query = item["query"]
            
            old_hits = self.retriever.retrieve(query=query, policy_ids=[old_policy_id], top_k=1)
            new_hits = self.retriever.retrieve(query=query, policy_ids=[new_policy_id], top_k=1)
            
            if not old_hits and not new_hits:
                continue
                
            old_chunk = old_hits[0] if old_hits else {}
            new_chunk = new_hits[0] if new_hits else {}
            
            old_text = old_chunk.get("content_text", "Clause not present in old version.")
            new_text = new_chunk.get("content_text", "Clause not present in new version.")
            old_page = old_chunk.get("page_number", 1)
            new_page = new_chunk.get("page_number", 1)
            
            change_type, impact = self._classify_change(cat, old_chunk, new_chunk)
            
            changes.append(PolicyDiffItem(
                category=cat,
                change_type=change_type,
                old_clause_text=old_text.split(":\n")[-1][:260] + "...",
                new_clause_text=new_text.split(":\n")[-1][:260] + "...",
                old_page=old_page,
                new_page=new_page,
                impact_analysis=impact
            ))
            
        summary = (
            f"Comparison between Old Version ({old_policy_id}) and New Version ({new_policy_id}) "
            f"revealed {sum(1 for c in changes if c.change_type == 'EXPANSION')} benefit expansions, "
            f"{sum(1 for c in changes if c.change_type == 'RESTRICTION')} coverage restrictions, and "
            f"{sum(1 for c in changes if c.change_type == 'PROCEDURAL')} procedural updates."
        )
        
        return PolicyDiffResponse(
            old_policy_id=old_policy_id,
            new_policy_id=new_policy_id,
            summary_of_changes=summary,
            changes=changes
        )

    def _classify_change(self, category: str, old_c: Dict[str, Any], new_c: Dict[str, Any]) -> tuple[str, str]:
        """Classifies change as Expansion, Restriction, or Procedural."""
        old_ent = old_c.get("entities", {})
        new_ent = new_c.get("entities", {})
        
        # Check Waiting Periods
        old_wp = old_ent.get("waiting_period_months")
        new_wp = new_ent.get("waiting_period_months")
        if old_wp and new_wp:
            if new_wp < old_wp:
                return "EXPANSION", f"Waiting period reduced from {old_wp} months to {new_wp} months (Favorable)."
            elif new_wp > old_wp:
                return "RESTRICTION", f"Waiting period increased from {old_wp} months to {new_wp} months (Unfavorable)."
                
        # Check Co-pay
        old_cp = old_ent.get("copay_percent")
        new_cp = new_ent.get("copay_percent")
        if new_cp and (not old_cp or new_cp > old_cp):
            return "RESTRICTION", f"New/Higher co-payment of {new_cp}% introduced on claims."
            
        return "PROCEDURAL", "Wording updated; review exact clause phrasing for procedural requirements."
