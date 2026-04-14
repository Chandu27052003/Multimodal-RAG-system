from pydantic import BaseModel, Field


class PreprocessRequest(BaseModel):
    """Input: raw text + metadata from the ingestion service."""
    doc_id: str
    source_type: str
    filename: str | None = None
    text_content: str
    extra_metadata: dict = Field(default_factory=dict)


class ChunkResult(BaseModel):
    """A single preprocessed text chunk with inherited metadata."""
    chunk_id: str
    doc_id: str
    chunk_index: int
    total_chunks: int
    text: str
    char_count: int
    word_count: int
    source_type: str
    filename: str | None = None
    extra_metadata: dict = Field(default_factory=dict)


class PreprocessResponse(BaseModel):
    """Output: list of cleaned, chunked text segments."""
    doc_id: str
    original_char_count: int
    cleaned_char_count: int
    total_chunks: int
    chunks: list[ChunkResult]


class NormalizeRequest(BaseModel):
    """Input for standalone text normalization."""
    text: str


class NormalizeResponse(BaseModel):
    """Output of standalone text normalization."""
    original_char_count: int
    cleaned_char_count: int
    cleaned_text: str
