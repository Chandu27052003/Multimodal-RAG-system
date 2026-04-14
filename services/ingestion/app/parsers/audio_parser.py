import logging
from pathlib import Path

import requests

from .base import BaseParser

logger = logging.getLogger(__name__)

EXTENSION_MIME = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
}

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


class AudioParser(BaseParser):
    """Transcribe audio files via the Deepgram pre-recorded REST API."""

    def __init__(self, api_key: str, model: str = "nova-2"):
        self._api_key = api_key
        self._model = model

    # ── BaseParser interface ──────────────────────────────────────

    def parse(self, file_path: Path) -> dict:
        ext = file_path.suffix.lower()
        mime = EXTENSION_MIME.get(ext, "audio/wav")

        audio_bytes = file_path.read_bytes()
        logger.info(
            f"Sending {file_path.name} ({len(audio_bytes)} bytes, {mime}) to Deepgram"
        )

        params = {
            "model": self._model,
            "language": "en",
            "smart_format": "true",
            "paragraphs": "true",
            "utterances": "true",
            "punctuate": "true",
        }

        resp = requests.post(
            DEEPGRAM_URL,
            params=params,
            headers={
                "Authorization": f"Token {self._api_key}",
                "Content-Type": mime,
            },
            data=audio_bytes,
            timeout=300,
        )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Deepgram API returned {resp.status_code}: {resp.text}"
            )

        result = resp.json()
        return self._extract(result)

    def supported_extensions(self) -> list[str]:
        return list(EXTENSION_MIME.keys())

    # ── Internal helpers ──────────────────────────────────────────

    @staticmethod
    def _extract(dg_response: dict) -> dict:
        """Pull transcript, paragraphs, and metadata from the Deepgram response."""
        results = dg_response.get("results", {})
        channels = results.get("channels", [{}])
        alternatives = channels[0].get("alternatives", [{}]) if channels else [{}]
        best = alternatives[0] if alternatives else {}

        transcript = best.get("transcript", "")
        confidence = best.get("confidence", 0.0)

        paragraphs_obj = best.get("paragraphs", {})
        paragraph_texts = []
        if paragraphs_obj and paragraphs_obj.get("paragraphs"):
            for para in paragraphs_obj["paragraphs"]:
                sentences = para.get("sentences", [])
                para_text = " ".join(s.get("text", "") for s in sentences)
                if para_text.strip():
                    paragraph_texts.append(para_text.strip())

        full_text = "\n\n".join(paragraph_texts) if paragraph_texts else transcript

        metadata = dg_response.get("metadata", {})
        duration = metadata.get("duration", 0.0)
        model_info = metadata.get("model_info", {})
        model_name = ""
        if model_info:
            first_model = next(iter(model_info.values()), {})
            model_name = first_model.get("name", "")

        utterances = results.get("utterances", [])

        return {
            "text": full_text,
            "pages": paragraph_texts or None,
            "page_count": len(paragraph_texts) if paragraph_texts else None,
            "extra": {
                "duration_seconds": round(duration, 2),
                "confidence": round(confidence, 4),
                "deepgram_model": model_name,
                "utterance_count": len(utterances),
            },
        }
