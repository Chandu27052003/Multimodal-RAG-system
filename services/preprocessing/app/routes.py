import logging

from fastapi import APIRouter, Query

from .chunker import semantic_chunk
from .config import settings
from .metadata import build_chunk_results
from .models import (
    NormalizeRequest,
    NormalizeResponse,
    PreprocessRequest,
    PreprocessResponse,
)
from .normalizer import normalize_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/preprocess", tags=["Preprocessing"])


@router.post("/", response_model=PreprocessResponse)
async def preprocess_document(
    request: PreprocessRequest,
    chunk_size: int = Query(default=None, description="Override default chunk size (words)"),
    chunk_overlap: int = Query(default=None, description="Override default chunk overlap (words)"),
):
    """
    Full preprocessing pipeline: normalize text → semantic chunking → metadata assignment.

    Stateless — receives raw text, returns cleaned chunks with metadata.
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    original_len = len(request.text_content)

    cleaned_text = normalize_text(request.text_content)
    cleaned_len = len(cleaned_text)

    logger.info(
        f"Normalized doc {request.doc_id}: {original_len} → {cleaned_len} chars "
        f"({original_len - cleaned_len} removed)"
    )

    chunks = semantic_chunk(cleaned_text, chunk_size=size, chunk_overlap=overlap)

    chunk_results = build_chunk_results(
        doc_id=request.doc_id,
        source_type=request.source_type,
        filename=request.filename,
        extra_metadata=request.extra_metadata,
        chunks=chunks,
    )

    return PreprocessResponse(
        doc_id=request.doc_id,
        original_char_count=original_len,
        cleaned_char_count=cleaned_len,
        total_chunks=len(chunk_results),
        chunks=chunk_results,
    )


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize_only(request: NormalizeRequest):
    """Standalone text normalization without chunking."""
    cleaned = normalize_text(request.text)
    return NormalizeResponse(
        original_char_count=len(request.text),
        cleaned_char_count=len(cleaned),
        cleaned_text=cleaned,
    )
