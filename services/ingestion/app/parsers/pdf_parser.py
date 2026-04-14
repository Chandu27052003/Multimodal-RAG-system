import logging
from pathlib import Path

from PyPDF2 import PdfReader

from .base import BaseParser

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def parse(self, file_path: Path) -> dict:
        reader = PdfReader(str(file_path))
        pages: list[str] = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                logger.warning(f"Page {i} of {file_path.name} yielded no text")
                pages.append("")

        full_text = "\n\n".join(pages)

        return {
            "text": full_text,
            "pages": pages,
            "page_count": len(reader.pages),
            "extra": {
                "pdf_metadata": reader.metadata.__dict__ if reader.metadata else {},
            },
        }
