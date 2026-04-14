import logging
import uuid
from datetime import datetime
from pathlib import Path

from .config import settings
from .models import DocumentMetadata, IngestedDocument, SourceType
from .parsers import DOCXParser, HTMLParser, PDFParser, TextParser, URLParser, AudioParser, YouTubeParser

logger = logging.getLogger(__name__)

EXTENSION_TO_SOURCE: dict[str, SourceType] = {
    ".pdf": SourceType.PDF,
    ".docx": SourceType.DOCX,
    ".txt": SourceType.TXT,
    ".html": SourceType.HTML,
    ".htm": SourceType.HTML,
    ".wav": SourceType.AUDIO,
    ".mp3": SourceType.AUDIO,
    ".m4a": SourceType.AUDIO,
    ".ogg": SourceType.AUDIO,
    ".flac": SourceType.AUDIO,
    ".webm": SourceType.AUDIO,
}

_pdf_parser = PDFParser()
_docx_parser = DOCXParser()
_text_parser = TextParser()
_html_parser = HTMLParser()
_url_parser = URLParser()
_audio_parser = AudioParser(
    api_key=settings.DEEPGRAM_API_KEY,
    model=settings.DEEPGRAM_MODEL,
)

_youtube_parser = YouTubeParser(audio_parser=_audio_parser)

PARSER_MAP = {
    SourceType.PDF: _pdf_parser,
    SourceType.DOCX: _docx_parser,
    SourceType.TXT: _text_parser,
    SourceType.HTML: _html_parser,
    SourceType.AUDIO: _audio_parser,
}


def _generate_doc_id() -> str:
    return f"doc_{uuid.uuid4().hex[:12]}"


def detect_source_type(filename: str) -> SourceType:
    ext = Path(filename).suffix.lower()
    if ext not in EXTENSION_TO_SOURCE:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Supported: {list(EXTENSION_TO_SOURCE.keys())}"
        )
    return EXTENSION_TO_SOURCE[ext]


def ingest_file(file_path: Path, original_filename: str) -> IngestedDocument:
    """Parse a local file and return an IngestedDocument with metadata."""
    source_type = detect_source_type(original_filename)
    parser = PARSER_MAP[source_type]

    logger.info(f"Parsing {original_filename} as {source_type.value}")
    result = parser.parse(file_path)

    file_size = file_path.stat().st_size

    metadata = DocumentMetadata(
        doc_id=_generate_doc_id(),
        source_type=source_type,
        filename=original_filename,
        ingestion_timestamp=datetime.utcnow(),
        file_size_bytes=file_size,
        page_count=result.get("page_count"),
        extra=result.get("extra", {}),
    )

    return IngestedDocument(
        metadata=metadata,
        text_content=result["text"],
        raw_pages=result.get("pages"),
    )


def ingest_url(url: str) -> IngestedDocument:
    """Fetch a URL, extract text content, and return an IngestedDocument."""
    logger.info(f"Fetching URL: {url}")
    result = _url_parser.parse(url)

    metadata = DocumentMetadata(
        doc_id=_generate_doc_id(),
        source_type=SourceType.URL,
        url=url,
        ingestion_timestamp=datetime.utcnow(),
        extra=result.get("extra", {}),
    )

    return IngestedDocument(
        metadata=metadata,
        text_content=result["text"],
        raw_pages=result.get("pages"),
    )


def ingest_youtube(url: str) -> IngestedDocument:
    """Download audio from a YouTube video, transcribe, and return an IngestedDocument."""
    logger.info(f"Processing YouTube URL: {url}")
    result, video_info = _youtube_parser.parse(url)

    title = video_info.get("title", "")

    metadata = DocumentMetadata(
        doc_id=_generate_doc_id(),
        source_type=SourceType.YOUTUBE,
        filename=title or None,
        url=url,
        ingestion_timestamp=datetime.utcnow(),
        page_count=result.get("page_count"),
        extra=result.get("extra", {}),
    )

    return IngestedDocument(
        metadata=metadata,
        text_content=result["text"],
        raw_pages=result.get("pages"),
    )
