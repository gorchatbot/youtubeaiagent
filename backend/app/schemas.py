"""
Request/response contracts for the API. Keeping these as explicit Pydantic
models (rather than raw dicts) gives us automatic validation, auto-generated
OpenAPI docs at /docs, and a single source of truth for the frontend to
mirror.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Provider(str, Enum):
    openai = "openai"
    gemini = "gemini"
    groq = "groq"


class VideoLength(str, Enum):
    shorts = "shorts"          # < 60s
    short_form = "short_form"  # 1-3 min
    medium = "medium"          # 5-10 min
    long_form = "long_form"    # 10-20+ min


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300, description="The core video idea/topic")
    provider: Provider = Field(..., description="Which LLM provider to use for this request")

    niche: str | None = Field(None, max_length=80, description="e.g. tech, finance, fitness, education")
    audience: str | None = Field(None, max_length=120, description="e.g. beginners, working professionals")
    tone: str | None = Field(None, max_length=60, description="e.g. casual, professional, energetic")
    length: VideoLength = Field(VideoLength.medium, description="Target video length bucket")
    language: str = Field("English", max_length=40)

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "5 mistakes beginners make when learning Python",
                "provider": "groq",
                "niche": "programming education",
                "audience": "complete beginners",
                "tone": "casual and encouraging",
                "length": "medium",
                "language": "English",
            }
        }


class ContentPackage(BaseModel):
    script: str
    titles: list[str]
    description: str
    tags: list[str]
    thumbnail_concept: str
    thumbnail_text: str
