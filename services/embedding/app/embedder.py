import logging
from typing import Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


class NVIDIAEmbedder:
    """Client for NVIDIA NIM Embedding API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.base_url = (base_url or settings.NVIDIA_BASE_URL).rstrip("/")
        self.model = model or settings.EMBEDDING_MODEL
        self._endpoint = f"{self.base_url}/embeddings"

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. "
                "Please set it in your .env file or environment."
            )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def embed(
        self,
        texts: list[str],
        input_type: str = "passage",
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts via NVIDIA NIM API.

        Args:
            texts: List of text strings to embed.
            input_type: 'passage' for documents, 'query' for search queries.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        all_embeddings: list[list[float]] = []

        for batch_start in range(0, len(texts), settings.BATCH_SIZE):
            batch = texts[batch_start : batch_start + settings.BATCH_SIZE]

            payload = {
                "input": batch,
                "model": self.model,
                "encoding_format": "float",
                "input_type": input_type,
            }

            logger.info(
                f"Embedding batch [{batch_start}:{batch_start + len(batch)}] "
                f"of {len(texts)} texts via {self.model}"
            )

            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                response = await client.post(
                    self._endpoint,
                    headers=self._headers(),
                    json=payload,
                )

            if response.status_code != 200:
                detail = response.text
                logger.error(
                    f"NVIDIA NIM API error {response.status_code}: {detail}"
                )
                raise RuntimeError(
                    f"NVIDIA NIM embedding API returned {response.status_code}: {detail}"
                )

            data = response.json()

            batch_embeddings = sorted(data["data"], key=lambda x: x["index"])
            for item in batch_embeddings:
                all_embeddings.append(item["embedding"])

        return all_embeddings

    async def embed_single(
        self, text: str, input_type: str = "passage"
    ) -> list[float]:
        """Embed a single text string."""
        results = await self.embed([text], input_type=input_type)
        return results[0]

    async def embed_query(self, query: str) -> list[float]:
        """Embed a search query (uses input_type='query')."""
        return await self.embed_single(query, input_type="query")


_embedder: Optional[NVIDIAEmbedder] = None


def get_embedder() -> NVIDIAEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = NVIDIAEmbedder()
    return _embedder
