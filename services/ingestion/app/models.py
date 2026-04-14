from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    URL = "url"
    AUDIO = "audio"
    VIDEO = "video"
    YOUTUBE = "youtube"


class DocumentMetadata(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    source_type: SourceType
    filename: str | None = None
    url: str | None = None
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_size_bytes: int | None = None
    page_count: int | None = None
    extra: dict = Field(default_factory=dict)


class IngestedDocument(BaseModel):
    metadata: DocumentMetadata
    text_content: str
    raw_pages: list[str] | None = None


class IngestionResponse(BaseModel):
    doc_id: str
    source_type: SourceType
    filename: str | None = None
    char_count: int
    page_count: int | None = None
    message: str = "Document ingested successfully"


class URLIngestionRequest(BaseModel):
    url: str = Field(..., description="URL of the webpage to ingest")


class YouTubeIngestionRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")


class BatchIngestionResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: list[IngestionResponse | dict]
