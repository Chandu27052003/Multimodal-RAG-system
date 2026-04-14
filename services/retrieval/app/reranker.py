import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


async def rerank(
    query: str,
    candidates: list[dict],
    top_k: int | None = None,
) -> list[dict]:
    """
    Rerank candidate chunks using NVIDIA NIM Reranking API.

    Args:
        query: The user's search query.
        candidates: List of dicts with at least 'id' and 'document' keys
                    (output from vector search).
        top_k: Number of top results to return after reranking.

    Returns:
        Candidates sorted by rerank relevance score (highest first),
        each enriched with a 'rerank_score' field.
    """
    top_k = top_k or settings.TOP_K_RERANK

    if not candidates:
        return []

    documents = [
        {"text": c["document"]} for c in candidates if c.get("document")
    ]
    if not documents:
        return []

    payload = {
        "model": settings.RERANKING_MODEL,
        "query": {"text": query},
        "passages": documents,
    }

    url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.info(
        f"Reranking {len(documents)} candidates with {settings.RERANKING_MODEL}"
    )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        logger.error(f"Reranking API error {resp.status_code}: {resp.text}")
        raise RuntimeError(
            f"NVIDIA NIM reranking API returned {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    rankings = data.get("rankings", [])

    for rank_item in rankings:
        idx = rank_item["index"]
        candidates[idx]["rerank_score"] = rank_item["logit"]

    reranked = sorted(
        [c for c in candidates if "rerank_score" in c],
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    result = reranked[:top_k]
    logger.info(
        f"Reranking complete: {len(candidates)} → top {len(result)} "
        f"(scores: {[round(r['rerank_score'], 3) for r in result]})"
    )
    return result
