"""
webapp.py
Web layer for Codebase Autopsy. Serves the dashboard UI and a JSON API
that wraps the existing pipeline (ingest -> graph -> Bob analysis).

Run locally:
    uvicorn autopsy.webapp:app --reload --port 8000

Deploy: see DEPLOY.md at the repo root.

Security notes (public-facing deployment):
  - Only github.com / gitlab.com / bitbucket.org URLs can be cloned
    (autopsy/source.py ALLOWED_HOSTS) — not an open clone proxy.
  - `mock` defaults to True for POST /api/analyze. Real Bob calls cost
    Bobcoins from a shared, limited budget — real=True should stay
    something *you* trigger deliberately, not the default for random
    visitors hitting a public link.
  - DEFAULT_MAX_MODULES caps how many Bob calls one request can trigger.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from autopsy.main import run_autopsy
from autopsy.source import SourceError, resolve_repo

app = FastAPI(title="Codebase Autopsy")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
DEFAULT_MAX_MODULES = 25


class AnalyzeRequest(BaseModel):
    repo: str = Field(..., description="Local path or a github.com/gitlab.com/bitbucket.org URL")
    mock: bool = True
    max_modules: int = Field(default=DEFAULT_MAX_MODULES, ge=1, le=100)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not req.mock and not os.environ.get("BOB_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="Server has no BOB_API_KEY configured — only mock=true requests are available.",
        )

    try:
        with resolve_repo(req.repo) as local_path:
            report = run_autopsy(local_path, mock=req.mock, max_modules=req.max_modules)
    except SourceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 — surface a clean error to the client
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    return JSONResponse(report)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "bob_configured": bool(os.environ.get("BOB_API_KEY")),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
