import re
import logging
import unicodedata

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript)[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)
_MULTI_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def normalize_text(text: str) -> str:
    """
    Clean and normalize raw text for downstream chunking.

    Steps:
      1. Strip script/style blocks
      2. Remove residual HTML tags
      3. Unicode normalization (NFKC)
      4. Remove control characters
      5. Normalize whitespace (collapse spaces/tabs, limit blank lines)
      6. Strip leading/trailing whitespace per line
    """
    result = _SCRIPT_STYLE_RE.sub(" ", text)

    result = _HTML_TAG_RE.sub(" ", result)

    result = unicodedata.normalize("NFKC", result)

    result = _CONTROL_CHAR_RE.sub("", result)

    lines = result.splitlines()
    cleaned_lines = [_MULTI_WHITESPACE_RE.sub(" ", line).strip() for line in lines]
    result = "\n".join(cleaned_lines)

    result = _MULTI_NEWLINE_RE.sub("\n\n", result)

    result = result.strip()

    return result
