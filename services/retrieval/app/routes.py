import logging

from fastapi import APIRouter, HTTPException, status

from .config import settings
from .context_builder import build_context
from .models import RetrievalRequest, RetrievalResponse, RetrievedChunk
from .query_processor import normalize_query
from .reranker import rerank
from .retriever import get_query_embedding, vector_search

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/retrieve", tags=["Retrieval"])


@router.post("/", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    """
    Full retrieval pipeline:
      1. Normalize query
      2. Embed query via Embedding Service
      3. Vector search via Vector Store Service
      4. Rerank candidates via NVIDIA NIM
      5. Build context block (respecting token limit)
    """
    query = normalize_query(request.query)
    top_k = request.top_k or settings.TOP_K_RERANK

    try:
        query_embedding = await get_query_embedding(query)
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to embed query: {e}",
        )

    try:
        candidates = await vector_search(
            query_embedding=query_embedding,
            collection_name=request.collection_name,
            n_results=settings.TOP_K_RETRIEVAL,
            where=request.where,
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vector search failed: {e}",
        )

    if not candidates:
        return RetrievalResponse(
            query=query,
            collection_name=request.collection_name,
            retrieved_count=0,
            reranked_count=0,
            context="",
            context_token_estimate=0,
            chunks=[],
        )

    try:
        reranked = await rerank(query=query, candidates=candidates, top_k=top_k)
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reranking failed: {e}",
        )

    context, token_est = build_context(reranked)

    chunks = [
        RetrievedChunk(
            chunk_id=c.get("id", ""),
            text=c.get("document", ""),
            metadata=c.get("metadata"),
            vector_distance=c.get("distance"),
            rerank_score=c.get("rerank_score"),
        )
        for c in reranked
    ]

    return RetrievalResponse(
        query=query,
        collection_name=request.collection_name,
        retrieved_count=len(candidates),
        reranked_count=len(reranked),
        context=context,
        context_token_estimate=token_est,
        chunks=chunks,
    )
