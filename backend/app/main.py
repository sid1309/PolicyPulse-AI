import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.routes_policies import router as policies_router, init_sample_policies, _load_metadata
from backend.app.api.routes_chat import router as chat_router
from backend.app.api.routes_compare import router as compare_router
from backend.app.api.routes_claims import router as claims_router
from backend.app.api.routes_eval import router as eval_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade RAG decision-support system for insurance policies with multi-policy comparison, claims math, and citations.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend (supports localhost & Vercel deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://policypulseai-lilac.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(policies_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(compare_router, prefix=settings.API_V1_PREFIX)
app.include_router(claims_router, prefix=settings.API_V1_PREFIX)
app.include_router(eval_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/health")
def health_check():
    has_gemini = bool(settings.GEMINI_API_KEY)
    has_openai = bool(settings.OPENAI_API_KEY)
    mode = "Generative Grounded RAG" if (has_gemini or has_openai) else "Deterministic Grounded RAG (Zero-Hallucination Fallback)"
    return {
        "status": "healthy",
        "engine_mode": mode,
        "has_gemini": has_gemini,
        "has_openai": has_openai,
        "neo4j_enabled": settings.NEO4J_ENABLED,
        "default_llm": settings.DEFAULT_LLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port)
