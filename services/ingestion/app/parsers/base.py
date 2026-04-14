from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Base class for all document parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> dict:
        """
        Parse a file and return extracted content.

        Returns:
            dict with keys:
                - text: str (full extracted text)
                - pages: list[str] | None (per-page text if applicable)
                - page_count: int | None
                - extra: dict (parser-specific metadata)
        """
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of file extensions this parser handles."""
        ...
