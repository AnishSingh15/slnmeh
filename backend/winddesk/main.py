"""ASGI application factory.

Run (from backend/):  uv run uvicorn --factory winddesk.main:create_app --reload
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from winddesk.api.routes import router
from winddesk.config import Settings
from winddesk.repository import load_snapshot
from winddesk.service import WindDeskService

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, service: WindDeskService | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    if service is None:
        service = WindDeskService(load_snapshot(settings.data_dir))
        log.info("Loaded snapshot fetched at %s", service.health().data_fetched_at)

    app = FastAPI(
        title="WindDesk API",
        version="1.0.0",
        description="Day-ahead wind forecast intelligence for GB electricity trading.",
    )
    app.state.service = service
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.include_router(router)
    if settings.static_dir is not None:
        _serve_frontend(app, settings.static_dir)
    return app


def _serve_frontend(app: FastAPI, static_dir: Path) -> None:
    """Serve the built SPA; unknown non-API paths fall back to index.html."""
    root = static_dir.resolve()
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(root / "index.html")
