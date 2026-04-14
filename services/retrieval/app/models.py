from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    """User query for retrieval."""
    query: str
    collection_name: str = "default"
    top_k: int | None = Field(default=None, description="Override TOP_K_RERANK")
    where: dict | None = Field(default=None, description="Metadata filter for vector search")


class RetrievedChunk(BaseModel):
    """A single retrieved and reranked chunk."""
    chunk_id: str
    text: str
    metadata: dict | None = None
    vector_distance: float | None = None
    rerank_score: float | None = None


class RetrievalResponse(BaseModel):
    query: str
    collection_name: str
    retrieved_count: int
    reranked_count: int
    context: str
    context_token_estimate: int
    chunks: list[RetrievedChunk]
