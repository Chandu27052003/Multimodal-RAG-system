import logging

from fastapi import APIRouter, HTTPException, status

from .config import settings
from .embedder import get_embedder
from .models import (
    EmbedBatchRequest,
    EmbedRequest,
    EmbedResponse,
    EmbeddingResult,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/embed", tags=["Embedding"])


@router.post("/single", response_model=EmbedResponse)
async def embed_single(request: EmbedRequest):
    """Generate embedding for a single text chunk."""
    try:
        embedder = get_embedder()
        vector = await embedder.embed_single(request.text, input_type=request.input_type)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding generation failed: {e}",
        )

    return EmbedResponse(
        model=settings.EMBEDDING_MODEL,
        embedding_dim=len(vector),
        total=1,
        results=[
            EmbeddingResult(
                index=0,
                embedding=vector,
                char_count=len(request.text),
            )
        ],
    )


@router.post("/batch", response_model=EmbedResponse)
async def embed_batch(request: EmbedBatchRequest):
    """Generate embeddings for multiple text chunks."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="texts list cannot be empty")

    try:
        embedder = get_embedder()
        vectors = await embedder.embed(request.texts, input_type=request.input_type)
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Batch embedding failed: {e}",
        )

    results = [
        EmbeddingResult(
            index=i,
            embedding=vec,
            char_count=len(request.texts[i]),
        )
        for i, vec in enumerate(vectors)
    ]

    return EmbedResponse(
        model=settings.EMBEDDING_MODEL,
        embedding_dim=len(vectors[0]) if vectors else 0,
        total=len(results),
        results=results,
    )


@router.post("/query", response_model=EmbedResponse)
async def embed_query(request: EmbedRequest):
    """Generate embedding for a search query (uses input_type='query')."""
    try:
        embedder = get_embedder()
        vector = await embedder.embed_query(request.text)
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Query embedding failed: {e}",
        )

    return EmbedResponse(
        model=settings.EMBEDDING_MODEL,
        embedding_dim=len(vector),
        total=1,
        results=[
            EmbeddingResult(
                index=0,
                embedding=vector,
                char_count=len(request.text),
            )
        ],
    )
