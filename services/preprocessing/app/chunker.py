import logging

import nltk

nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

logger = logging.getLogger(__name__)


def _word_count(text: str) -> int:
    return len(text.split())


def semantic_chunk(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks using sentence boundaries.

    Algorithm:
      1. Tokenize the text into sentences.
      2. Accumulate sentences into a chunk until adding the next sentence
         would exceed `chunk_size` (measured in words).
      3. When the limit is hit, finalize the chunk and start the next one
         by carrying over enough trailing sentences to cover `chunk_overlap`
         words (preserving cross-boundary context).

    Args:
        text: Cleaned input text.
        chunk_size: Target maximum words per chunk.
        chunk_overlap: Target overlap words between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text.strip():
        return []

    sentences = sent_tokenize(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_word_count = 0

    for sentence in sentences:
        s_words = _word_count(sentence)

        if current_word_count + s_words > chunk_size and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(chunk_text)

            overlap_sentences: list[str] = []
            overlap_words = 0
            for s in reversed(current_sentences):
                sw = _word_count(s)
                if overlap_words + sw > chunk_overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_words += sw

            current_sentences = overlap_sentences
            current_word_count = overlap_words

        current_sentences.append(sentence)
        current_word_count += s_words

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        if chunks and chunk_text == chunks[-1]:
            pass
        else:
            chunks.append(chunk_text)

    logger.info(
        f"Chunked {len(sentences)} sentences into {len(chunks)} chunks "
        f"(target size={chunk_size}, overlap={chunk_overlap})"
    )
    return chunks
