from __future__ import annotations

import os
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from groq import Groq


@runtime_checkable
class LlmClientProtocol(Protocol):
    def summarize(self, prompt: str) -> str:
        """Input: prompt text. Output: one-line summary string."""


class NoOpLlmClient:
    """Does not call an API — caller should use fallback_summary instead."""

    def summarize(self, prompt: str) -> str:
        raise NotImplementedError("NoOpLlmClient does not summarize; use fallback_summary")


class GroqClient:
    """Groq free-tier client for README summarization."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self._client: Groq | None = None

    def _ensure_client(self) -> Groq:
        if not self._api_key:
            raise ValueError("GROQ_API_KEY is not set")
        if self._client is None:
            from groq import Groq

            self._client = Groq(api_key=self._api_key)
        return self._client

    def summarize(self, prompt: str) -> str:
        client = self._ensure_client()
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize the project README in one concise sentence "
                        "(max 25 words). No quotes or preamble."
                    ),
                },
                {"role": "user", "content": prompt[:8000]},
            ],
            max_tokens=80,
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()


def build_llm_client() -> LlmClientProtocol | None:
    """Return GroqClient if GROQ_API_KEY is set, else None."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return GroqClient(api_key=key)
    return None
