import logging

from .config import settings

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 words per token for English text."""
    return int(len(text.split()) / 0.75)


def build_context(
    chunks: list[dict],
    token_limit: int | None = None,
) -> tuple[str, int]:
    """
    Aggregate reranked chunks into a unified context block.

    Chunks are added in rerank-score order until the token limit is reached.
    Each chunk is prefixed with its source info for traceability.

    Args:
        chunks: Reranked candidate dicts (must have 'document' and optionally 'metadata').
        token_limit: Max tokens for the assembled context.

    Returns:
        (context_string, token_estimate)
    """
    limit = token_limit or settings.CONTEXT_TOKEN_LIMIT
    context_parts: list[str] = []
    running_tokens = 0

    for i, chunk in enumerate(chunks):
        text = chunk.get("document", "")
        if not text:
            continue

        source = ""
        meta = chunk.get("metadata") or {}
        if meta.get("filename"):
            source = f"[Source: {meta['filename']}"
            if meta.get("chunk_index") is not None:
                source += f", chunk {meta['chunk_index']}"
            source += "]"
        elif meta.get("doc_id"):
            source = f"[Source: {meta['doc_id']}]"

        block = f"{source}\n{text}" if source else text
        block_tokens = estimate_tokens(block)

        if running_tokens + block_tokens > limit:
            remaining = limit - running_tokens
            if remaining > 50:
                words = block.split()
                truncated_words = words[:int(remaining * 0.75)]
                context_parts.append(" ".join(truncated_words) + " ...")
                running_tokens += len(truncated_words)
            break

        context_parts.append(block)
        running_tokens += block_tokens

    context = "\n\n---\n\n".join(context_parts)
    final_tokens = estimate_tokens(context)

    logger.info(
        f"Context built: {len(context_parts)} chunks, "
        f"~{final_tokens} tokens (limit: {limit})"
    )
    return context, final_tokens
