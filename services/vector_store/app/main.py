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
    title="Vector Store Service",
    description="Multimodal RAG - Vector Store Microservice. "
    "Persistent ChromaDB backend with collection management, "
    "document storage, and similarity search.",
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
    from .store import get_store
    store = get_store()
    collections = store.list_collections()
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "db_path": str(settings.db_path),
        "distance_metric": settings.VECTOR_DB_DISTANCE,
        "total_collections": len(collections),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
