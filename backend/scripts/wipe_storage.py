import shutil
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
data_dir = backend_dir / "data"
storage_dir = data_dir / "storage"
policies_dir = data_dir / "policies"
backup_dir = data_dir / "policies_backup"

print("--- Step 1: Backing up PDF files if any ---")
if policies_dir.exists():
    backup_dir.mkdir(parents=True, exist_ok=True)
    for pdf_file in policies_dir.glob("*.pdf"):
        dest = backup_dir / pdf_file.name
        shutil.copy2(pdf_file, dest)
        print(f"Backed up: {pdf_file.name} -> {dest}")

print("\n--- Step 2: Deleting Qdrant vector database ---")
qdrant_dir = storage_dir / "qdrant"
if qdrant_dir.exists():
    shutil.rmtree(qdrant_dir, ignore_errors=True)
    qdrant_dir.mkdir(parents=True, exist_ok=True)
    print("Qdrant directory wiped clean.")

print("\n--- Step 3: Deleting BM25 index ---")
bm25_dir = storage_dir / "bm25"
if bm25_dir.exists():
    for f in bm25_dir.glob("*"):
        try:
            f.unlink()
            print(f"Deleted: {f.name}")
        except Exception as e:
            print(f"Error deleting {f.name}: {e}")
bm25_dir.mkdir(parents=True, exist_ok=True)

print("\n--- Step 4: Resetting policies_metadata.json ---")
meta_file = storage_dir / "policies_metadata.json"
with open(meta_file, "w", encoding="utf-8") as f:
    f.write("{}\n")
print("Reset policies_metadata.json to empty {}.")

print("\n--- Storage wipe complete! All old indexed data has been deleted. ---")
