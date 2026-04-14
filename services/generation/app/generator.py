import logging
import re
from typing import Optional

from openai import OpenAI

from .config import settings
from .prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class NVIDIAGenerator:
    """Client for NVIDIA NIM Chat Completions API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.NVIDIA_API_KEY
        self.base_url = base_url or settings.NVIDIA_BASE_URL
        self.model = model or settings.GENERATION_MODEL

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. "
                "Please set it in your .env file or environment."
            )

        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def generate(
        self,
        query: str,
        context: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """
        Generate a context-grounded response.

        Args:
            query: The user's question.
            context: Retrieved context block.
            temperature: Sampling temperature override.
            max_tokens: Max tokens override.

        Returns:
            dict with 'answer', 'model', and 'usage' keys.
        """
        user_message = build_user_prompt(query, context)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        logger.info(f"Generating response with {self.model} (temp={temperature or settings.TEMPERATURE})")

        completion = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or settings.TEMPERATURE,
            top_p=settings.TOP_P,
            max_tokens=max_tokens or settings.MAX_TOKENS,
            stream=False,
        )

        raw_answer = completion.choices[0].message.content or ""
        answer = self._normalize_latex(raw_answer)
        usage = None
        if completion.usage:
            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
            }

        logger.info(f"Generation complete: {len(answer)} chars, usage={usage}")

        return {
            "answer": answer,
            "model": self.model,
            "usage": usage,
        }


    @staticmethod
    def _normalize_latex(text: str) -> str:
        """Convert \\( \\) and \\[ \\] delimiters to $ and $$ for Streamlit rendering."""
        text = re.sub(r'\\\[', '$$', text)
        text = re.sub(r'\\\]', '$$', text)
        text = re.sub(r'\\\(', '$', text)
        text = re.sub(r'\\\)', '$', text)
        return text


_generator: Optional[NVIDIAGenerator] = None


def get_generator() -> NVIDIAGenerator:
    global _generator
    if _generator is None:
        _generator = NVIDIAGenerator()
    return _generator
