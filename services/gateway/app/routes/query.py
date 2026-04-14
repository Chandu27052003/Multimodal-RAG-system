import logging

from fastapi import APIRouter, HTTPException, status

from ..models import QueryRequest, QueryResponse, SourceChunk
from ..orchestrator import query_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the knowledge base: retrieve relevant chunks, rerank, and generate
    a context-grounded answer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = await query_pipeline(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k,
            where=request.where,
        )
    except Exception as e:
        logger.error(f"Query pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query pipeline failed: {e}",
        )

    return QueryResponse(
        query=result["query"],
        answer=result["answer"],
        model=result["model"],
        sources=[SourceChunk(**s) for s in result["sources"]],
        context_token_estimate=result["context_token_estimate"],
        usage=result.get("usage"),
    )
