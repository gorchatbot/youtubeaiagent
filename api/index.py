"""
Entry point Vercel's Python runtime looks for when you deploy this repo.
Not used for local development (use `uvicorn app.main:app --reload` inside
backend/ for that) - this only matters once you deploy.

It just adds backend/ to the import path and re-exports the FastAPI app.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
