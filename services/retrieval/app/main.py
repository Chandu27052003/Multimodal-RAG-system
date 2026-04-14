import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(settings.SERVICE_NAME)

app = FastAPI(
    title="Retrieval Service",
    description="Multimodal RAG - Retrieval Microservice. "
    "Processes queries through embedding → vector search → "
    "neural reranking → context construction pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "reranking_model": settings.RERANKING_MODEL,
        "top_k_retrieval": settings.TOP_K_RETRIEVAL,
        "top_k_rerank": settings.TOP_K_RERANK,
        "context_token_limit": settings.CONTEXT_TOKEN_LIMIT,
        "embedding_service": settings.EMBEDDING_SERVICE_URL,
        "vector_store_service": settings.VECTOR_STORE_SERVICE_URL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
