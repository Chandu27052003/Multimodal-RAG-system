import re
import unicodedata


_MULTI_WHITESPACE_RE = re.compile(r"\s+")


def normalize_query(query: str) -> str:
    """
    Normalize a user query for consistent embedding and retrieval.

    Steps:
      1. Unicode normalization (NFKC)
      2. Strip leading/trailing whitespace
      3. Collapse internal whitespace to single spaces
    """
    result = unicodedata.normalize("NFKC", query)
    result = _MULTI_WHITESPACE_RE.sub(" ", result)
    result = result.strip()
    return result
