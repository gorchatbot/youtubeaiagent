"""
LLMs occasionally wrap JSON in markdown code fences or add a stray sentence
before/after it, even when explicitly told not to. This utility makes JSON
parsing robust to that instead of crashing the pipeline on a formatting slip.
"""

import json
import re


class LLMJSONParseError(Exception):
    pass


def parse_json_response(raw_text: str) -> dict:
    text = raw_text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # If there's still leading/trailing noise, grab the outermost { ... }
    if not text.startswith("{"):
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMJSONParseError(f"Could not parse model output as JSON: {exc}\nRaw: {raw_text[:300]}") from exc
