import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
POLICIES_DIR = DATA_DIR / "policies"
QDRANT_DIR = STORAGE_DIR / "qdrant"
BM25_DIR = STORAGE_DIR / "bm25"

# Ensure directories exist
for path in [DATA_DIR, STORAGE_DIR, POLICIES_DIR, QDRANT_DIR, BM25_DIR]:
    path.mkdir(parents=True, exist_ok=True)

from dotenv import load_dotenv

# Explicitly search and load .env from backend directory or project root
for env_path in [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
    Path.cwd() / ".env",
    Path.cwd() / "backend" / ".env"
]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Insurance Policy Intelligence & Claims Assistant"
    API_V1_PREFIX: str = "/api"
    
    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    STORAGE_DIR: Path = STORAGE_DIR
    POLICIES_DIR: Path = POLICIES_DIR
    QDRANT_DIR: Path = QDRANT_DIR
    BM25_DIR: Path = BM25_DIR
    
    # LLM & Embedding Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROG_API_KEY_1: str = os.getenv("GROG_API_KEY_1", "")
    GROG_API_KEY_2: str = os.getenv("GROG_API_KEY_2", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "groq") # "groq", "gemini" or "openai"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Embeddings & Reranker
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-large-en-v1.5"
    FAST_EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-large"
    
    # Retrieval Tuning
    DENSE_WEIGHT: float = 0.6
    SPARSE_WEIGHT: float = 0.4
    RRF_K: int = 60
    TOP_CANDIDATES_K: int = 25
    FINAL_TOP_K: int = 5
    
    # Knowledge Graph (Neo4j)
    NEO4J_ENABLED: bool = os.getenv("NEO4J_ENABLED", "false").lower() == "true"
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "insurance_rag")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
