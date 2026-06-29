"""
The pipeline IS the agent: it decides the sequence of steps, and explicitly
feeds each step's real output forward as context into the next step's
prompt. That context-passing is what separates this from five independent,
disconnected prompts - the title generator is reading the actual script,
not just the raw topic; the tag generator is reading the actual title and
description, not guessing blind.

Implemented as an async generator so the API layer can stream step-by-step
progress events to the frontend (SSE) instead of the user staring at a
blank spinner for 20-30 seconds.
"""

from collections.abc import AsyncGenerator
from typing import Any

from app.agent.json_utils import LLMJSONParseError, parse_json_response
from app.agent.prompts import (
    DESCRIPTION_SYSTEM_PROMPT,
    SCRIPT_SYSTEM_PROMPT,
    TAGS_SYSTEM_PROMPT,
    THUMBNAIL_SYSTEM_PROMPT,
    TITLES_SYSTEM_PROMPT,
    description_prompt,
    script_prompt,
    tags_prompt,
    thumbnail_prompt,
    titles_prompt,
)
from app.providers.base import LLMProvider, ProviderError
from app.schemas import GenerateRequest

STEP_ORDER = ["script", "titles", "description", "tags", "thumbnail"]

STEP_LABELS = {
    "script": "Writing the script",
    "titles": "Generating title options from the script",
    "description": "Writing an SEO description from the script + title",
    "tags": "Extracting tags from the script + description",
    "thumbnail": "Designing a thumbnail concept from the title",
}


async def run_pipeline(req: GenerateRequest, provider: LLMProvider) -> AsyncGenerator[dict[str, Any], None]:
    """
    Yields one event per pipeline step:
      {"type": "step_start", "step": "script", "label": "..."}
      {"type": "step_done",  "step": "script", "data": {...}}
      {"type": "error",      "step": "titles", "message": "..."}
      {"type": "complete",   "data": {full ContentPackage dict}}
    """
    result: dict[str, Any] = {}

    try:
        # --- Step 1: Script ---
        yield {"type": "step_start", "step": "script", "label": STEP_LABELS["script"]}
        script = await provider.complete(
            SCRIPT_SYSTEM_PROMPT,
            script_prompt(req.topic, req.niche, req.audience, req.tone, req.length.value, req.language),
            temperature=0.8,
        )
        result["script"] = script.strip()
        yield {"type": "step_done", "step": "script", "data": {"script": result["script"]}}

        # --- Step 2: Titles (context: script) ---
        yield {"type": "step_start", "step": "titles", "label": STEP_LABELS["titles"]}
        titles_raw = await provider.complete(
            TITLES_SYSTEM_PROMPT,
            titles_prompt(req.topic, result["script"], req.niche),
            temperature=0.9,
        )
        titles_json = parse_json_response(titles_raw)
        result["titles"] = titles_json.get("titles", [])
        yield {"type": "step_done", "step": "titles", "data": {"titles": result["titles"]}}

        chosen_title = result["titles"][0] if result["titles"] else req.topic

        # --- Step 3: Description (context: script + chosen title) ---
        yield {"type": "step_start", "step": "description", "label": STEP_LABELS["description"]}
        description_raw = await provider.complete(
            DESCRIPTION_SYSTEM_PROMPT,
            description_prompt(req.topic, result["script"], chosen_title, req.niche),
            temperature=0.7,
        )
        description_json = parse_json_response(description_raw)
        result["description"] = description_json.get("description", "")
        yield {"type": "step_done", "step": "description", "data": {"description": result["description"]}}

        # --- Step 4: Tags (context: script + title + description) ---
        yield {"type": "step_start", "step": "tags", "label": STEP_LABELS["tags"]}
        tags_raw = await provider.complete(
            TAGS_SYSTEM_PROMPT,
            tags_prompt(req.topic, result["script"], chosen_title, result["description"]),
            temperature=0.6,
        )
        tags_json = parse_json_response(tags_raw)
        result["tags"] = tags_json.get("tags", [])
        yield {"type": "step_done", "step": "tags", "data": {"tags": result["tags"]}}

        # --- Step 5: Thumbnail concept (context: title + tone/niche) ---
        yield {"type": "step_start", "step": "thumbnail", "label": STEP_LABELS["thumbnail"]}
        thumbnail_raw = await provider.complete(
            THUMBNAIL_SYSTEM_PROMPT,
            thumbnail_prompt(chosen_title, req.tone, req.niche),
            temperature=0.8,
        )
        thumbnail_json = parse_json_response(thumbnail_raw)
        result["thumbnail_concept"] = thumbnail_json.get("thumbnail_concept", "")
        result["thumbnail_text"] = thumbnail_json.get("thumbnail_text", "")
        yield {
            "type": "step_done",
            "step": "thumbnail",
            "data": {
                "thumbnail_concept": result["thumbnail_concept"],
                "thumbnail_text": result["thumbnail_text"],
            },
        }

        yield {"type": "complete", "data": result}

    except ProviderError as exc:
        yield {"type": "error", "message": str(exc)}
    except LLMJSONParseError as exc:
        yield {"type": "error", "message": f"The model returned malformed output: {exc}"}
    except Exception as exc:  # noqa: BLE001 - last-resort guard so the stream always ends cleanly
        yield {"type": "error", "message": f"Unexpected error: {exc}"}
