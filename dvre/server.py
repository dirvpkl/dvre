"""
FastAPI server for DVRE.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from dvre.builder import OutputBuilder
from dvre.utils.config import BuildConfig
from dvre.utils.errors import ResolveError
from dvre.utils.helper import get_resolve
from dvre.utils.types import ProjectManager as ResolveProjectManager

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    log.info("Starting DVRE server...")
    app.state.build_lock = asyncio.Lock()

    yield

    log.info("Bye")


def get_project_manager(_: Request) -> ResolveProjectManager:
    # Resolve remote objects are not stable across long-lived server uptime,
    # so fetch a fresh ProjectManager for each request.
    return get_resolve().GetProjectManager()


router = APIRouter()

# async def because of lock, the actual build process is sync because of Resolve API
@router.post("/build", status_code=200)
async def build(request: Request, config: BuildConfig, project_manager = Depends(get_project_manager)) -> Response:
    """
    Create a timeline from JSON configuration.

    Accepts a JSON config with project settings, track layout,
    video clips, audio clips and export path. Creates the complete
    timeline in DaVinci Resolve and exports it to the target path.
    """
    lock: asyncio.Lock = request.app.state.build_lock

    if lock.locked():
        raise HTTPException(status_code=409, detail="Build already in progress")

    async with lock:
        try:
            OutputBuilder(project_manager).build(config)
            return Response(status_code=200)
        except ResolveError as e:
            log.error(f"Resolve error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception:
            log.exception("Unexpected build failure")
            raise HTTPException(status_code=500, detail="Unexpected build failure")

def create_app() -> FastAPI:
    app = FastAPI(
        title="DVRE - DaVinci Resolve Video Editor",
        description="Server DVRE",
        version="0.1.0",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app

if __name__ == "__main__":
    app = create_app()
