from fastapi import APIRouter, HTTPException
from backend.app.core.models import (
    ChatQueryRequest, ChatResponse,
    ExplainClauseRequest, ExplainClauseResponse
)
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.engines.coverage_engine import CoverageEngine
from backend.app.graph.neo4j_client import GraphRAGClient

router = APIRouter(prefix="/chat", tags=["Chat"])

retriever = HybridRetriever()
coverage_engine = CoverageEngine()
graph_client = GraphRAGClient()

@router.post("", response_model=ChatResponse)
def query_assistant(req: ChatQueryRequest):
    """Executes query through Hybrid Retrieval + Reranker + Coverage Synthesis."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    # Hybrid retrieval with multi-policy support
    retrieved_chunks = retriever.retrieve(
        query=req.query,
        policy_ids=req.policy_ids if req.policy_ids else None,
        top_k=5
    )
    
    # Graph check if enabled
    if req.enable_graph and req.policy_ids:
        # Extract potential treatment name from query
        for pid in req.policy_ids:
            graph_facts = graph_client.query_treatment_rules(pid, req.query)
            if graph_facts:
                for gf in graph_facts:
                    # Append synthetic graph context clause
                    retrieved_chunks.append({
                        "policy_id": pid,
                        "insurer": "Knowledge Graph",
                        "plan_name": "Relational Rules",
                        "section_name": gf.get("section", "Graph Rule"),
                        "clause_id": gf.get("clause_id", "Graph_Node"),
                        "clause_title": f"Knowledge Graph Relationship (Page {gf.get('page')})",
                        "page_number": gf.get("page", 1),
                        "content_text": f"Knowledge Graph Link: Governing Clause {gf.get('clause_id')} specifies waiting period of {gf.get('waiting_months')} months.",
                        "normalized_score": 0.95
                    })
                    
    ans_resp = coverage_engine.generate_answer(
        query=req.query,
        retrieved_chunks=retrieved_chunks,
        history=req.history
    )
    
    return ans_resp

@router.post("/explain", response_model=ExplainClauseResponse)
def explain_clause(req: ExplainClauseRequest):
    """Explains a complex insurance policy clause in simple, plain English."""
    explanation = coverage_engine.explain_clause(
        clause_title=req.clause_title,
        clause_text=req.clause_text,
        verdict=req.verdict,
        insurer=req.insurer
    )
    return ExplainClauseResponse(
        clause_title=explanation.get("clause_title", req.clause_title),
        simple_explanation=explanation.get("simple_explanation", ""),
        wallet_impact=explanation.get("wallet_impact", ""),
        action_checklist=explanation.get("action_checklist", [])
    )
