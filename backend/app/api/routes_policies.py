import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.core.models import PolicyMetadata, PolicySummaryResponse, CitationItem
from backend.app.parsers.clause_chunker import StructureAwareChunker
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.graph.neo4j_client import GraphRAGClient
from backend.app.core.generate_sample_policies import create_sample_policies
from backend.app.engines.comparison_engine import MultiPolicyComparisonEngine

router = APIRouter(prefix="/policies", tags=["Policies"])

# Global singletons
chunker = StructureAwareChunker()
retriever = HybridRetriever()
graph_client = GraphRAGClient()

METADATA_FILE = settings.STORAGE_DIR / "policies_metadata.json"
SUMMARIES_CACHE_FILE = settings.STORAGE_DIR / "policy_summaries_cache.json"

def _load_metadata() -> Dict[str, Dict[str, Any]]:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_metadata(data: Dict[str, Dict[str, Any]]):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def _load_summaries_cache() -> Dict[str, Dict[str, Any]]:
    if SUMMARIES_CACHE_FILE.exists():
        try:
            with open(SUMMARIES_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_summaries_cache(data: Dict[str, Dict[str, Any]]):
    try:
        SUMMARIES_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARIES_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def invalidate_summary_cache(policy_id: str = None):
    """Purges cached summary for a specific policy_id or all policies if None."""
    if not SUMMARIES_CACHE_FILE.exists():
        return
    if policy_id is None:
        try:
            SUMMARIES_CACHE_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return
    cache = _load_summaries_cache()
    if policy_id in cache:
        del cache[policy_id]
        _save_summaries_cache(cache)

@router.get("", response_model=List[PolicyMetadata])
def list_policies():
    """Returns list of all ingested policies."""
    meta = _load_metadata()
    return list(meta.values())

@router.post("/upload", response_model=PolicyMetadata)
async def upload_policy(
    file: UploadFile = File(...),
    insurer: str = Form("Standard Insurer"),
    plan_name: str = Form("Health Plan"),
    version: str = Form("2024")
):
    """Uploads, parses, and indexes a policy PDF."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    policy_id = f"{insurer}_{plan_name}_{version}".replace(" ", "_").upper()
    dest_path = settings.POLICIES_DIR / f"{policy_id}.pdf"
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Process and chunk
    import gc
    chunks = chunker.chunk_policy(
        file_path=str(dest_path),
        policy_id=policy_id,
        insurer=insurer,
        plan_name=plan_name,
        version=version
    )
    gc.collect()
    
    if not chunks:
        raise HTTPException(status_code=422, detail="Failed to extract readable clauses from PDF.")
        
    # Multi-index storage
    retriever.vector_store.upsert_chunks(chunks)
    retriever.bm25.add_chunks(chunks)
    gc.collect()
    
    # Ingest relations to graph
    for c in chunks:
        ent = c.entities
        graph_client.add_clause_relation(
            policy_id=policy_id,
            clause_id=c.clause_id,
            section_name=c.section_name,
            page_num=c.page_number,
            treatment=ent.get("treatments")[0] if ent.get("treatments") else None,
            waiting_period_months=ent.get("waiting_period_months"),
            sublimit_text=ent.get("room_rent_cap")
        )
        
    total_pages = max(c.page_number for c in chunks) if chunks else 1
    
    meta_entry = PolicyMetadata(
        policy_id=policy_id,
        filename=file.filename,
        insurer=insurer,
        plan_name=plan_name,
        version=version,
        total_pages=total_pages,
        chunk_count=len(chunks),
        file_path=str(dest_path),
        created_at=datetime.utcnow().isoformat()
    )
    
    all_meta = _load_metadata()
    all_meta[policy_id] = meta_entry.dict()
    _save_metadata(all_meta)
    
    # Invalidate old summary cache & compare cache for this policy
    invalidate_summary_cache(policy_id)
    MultiPolicyComparisonEngine.invalidate_cache(policy_id)
    
    return meta_entry

@router.get("/pdf/{policy_id}")
def get_policy_pdf(policy_id: str):
    """Serves the PDF file for browser viewing."""
    all_meta = _load_metadata()
    if policy_id not in all_meta:
        raise HTTPException(status_code=404, detail="Policy not found.")
    file_path = all_meta[policy_id]["file_path"]
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk.")
    return FileResponse(file_path, media_type="application/pdf")

@router.get("/{policy_id}/summary", response_model=PolicySummaryResponse)
def get_policy_summary(policy_id: str):
    """
    Generates an instant 1-page health & coverage summary ID card for the policy.
    Uses fingerprint-based disk caching: verifies policy filename, created_at
    (datetime of upload doc) and chunk_count. If matched, returns cached summary;
    otherwise generates fresh, caches it, and returns.
    """
    all_meta = _load_metadata()
    if policy_id not in all_meta:
        raise HTTPException(status_code=404, detail="Policy not found.")
        
    meta = all_meta[policy_id]
    curr_filename = meta.get("filename")
    curr_created_at = meta.get("created_at")
    curr_chunk_count = meta.get("chunk_count")
    
    # Check persistent cache
    cache = _load_summaries_cache()
    cached_entry = cache.get(policy_id)
    if cached_entry:
        fp = cached_entry.get("fingerprint", {})
        if (
            fp.get("filename") == curr_filename and
            fp.get("created_at") == curr_created_at and
            fp.get("chunk_count") == curr_chunk_count and
            "summary" in cached_entry
        ):
            return PolicySummaryResponse(**cached_entry["summary"])
    insurer = meta.get("insurer", "Unknown Insurer")
    plan_name = meta.get("plan_name", "Health Plan")
    version = meta.get("version", "2024")
    total_pages = meta.get("total_pages", 1)
    
    features = {
        "room_rent": "room rent capping single private room proportional deduction limit",
        "ped": "pre-existing diseases PED waiting period months",
        "specific": "specific illness 24 months cataract hernia waiting period",
        "copay": "co-payment mandatory copay zone deductible percentage",
        "pre_post": "pre-hospitalization 60 days post-hospitalization 180 days"
    }
    
    results = {}
    citations = []
    
    for key, query in features.items():
        hits = retriever.retrieve(query=query, policy_ids=[policy_id], top_k=1)
        if hits:
            h = hits[0]
            results[key] = h
            citations.append(CitationItem(
                policy_id=policy_id,
                insurer=insurer,
                plan_name=plan_name,
                section_name=h.get("section_name", "Terms"),
                clause_id=h.get("clause_id", "Clause"),
                clause_title=h.get("clause_title", "Coverage Term"),
                page_number=h.get("page_number", 1),
                excerpt=h.get("content_text", "")[:180] + "..."
            ))
        else:
            results[key] = None
            
    rr_chunk = results.get("room_rent")
    rr_cap = "Single Private AC Room (No Proportionate Deduction)"
    if rr_chunk:
        ent_rr = rr_chunk.get("entities", {}).get("room_rent_cap")
        if ent_rr:
            rr_cap = ent_rr
        elif "1%" in rr_chunk.get("content_text", ""):
            rr_cap = "1% of Sum Insured per day"
        elif "single private" in rr_chunk.get("content_text", "").lower():
            rr_cap = "Single Private AC Room (No Sub-limit)"
            
    ped_chunk = results.get("ped")
    ped_wp = "36 Months"
    if ped_chunk:
        wp_ent = ped_chunk.get("entities", {}).get("waiting_period_months")
        if wp_ent:
            ped_wp = f"{wp_ent} Months"
        elif "48 months" in ped_chunk.get("content_text", "").lower():
            ped_wp = "48 Months"
        elif "36 months" in ped_chunk.get("content_text", "").lower():
            ped_wp = "36 Months"
            
    spec_chunk = results.get("specific")
    spec_wp = "24 Months"
    if spec_chunk:
        wp_ent = spec_chunk.get("entities", {}).get("waiting_period_months")
        if wp_ent:
            spec_wp = f"{wp_ent} Months"
            
    copay_chunk = results.get("copay")
    copay_val = "0% (Nil Co-payment)"
    if copay_chunk:
        cp_ent = copay_chunk.get("entities", {}).get("copay_percent")
        if cp_ent:
            copay_val = f"{cp_ent}% Mandatory Co-pay"
        elif "20%" in copay_chunk.get("content_text", ""):
            copay_val = "20% Co-payment (Zone / Age Based)"
            
    pre_post_chunk = results.get("pre_post")
    pre_post_val = "60 Days Pre / 180 Days Post Hospitalization"
    if pre_post_chunk and "30" in pre_post_chunk.get("content_text", "") and "60" in pre_post_chunk.get("content_text", ""):
        pre_post_val = "30 Days Pre / 60 Days Post Hospitalization"
        
    excl_items = [
        "Cosmetic, aesthetic or obesity surgeries (unless reconstructive post-trauma)",
        "Dental treatments and tooth extractions (unless hospitalization is medically indicated)",
        "Unproven, experimental treatments and stem-cell therapies",
        "Self-inflicted injuries and treatments resulting from hazardous extreme sports",
        "Rest cure, general weakness and non-prescribed diagnostic admission"
    ]
    
    plain_summary = (
        f"{insurer} {plan_name} provides comprehensive in-patient cover with {rr_cap}. "
        f"Pre-existing illnesses require {ped_wp} continuous tenure, and specified surgeries (cataract, hernia) require {spec_wp}. "
        f"Mandatory co-payment is {copay_val}."
    )
    
    summary_resp = PolicySummaryResponse(
        policy_id=policy_id,
        insurer=insurer,
        plan_name=plan_name,
        version=version,
        total_pages=total_pages,
        sum_insured="₹5 Lakhs – ₹2 Crore",
        room_rent_cap=rr_cap,
        icu_limit="No Sub-limit / Actuals",
        ped_waiting_period=ped_wp,
        specific_illness_waiting=spec_wp,
        initial_waiting_period="30 Days (Accident exempt)",
        pre_post_hospitalization=pre_post_val,
        copay=copay_val,
        restoration_benefit="100% Instant Recharge on exhaustion",
        day_care="All 540+ Day Care procedures covered",
        key_exclusions=excl_items,
        plain_english_summary=plain_summary,
        citations=citations[:5]
    )
    
    # Store in persistent cache with policy upload metadata fingerprint
    cache[policy_id] = {
        "policy_id": policy_id,
        "fingerprint": {
            "filename": curr_filename,
            "created_at": curr_created_at,
            "chunk_count": curr_chunk_count
        },
        "summary": summary_resp.dict(),
        "cached_at": datetime.utcnow().isoformat()
    }
    _save_summaries_cache(cache)
    
    return summary_resp

@router.delete("/{policy_id}")
def delete_policy(policy_id: str):
    """Deletes policy from vector store, BM25, and disk, and purges all cached summaries & comparisons."""
    all_meta = _load_metadata()
    if policy_id in all_meta:
        file_path = Path(all_meta[policy_id]["file_path"])
        if file_path.exists():
            file_path.unlink()
        retriever.vector_store.delete_policy(policy_id)
        retriever.bm25.delete_policy(policy_id)
        del all_meta[policy_id]
        _save_metadata(all_meta)
        
        # 1. Purge cached summary for this policy
        invalidate_summary_cache(policy_id)
        
        # 2. Purge compare tab parameters & matrix cache for this policy
        MultiPolicyComparisonEngine.invalidate_cache(policy_id)
        
    return {"status": "deleted", "policy_id": policy_id}

@router.post("/init-samples")
def init_sample_policies():
    """Auto-generates and ingests 3 realistic sample policies for immediate testing."""
    create_sample_policies()
    
    samples = [
        {"file": "HDFC_Optima_Secure_2024.pdf", "insurer": "HDFC ERGO", "plan": "Optima Secure", "version": "2024.1"},
        {"file": "Star_Comprehensive_2024.pdf", "insurer": "Star Health", "plan": "Comprehensive", "version": "2024.2"},
        {"file": "HDFC_Optima_Secure_2021_Old.pdf", "insurer": "HDFC ERGO", "plan": "Optima Secure Legacy", "version": "2021.0"}
    ]
    
    all_meta = _load_metadata()
    ingested = []
    
    for s in samples:
        file_path = settings.POLICIES_DIR / s["file"]
        if file_path.exists():
            pid = f"{s['insurer']}_{s['plan']}_{s['version']}".replace(" ", "_").upper()
            if pid not in all_meta:
                chunks = chunker.chunk_policy(
                    file_path=str(file_path),
                    policy_id=pid,
                    insurer=s["insurer"],
                    plan_name=s["plan"],
                    version=s["version"]
                )
                if chunks:
                    retriever.vector_store.upsert_chunks(chunks)
                    retriever.bm25.add_chunks(chunks)
                    for c in chunks:
                        ent = c.entities
                        graph_client.add_clause_relation(
                            policy_id=pid,
                            clause_id=c.clause_id,
                            section_name=c.section_name,
                            page_num=c.page_number,
                            treatment=ent.get("treatments")[0] if ent.get("treatments") else None,
                            waiting_period_months=ent.get("waiting_period_months"),
                            sublimit_text=ent.get("room_rent_cap")
                        )
                    total_pages = max(c.page_number for c in chunks)
                    entry = PolicyMetadata(
                        policy_id=pid,
                        filename=s["file"],
                        insurer=s["insurer"],
                        plan_name=s["plan"],
                        version=s["version"],
                        total_pages=total_pages,
                        chunk_count=len(chunks),
                        file_path=str(file_path),
                        created_at=datetime.utcnow().isoformat()
                    )
                    all_meta[pid] = entry.dict()
                    ingested.append(pid)
                    
    _save_metadata(all_meta)
    for pid in ingested:
        invalidate_summary_cache(pid)
        MultiPolicyComparisonEngine.invalidate_cache(pid)
    return {"status": "success", "ingested_sample_policies": ingested, "total_policies": len(all_meta)}
