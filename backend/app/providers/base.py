"""
Every provider (OpenAI, Gemini, Groq) implements this single interface.
The rest of the codebase (the agent pipeline) only ever talks to
`LLMProvider.complete(...)` — it has no idea which actual API is behind it.

This is the whole point of the abstraction: swapping/adding a provider
later means writing one new file here, not touching the pipeline.
"""

from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Raised for any provider-side failure (missing key, API error, timeout)."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Send one prompt, return the raw text completion.
        Implementations must raise ProviderError (not a provider-specific
        exception) on failure, so the router can return a clean error.
        """
        raise NotImplementedError
