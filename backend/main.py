"""Audiobook Studio backend entry point.

Run in development:
    uvicorn backend.main:app --reload --port 7860
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import routes_books, routes_generate, routes_roles, routes_voices

BACKEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = BACKEND_DIR.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Audiobook Studio", version="0.1.0")

    # CORS for local Vite dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_books.router, prefix="/api/books", tags=["books"])
    app.include_router(routes_roles.router, prefix="/api/roles", tags=["roles"])
    app.include_router(routes_voices.router, prefix="/api/voices", tags=["voices"])
    app.include_router(routes_generate.router, prefix="/api/generate", tags=["generate"])

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    # Serve SPA in production (after Vite build)
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()
