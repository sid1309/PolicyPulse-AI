from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.app.core.models import ComparisonResponse, PolicyDiffResponse
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.engines.comparison_engine import MultiPolicyComparisonEngine
from backend.app.engines.diff_engine import PolicyDiffEngine

router = APIRouter(prefix="/compare", tags=["Comparison & Diffing"])

retriever = HybridRetriever()
comparison_engine = MultiPolicyComparisonEngine(retriever)
diff_engine = PolicyDiffEngine(retriever)

class CompareRequest(BaseModel):
    policy_ids: List[str]
    force_refresh: bool = False

class DiffRequest(BaseModel):
    old_policy_id: str
    new_policy_id: str

@router.post("", response_model=ComparisonResponse)
def compare_policies(req: CompareRequest):
    """Generates side-by-side comparison matrix across canonical criteria with citations."""
    if len(req.policy_ids) < 2:
        raise HTTPException(status_code=400, detail="Please select at least 2 policies for comparison.")
    try:
        return comparison_engine.compare_policies(req.policy_ids, force_refresh=req.force_refresh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/diff", response_model=PolicyDiffResponse)
def diff_policy_versions(req: DiffRequest):
    """Detects differences, coverage expansions, and added restrictions between policy versions."""
    if not req.old_policy_id or not req.new_policy_id:
        raise HTTPException(status_code=400, detail="Both old_policy_id and new_policy_id are required.")
    try:
        return diff_engine.diff_policies(req.old_policy_id, req.new_policy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
