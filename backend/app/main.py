"""
App entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

This also mounts the static `frontend/` folder at "/" so opening
http://localhost:8000 in a browser serves the UI directly - no separate
frontend server needed for local dev. When you later deploy the backend
and frontend separately (e.g. backend on Render/Railway, frontend on
Vercel), just point the frontend's API_BASE_URL (see frontend/app.js) at
the deployed backend URL and tighten ALLOWED_ORIGINS below.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import generate

settings = get_settings()

app = FastAPI(
    title="YouTube Content Agent API",
    description="A multi-step AI agent that turns one video topic into a full, "
    "consistent content package: script, titles, description, tags, and a thumbnail concept.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "providers_configured": settings.available_providers,
    }


# Serve the frontend (static HTML/CSS/JS) at "/". Must be added AFTER the
# /api routes above so API requests are matched first.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
