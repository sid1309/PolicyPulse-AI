from fastapi import APIRouter, HTTPException
from backend.app.core.models import ClaimsAssessmentRequest, ClaimsAssessmentResult
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.engines.claims_math_engine import ClaimsMathEngine

router = APIRouter(prefix="/claims", tags=["Claims Assessment"])

retriever = HybridRetriever()
claims_engine = ClaimsMathEngine(retriever)

@router.post("/assess", response_model=ClaimsAssessmentResult)
def assess_claim(req: ClaimsAssessmentRequest):
    """Calculates claim eligibility, proportional room rent penalties, and document checklist."""
    if not req.policy_id:
        raise HTTPException(status_code=400, detail="Policy ID is required.")
    try:
        return claims_engine.assess_claim(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
