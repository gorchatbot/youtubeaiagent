import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent.pipeline import run_pipeline
from app.config import get_settings
from app.providers.base import ProviderError
from app.providers.factory import get_provider
from app.schemas import GenerateRequest

router = APIRouter(prefix="/api", tags=["generate"])
settings = get_settings()


def _sse_format(event: dict) -> str:
    """Encode one event as a Server-Sent Events `data:` line."""
    return f"data: {json.dumps(event)}\n\n"


@router.get("/providers")
async def list_providers():
    """Tells the frontend which providers actually have a key configured server-side,
    so the UI can disable/hide options that won't work instead of failing after submit."""
    return {"available": settings.available_providers}


@router.post("/generate")
async def generate(req: GenerateRequest):
    """
    Streams the agent pipeline's progress as Server-Sent Events.
    Event stream shape (one JSON object per `data:` line):
      {"type": "step_start", "step": "...", "label": "..."}
      {"type": "step_done",  "step": "...", "data": {...}}
      {"type": "error",      "message": "..."}
      {"type": "complete",   "data": {full content package}}
    """

    async def event_stream():
        try:
            provider = get_provider(req.provider.value)
        except ProviderError as exc:
            yield _sse_format({"type": "error", "message": str(exc)})
            return

        async for event in run_pipeline(req, provider):
            yield _sse_format(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering so chunks flush immediately
        },
    )
