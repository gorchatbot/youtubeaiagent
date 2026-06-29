"""
Centralized configuration.

All secrets / provider keys live in environment variables (.env locally,
Vercel/host env vars in production). The UI only ever sends a provider
*name* ("openai" | "gemini" | "groq") — never a key. The backend looks up
the matching key from its own environment. This keeps API keys off the
network entirely (browser -> server -> provider, never browser -> provider).
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()  # no-op in production if no .env file is present


class Settings:
    # --- OpenAI ---
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- Google Gemini ---
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Groq (OpenAI-compatible endpoint, free-tier friendly) ---
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # --- App ---
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    # Which providers are actually usable right now (key present in env)
    @property
    def available_providers(self) -> list[str]:
        available = []
        if self.OPENAI_API_KEY:
            available.append("openai")
        if self.GEMINI_API_KEY:
            available.append("gemini")
        if self.GROQ_API_KEY:
            available.append("groq")
        return available


@lru_cache
def get_settings() -> Settings:
    return Settings()
