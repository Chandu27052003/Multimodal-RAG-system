import logging
import shutil
from pathlib import Path

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from .config import settings
from .models import (
    BatchIngestionResponse,
    IngestionResponse,
    URLIngestionRequest,
    YouTubeIngestionRequest,
)
from .router import ingest_file, ingest_url, ingest_youtube, detect_source_type

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingestion"])


async def _save_upload(upload_file: UploadFile) -> Path:
    """Save an uploaded file to the uploads directory and return the path."""
    dest = settings.upload_path / upload_file.filename
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await upload_file.read(1024 * 1024):
            await f.write(chunk)
    return dest


@router.post("/file", response_model=IngestionResponse)
async def ingest_file_endpoint(file: UploadFile = File(...)):
    """Upload and ingest a single document (PDF, DOCX, TXT, HTML, Audio)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        detect_source_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = await _save_upload(file)

    try:
        doc = ingest_file(file_path, file.filename)
    except Exception as e:
        logger.error(f"Failed to ingest {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse file: {e}",
        )

    return IngestionResponse(
        doc_id=doc.metadata.doc_id,
        source_type=doc.metadata.source_type,
        filename=doc.metadata.filename,
        char_count=len(doc.text_content),
        page_count=doc.metadata.page_count,
    )


@router.post("/files", response_model=BatchIngestionResponse)
async def ingest_files_endpoint(files: list[UploadFile] = File(...)):
    """Upload and ingest multiple documents in a single request."""
    results = []
    successful = 0
    failed = 0

    for file in files:
        try:
            if not file.filename:
                raise ValueError("Filename is required")
            detect_source_type(file.filename)
            file_path = await _save_upload(file)
            doc = ingest_file(file_path, file.filename)
            results.append(
                IngestionResponse(
                    doc_id=doc.metadata.doc_id,
                    source_type=doc.metadata.source_type,
                    filename=doc.metadata.filename,
                    char_count=len(doc.text_content),
                    page_count=doc.metadata.page_count,
                )
            )
            successful += 1
        except Exception as e:
            logger.error(f"Failed to ingest {getattr(file, 'filename', '?')}: {e}")
            results.append({"filename": getattr(file, "filename", None), "error": str(e)})
            failed += 1

    return BatchIngestionResponse(
        total=len(files),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.post("/parse")
async def parse_file_endpoint(file: UploadFile = File(...)):
    """Parse a file and return the extracted text content (no persistence)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        detect_source_type(file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = await _save_upload(file)

    try:
        doc = ingest_file(file_path, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse file: {e}",
        )

    return {
        "doc_id": doc.metadata.doc_id,
        "source_type": doc.metadata.source_type.value,
        "filename": doc.metadata.filename,
        "text_content": doc.text_content,
        "char_count": len(doc.text_content),
    }


@router.post("/url/parse")
async def parse_url_endpoint(request: URLIngestionRequest):
    """Fetch a URL and return the extracted text content."""
    try:
        doc = ingest_url(request.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to fetch/parse URL: {e}",
        )

    return {
        "doc_id": doc.metadata.doc_id,
        "source_type": doc.metadata.source_type.value,
        "text_content": doc.text_content,
        "char_count": len(doc.text_content),
    }


@router.post("/url", response_model=IngestionResponse)
async def ingest_url_endpoint(request: URLIngestionRequest):
    """Ingest a webpage by URL."""
    try:
        doc = ingest_url(request.url)
    except Exception as e:
        logger.error(f"Failed to ingest URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to fetch/parse URL: {e}",
        )

    return IngestionResponse(
        doc_id=doc.metadata.doc_id,
        source_type=doc.metadata.source_type,
        filename=None,
        char_count=len(doc.text_content),
        page_count=doc.metadata.page_count,
        message=f"URL ingested successfully: {request.url}",
    )


@router.post("/youtube/parse")
async def parse_youtube_endpoint(request: YouTubeIngestionRequest):
    """Download audio from a YouTube video, transcribe it, and return the text."""
    try:
        doc = ingest_youtube(request.url)
    except Exception as e:
        logger.error(f"Failed to process YouTube URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process YouTube video: {e}",
        )

    return {
        "doc_id": doc.metadata.doc_id,
        "source_type": doc.metadata.source_type.value,
        "filename": doc.metadata.filename,
        "url": doc.metadata.url,
        "text_content": doc.text_content,
        "char_count": len(doc.text_content),
        "extra": doc.metadata.extra,
    }
