import logging

from fastapi import APIRouter, HTTPException, status

from ..orchestrator import list_collections, list_knowledge_base, delete_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge-base", tags=["Knowledge Base"])


@router.get("/collections")
async def get_collections():
    """List all available vector collections."""
    try:
        return await list_collections()
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {e}",
        )


@router.get("/")
async def get_knowledge_base(collection_name: str = "default"):
    """List all documents in the knowledge base, grouped by doc_id."""
    try:
        return await list_knowledge_base(collection_name)
    except Exception as e:
        logger.error(f"Failed to list knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {e}",
        )


@router.delete("/{doc_id}")
async def delete_kb_document(doc_id: str, collection_name: str = "default"):
    """Delete a document and all its chunks from the knowledge base."""
    try:
        return await delete_document(collection_name, doc_id)
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {e}",
        )
