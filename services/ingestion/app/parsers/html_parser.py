import logging
from pathlib import Path

from bs4 import BeautifulSoup

from .base import BaseParser

logger = logging.getLogger(__name__)

STRIP_TAGS = ["script", "style", "nav", "footer", "header", "noscript", "iframe"]


class HTMLParser(BaseParser):

    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]

    def parse(self, file_path: Path) -> dict:
        raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
        return self.parse_html_string(raw_html)

    def parse_html_string(self, html_content: str) -> dict:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(STRIP_TAGS):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        return {
            "text": clean_text,
            "pages": None,
            "page_count": None,
            "extra": {"title": title},
        }
