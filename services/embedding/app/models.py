from pydantic import BaseModel, Field


class EmbedRequest(BaseModel):
    """Embed a single text chunk."""
    text: str
    input_type: str = Field(
        default="passage",
        description="'passage' for document chunks, 'query' for search queries",
    )


class EmbedBatchRequest(BaseModel):
    """Embed multiple text chunks in one call."""
    texts: list[str]
    input_type: str = Field(
        default="passage",
        description="'passage' for document chunks, 'query' for search queries",
    )


class EmbeddingResult(BaseModel):
    index: int
    embedding: list[float]
    char_count: int


class EmbedResponse(BaseModel):
    model: str
    embedding_dim: int
    results: list[EmbeddingResult]
    total: int
