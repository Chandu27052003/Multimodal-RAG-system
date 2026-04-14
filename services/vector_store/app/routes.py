import logging

from fastapi import APIRouter, HTTPException, status

from .models import (
    AddDocumentsRequest,
    AddDocumentsResponse,
    CollectionCreateRequest,
    CollectionInfo,
    DeleteByWhereRequest,
    DeleteRequest,
    DeleteResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
)
from .store import get_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Vector Store"])


# ── Collection management ──────────────────────────────────────────

@router.get("/collections", response_model=list[CollectionInfo])
async def list_collections():
    """List all vector collections with their document counts."""
    store = get_store()
    return store.list_collections()


@router.post("/collections", response_model=CollectionInfo, status_code=201)
async def create_collection(request: CollectionCreateRequest):
    """Create a new vector collection."""
    store = get_store()
    try:
        col = store.create_collection(request.name, metadata=request.metadata)
    except Exception as e:
        raise HTTPException(status_code=409, detail=f"Collection error: {e}")
    return CollectionInfo(name=request.name, count=0, metadata=col.metadata)


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Delete a vector collection and all its data."""
    store = get_store()
    try:
        store.delete_collection(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {e}")
    return {"message": f"Collection '{name}' deleted"}


@router.get("/collections/{name}", response_model=CollectionInfo)
async def get_collection_info(name: str):
    """Get info about a specific collection."""
    store = get_store()
    try:
        count = store.collection_count(name)
        col = store.get_collection(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {e}")
    return CollectionInfo(name=name, count=count, metadata=col.metadata)


# ── Document operations ────────────────────────────────────────────

@router.post("/documents", response_model=AddDocumentsResponse)
async def add_documents(request: AddDocumentsRequest):
    """Add embeddings with text and metadata to a collection."""
    if len(request.ids) != len(request.embeddings) != len(request.documents):
        raise HTTPException(
            status_code=400,
            detail="ids, embeddings, and documents must have the same length",
        )

    store = get_store()
    try:
        count = store.add_documents(
            collection_name=request.collection_name,
            ids=request.ids,
            embeddings=request.embeddings,
            documents=request.documents,
            metadatas=request.metadatas if request.metadatas else None,
        )
    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add documents: {e}",
        )

    return AddDocumentsResponse(
        collection_name=request.collection_name,
        added_count=count,
    )


@router.delete("/documents", response_model=DeleteResponse)
async def delete_documents(request: DeleteRequest):
    """Delete documents by IDs from a collection."""
    store = get_store()
    try:
        count = store.delete_documents(request.collection_name, request.ids)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return DeleteResponse(
        collection_name=request.collection_name,
        deleted_count=count,
    )


# ── Search ─────────────────────────────────────────────────────────

@router.post("/search", response_model=QueryResponse)
async def search(request: QueryRequest):
    """Similarity search over a collection using a query embedding."""
    store = get_store()
    try:
        results = store.query(
            collection_name=request.collection_name,
            query_embedding=request.query_embedding,
            n_results=request.n_results,
            where=request.where,
            where_document=request.where_document,
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {e}",
        )

    return QueryResponse(
        collection_name=request.collection_name,
        results=[QueryResult(**r) for r in results],
        total=len(results),
    )


# ── List all / delete by metadata ─────────────────────────────────

@router.get("/documents")
async def list_documents(collection_name: str = "default"):
    """Return all document IDs and metadata from a collection."""
    store = get_store()
    try:
        data = store.list_all(collection_name, include=["metadatas"])
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    entries = []
    for i, doc_id in enumerate(data["ids"]):
        meta = data["metadatas"][i] if data.get("metadatas") else {}
        entries.append({"id": doc_id, "metadata": meta})

    return {"collection_name": collection_name, "entries": entries, "total": len(entries)}


@router.post("/documents/delete-by-metadata")
async def delete_documents_by_metadata(request: DeleteByWhereRequest):
    """Delete all documents matching a metadata filter (e.g. doc_id)."""
    store = get_store()
    try:
        before = store.collection_count(request.collection_name)
        store.delete_by_where(request.collection_name, request.where)
        after = store.collection_count(request.collection_name)
    except Exception as e:
        logger.error(f"Delete by metadata failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {e}",
        )

    deleted = before - after
    return {
        "collection_name": request.collection_name,
        "deleted_count": deleted,
        "message": f"Deleted {deleted} chunk(s)",
    }
