import sys
import json
from pathlib import Path

# Add project root to path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import settings
from backend.app.parsers.clause_chunker import StructureAwareChunker
from backend.app.retrieval.vector_store import VectorStoreManager
from backend.app.retrieval.bm25_search import BM25SearchManager

def reindex_all():
    print("=== Starting Full Policy Re-indexing ===")
    meta_file = settings.STORAGE_DIR / "policies_metadata.json"
    if not meta_file.exists():
        print(f"Error: {meta_file} not found.")
        return
        
    with open(meta_file, "r", encoding="utf-8") as f:
        policies_meta = json.load(f)
        
    print(f"Found {len(policies_meta)} policies to re-index:")
    for pid, meta in policies_meta.items():
        print(f"  - {pid}: {meta.get('filename')} ({meta.get('file_path')})")

    # Clear existing BM25 index file
    bm25_mgr = BM25SearchManager()
    bm25_mgr.chunks_data = []
    bm25_mgr.tokenized_corpus = []
    bm25_mgr.bm25 = None
    bm25_mgr._save_index()
    print("Cleared BM25 index.")

    # Reset Vector Store collection
    vector_mgr = VectorStoreManager()
    try:
        vector_mgr.client.delete_collection(vector_mgr.COLLECTION_NAME)
        print(f"Deleted old Qdrant collection '{vector_mgr.COLLECTION_NAME}'.")
    except Exception as e:
        print(f"Notice during collection delete: {e}")
    vector_mgr._ensure_collection()
    print(f"Ensured fresh Qdrant collection '{vector_mgr.COLLECTION_NAME}'.")

    chunker = StructureAwareChunker()
    updated_meta = {}

    for pid, meta in policies_meta.items():
        file_path = meta.get("file_path")
        if not Path(file_path).exists():
            print(f"Warning: File not found for {pid} at {file_path}, skipping.")
            updated_meta[pid] = meta
            continue
            
        print(f"\nProcessing {pid}...")
        chunks = chunker.chunk_policy(
            file_path=file_path,
            policy_id=pid,
            insurer=meta.get("insurer", "Unknown"),
            plan_name=meta.get("plan_name", "Plan"),
            version=meta.get("version", "2024")
        )
        
        table_chunks = [c for c in chunks if c.chunk_type == "table"]
        clause_chunks = [c for c in chunks if c.chunk_type == "clause"]
        print(f"  Extracted {len(chunks)} chunks ({len(clause_chunks)} clauses, {len(table_chunks)} tables)")
        
        # Display sample table sections
        for tc in table_chunks[:3]:
            print(f"    Table: [{tc.section_name}] -> {tc.clause_title}")
            
        # Display sample clause titles
        for cc in clause_chunks[:3]:
            print(f"    Clause: [{cc.section_name}] -> {cc.clause_title}")

        # Index chunks
        vector_mgr.upsert_chunks(chunks)
        bm25_mgr.add_chunks(chunks)
        
        meta_copy = dict(meta)
        meta_copy["chunk_count"] = len(chunks)
        meta_copy["total_pages"] = max(c.page_number for c in chunks) if chunks else meta.get("total_pages", 1)
        updated_meta[pid] = meta_copy

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, indent=2)
        
    print("\n=== Re-indexing Complete! Saved updated metadata. ===")

if __name__ == "__main__":
    reindex_all()
