import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .orchestrator import check_service_health
from .routes import ingest_router, query_router, kb_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(settings.SERVICE_NAME)

app = FastAPI(
    title="Multimodal RAG API Gateway",
    description="Public-facing API for the Multimodal RAG system. "
    "Orchestrates document ingestion, knowledge base querying, "
    "and context-grounded response generation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(kb_router)


@app.get("/health")
async def health_check():
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
    }


@app.get("/health/services")
async def services_health():
    """Check health of all downstream microservices."""
    services = {
        "ingestion": settings.INGESTION_SERVICE_URL,
        "preprocessing": settings.PREPROCESSING_SERVICE_URL,
        "embedding": settings.EMBEDDING_SERVICE_URL,
        "vector_store": settings.VECTOR_STORE_SERVICE_URL,
        "retrieval": settings.RETRIEVAL_SERVICE_URL,
        "generation": settings.GENERATION_SERVICE_URL,
    }
    results = []
    for name, url in services.items():
        result = await check_service_health(name, url)
        results.append(result)

    all_healthy = all(r["status"] == "healthy" for r in results)
    return {
        "gateway": "healthy",
        "all_services_healthy": all_healthy,
        "services": results,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
