from openai import AsyncOpenAI, APIError, APITimeoutError

from app.config import get_settings
from app.providers.base import LLMProvider, ProviderError

settings = get_settings()


class GroqProvider(LLMProvider):
    """
    Groq exposes an OpenAI-compatible Chat Completions endpoint, so we reuse
    the official `openai` SDK and just point it at Groq's base_url instead
    of writing a separate HTTP client. Groq's free tier + very fast
    inference makes this the easiest provider for viewers to test with.
    """

    name = "groq"

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise ProviderError(
                "GROQ_API_KEY is not set on the server. Add it to your .env file."
            )
        self._client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
        self._model = settings.GROQ_MODEL

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content or ""
        except APITimeoutError as exc:
            raise ProviderError("Groq request timed out.") from exc
        except APIError as exc:
            raise ProviderError(f"Groq API error: {exc}") from exc
