from .models import ChunkResult


def build_chunk_results(
    doc_id: str,
    source_type: str,
    filename: str | None,
    extra_metadata: dict,
    chunks: list[str],
) -> list[ChunkResult]:
    """
    Wrap raw text chunks with inherited document metadata.

    Each chunk gets:
      - A unique chunk_id (doc_id + index)
      - The parent doc_id
      - Its position (chunk_index) and total_chunks
      - Word/char counts
      - All metadata from the parent document
    """
    total = len(chunks)
    results: list[ChunkResult] = []

    for idx, text in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx:04d}"
        results.append(
            ChunkResult(
                chunk_id=chunk_id,
                doc_id=doc_id,
                chunk_index=idx,
                total_chunks=total,
                text=text,
                char_count=len(text),
                word_count=len(text.split()),
                source_type=source_type,
                filename=filename,
                extra_metadata=extra_metadata,
            )
        )

    return results
