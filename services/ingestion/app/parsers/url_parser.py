import logging

import requests

from .html_parser import HTMLParser

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (compatible; MultimodalRAG/1.0; +https://github.com/multimodal-rag)"
)


class URLParser:
    """Fetches a webpage via URL and extracts readable text content."""

    def __init__(self):
        self._html_parser = HTMLParser()

    def parse(self, url: str) -> dict:
        headers = {"User-Agent": USER_AGENT}

        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise ValueError(
                f"Unsupported content type '{content_type}' from URL: {url}"
            )

        result = self._html_parser.parse_html_string(response.text)
        result["extra"]["source_url"] = url
        result["extra"]["status_code"] = response.status_code
        result["extra"]["content_type"] = content_type

        return result
