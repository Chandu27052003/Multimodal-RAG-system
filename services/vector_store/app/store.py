import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings

logger = logging.getLogger(__name__)


class ChromaStore:
    """Persistent ChromaDB wrapper supporting multiple collections."""

    def __init__(self):
        db_path = str(settings.db_path.resolve())
        logger.info(f"Initializing ChromaDB with persistent storage at: {db_path}")
        self._client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def get_or_create_collection(
        self, name: str, metadata: Optional[dict] = None,
    ) -> chromadb.Collection:
        col_metadata = {"hnsw:space": settings.VECTOR_DB_DISTANCE}
        if metadata:
            col_metadata.update(metadata)
        return self._client.get_or_create_collection(
            name=name, metadata=col_metadata,
        )

    def create_collection(
        self, name: str, metadata: Optional[dict] = None,
    ) -> chromadb.Collection:
        col_metadata = {"hnsw:space": settings.VECTOR_DB_DISTANCE}
        if metadata:
            col_metadata.update(metadata)
        return self._client.create_collection(
            name=name, metadata=col_metadata,
        )

    def get_collection(self, name: str) -> chromadb.Collection:
        return self._client.get_collection(name=name)

    def list_collections(self) -> list[dict]:
        collections = self._client.list_collections()
        results = []
        for col in collections:
            results.append({
                "name": col.name,
                "count": col.count(),
                "metadata": col.metadata,
            })
        return results

    def delete_collection(self, name: str) -> None:
        self._client.delete_collection(name=name)

    @staticmethod
    def _sanitize_metadata(meta: dict) -> dict:
        """Remove None values from metadata — ChromaDB rejects them."""
        return {k: v for k, v in meta.items() if v is not None}

    def add_documents(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: Optional[list[dict]] = None,
    ) -> int:
        collection = self.get_or_create_collection(collection_name)
        clean_meta = [
            self._sanitize_metadata(m) for m in (metadatas or [{}] * len(ids))
        ]
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_meta,
        )
        return len(ids)

    def query(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        collection = self.get_collection(collection_name)

        kwargs: dict = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        results = collection.query(**kwargs)

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i] if results["documents"] else None,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
        return output

    def delete_documents(
        self, collection_name: str, ids: list[str],
    ) -> int:
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids)
        return len(ids)

    def collection_count(self, collection_name: str) -> int:
        collection = self.get_collection(collection_name)
        return collection.count()

    def list_all(
        self,
        collection_name: str,
        include: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """Return all entries from a collection (ids, metadatas, documents)."""
        collection = self.get_collection(collection_name)
        inc = include or ["metadatas", "documents"]
        kwargs: dict = {"include": inc}
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        return collection.get(**kwargs)

    def delete_by_where(self, collection_name: str, where: dict) -> None:
        """Delete all entries matching a metadata filter."""
        collection = self.get_collection(collection_name)
        collection.delete(where=where)


_store: Optional[ChromaStore] = None


def get_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store
