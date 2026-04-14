import logging
from pathlib import Path

from .base import BaseParser

logger = logging.getLogger(__name__)


class TextParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".txt"]

    def parse(self, file_path: Path) -> dict:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for enc in encodings:
            try:
                text = file_path.read_text(encoding=enc)
                return {
                    "text": text,
                    "pages": None,
                    "page_count": None,
                    "extra": {"encoding_detected": enc},
                }
            except (UnicodeDecodeError, ValueError):
                continue

        raise ValueError(
            f"Could not decode {file_path.name} with any supported encoding"
        )
