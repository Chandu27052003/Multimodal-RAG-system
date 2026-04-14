import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from ..models import IngestResponse, URLIngestRequest, YouTubeIngestRequest
from ..orchestrator import ingest_file_pipeline, ingest_url_pipeline, ingest_youtube_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Ingestion"])


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    collection_name: str = Form(default="default"),
):
    """
    Upload a document, extract text, chunk, embed, and store in the knowledge base.

    Supported formats: PDF, DOCX, TXT, HTML, Audio (WAV, MP3, M4A, OGG, FLAC, WEBM).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_bytes = await file.read()

    try:
        result = await ingest_file_pipeline(file_bytes, file.filename, collection_name)
    except Exception as e:
        logger.error(f"File ingestion pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline failed: {e}",
        )

    return IngestResponse(**result)


@router.post("/ingest/youtube", response_model=IngestResponse)
async def ingest_youtube(request: YouTubeIngestRequest):
    """
    Download audio from a YouTube video, transcribe via Deepgram,
    chunk, embed, and store in the knowledge base.
    """
    try:
        result = await ingest_youtube_pipeline(request.url, request.collection_name)
    except Exception as e:
        logger.error(f"YouTube ingestion pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YouTube ingestion pipeline failed: {e}",
        )

    return IngestResponse(**result)

@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(request: URLIngestRequest):
    """
    Fetch a webpage, extract text, chunk, embed, and store in the knowledge base.
    """
    try:
        result = await ingest_url_pipeline(request.url, request.collection_name)
    except Exception as e:
        logger.error(f"URL ingestion pipeline failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL ingestion pipeline failed: {e}",
        )

    return IngestResponse(**result)
