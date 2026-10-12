from typing import Optional, List
from fastapi import APIRouter, Query
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.engines.coverage_engine import CoverageEngine
from backend.app.eval.run_eval import RAGEvaluationRunner

router = APIRouter(prefix="/eval", tags=["Evaluation & Benchmarking"])

retriever = HybridRetriever()
coverage_engine = CoverageEngine()
eval_runner = RAGEvaluationRunner(retriever, coverage_engine)

@router.get("/benchmark")
def run_rag_benchmark(policy_id: Optional[str] = Query(None)):
    """Runs automated evaluation on benchmark dataset and computes Recall@5, MRR, Citation Accuracy, and Latency."""
    p_ids = [policy_id] if policy_id else None
    results = eval_runner.run_benchmark(policy_ids=p_ids)
    return results
