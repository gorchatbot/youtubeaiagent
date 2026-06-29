from google import genai
from google.genai import types
from google.genai.errors import APIError as GeminiAPIError

from app.config import get_settings
from app.providers.base import LLMProvider, ProviderError

settings = get_settings()


class GeminiProvider(LLMProvider):
    """
    Uses Google's current unified `google-genai` SDK (the old
    `google-generativeai` package is deprecated). System instructions are
    passed via GenerateContentConfig rather than stuffed into the prompt.
    """

    name = "gemini"

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ProviderError(
                "GEMINI_API_KEY is not set on the server. Add it to your .env file."
            )
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    async def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            )
            return response.text or ""
        except GeminiAPIError as exc:
            raise ProviderError(f"Gemini API error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - surface anything unexpected as ProviderError
            raise ProviderError(f"Gemini request failed: {exc}") from exc
