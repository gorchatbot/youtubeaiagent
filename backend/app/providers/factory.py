from app.providers.base import LLMProvider, ProviderError
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider

_PROVIDER_MAP = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_provider(name: str) -> LLMProvider:
    """
    Single point of control: given the provider name selected in the UI,
    instantiate the matching provider class. Instantiation itself raises
    ProviderError immediately if that provider's API key isn't configured
    on the server — so we fail fast, before running any pipeline steps.
    """
    provider_cls = _PROVIDER_MAP.get(name)
    if provider_cls is None:
        raise ProviderError(f"Unknown provider '{name}'. Valid options: {list(_PROVIDER_MAP)}")
    return provider_cls()
