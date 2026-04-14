from pydantic import BaseModel, Field


# ── Ingestion ──────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    doc_id: str
    source_type: str
    filename: str | None = None
    total_chunks: int
    collection_name: str
    message: str
    extra: dict | None = None


class URLIngestRequest(BaseModel):
    url: str
    collection_name: str = "default"


class YouTubeIngestRequest(BaseModel):
    url: str
    collection_name: str = "default"


# ── Query ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    collection_name: str = "default"
    top_k: int = 5
    where: dict | None = Field(default=None, description="Metadata filter")


class SourceChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: dict | None = None
    rerank_score: float | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    model: str
    sources: list[SourceChunk]
    context_token_estimate: int
    usage: dict | None = None
