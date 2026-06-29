from openai import AsyncOpenAI, APIError, APITimeoutError

from app.config import get_settings
from app.providers.base import LLMProvider, ProviderError

settings = get_settings()


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ProviderError(
                "OPENAI_API_KEY is not set on the server. Add it to your .env file."
            )
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

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
            raise ProviderError("OpenAI request timed out.") from exc
        except APIError as exc:
            raise ProviderError(f"OpenAI API error: {exc}") from exc
