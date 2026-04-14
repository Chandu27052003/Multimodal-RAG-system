from pydantic import BaseModel, Field


class AddDocumentsRequest(BaseModel):
    """Add embeddings with text and metadata to a collection."""
    collection_name: str = "default"
    ids: list[str]
    embeddings: list[list[float]]
    documents: list[str]
    metadatas: list[dict] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Query a collection with an embedding vector."""
    collection_name: str = "default"
    query_embedding: list[float]
    n_results: int = 10
    where: dict | None = Field(
        default=None,
        description="ChromaDB metadata filter (e.g. {'source_type': 'pdf'})",
    )
    where_document: dict | None = Field(
        default=None,
        description="ChromaDB document content filter",
    )


class QueryResult(BaseModel):
    id: str
    document: str | None
    metadata: dict | None
    distance: float


class QueryResponse(BaseModel):
    collection_name: str
    results: list[QueryResult]
    total: int


class DeleteRequest(BaseModel):
    collection_name: str = "default"
    ids: list[str]


class CollectionInfo(BaseModel):
    name: str
    count: int
    metadata: dict | None


class CollectionCreateRequest(BaseModel):
    name: str
    metadata: dict | None = None


class AddDocumentsResponse(BaseModel):
    collection_name: str
    added_count: int
    message: str = "Documents added successfully"


class DeleteResponse(BaseModel):
    collection_name: str
    deleted_count: int
    message: str = "Documents deleted successfully"


class DeleteByWhereRequest(BaseModel):
    collection_name: str = "default"
    where: dict = Field(..., description="Metadata filter, e.g. {'doc_id': 'doc_abc123'}")
