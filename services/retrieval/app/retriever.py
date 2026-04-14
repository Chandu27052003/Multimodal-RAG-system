import logging
from typing import Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


async def get_query_embedding(query: str) -> list[float]:
    """Call the Embedding Service to get a query vector."""
    url = f"{settings.EMBEDDING_SERVICE_URL}/embed/query"
    payload = {"text": query}

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Embedding service error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["results"][0]["embedding"]


async def vector_search(
    query_embedding: list[float],
    collection_name: str,
    n_results: int,
    where: Optional[dict] = None,
) -> list[dict]:
    """Call the Vector Store Service to perform similarity search."""
    url = f"{settings.VECTOR_STORE_SERVICE_URL}/search"
    payload = {
        "collection_name": collection_name,
        "query_embedding": query_embedding,
        "n_results": n_results,
    }
    if where:
        payload["where"] = where

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Vector store search error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["results"]
