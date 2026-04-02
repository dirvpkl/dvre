"""
FastAPI server for DVRE.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from dvre.builder import OutputBuilder
from dvre.utils.config import BuildConfig
from dvre.utils.helper import get_resolve
from dvre.utils.types import ProjectManager as ResolveProjectManager

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    log.info("Starting DVRE server...")
    app.state.project_manager = get_resolve().GetProjectManager()
    app.state.build_lock = asyncio.Lock()

    yield

    log.info("Bye")


def create_router(app: FastAPI) -> APIRouter:
    """
    Create API router with timeline endpoints.

    Returns:
        APIRouter instance
    """
    router = APIRouter()

    ProjectManagerDep = Annotated[ResolveProjectManager, Depends(lambda: app.state.project_manager)]

    @router.post("/build", status_code=200)
    async def build(config: BuildConfig, project_manager: ProjectManagerDep) -> Response:
        """
        Create a timeline from JSON configuration.

        Accepts a JSON config with project settings, track layout,
        video clips, audio clips and export path. Creates the complete
        timeline in DaVinci Resolve and exports it to the target path.

        Args:
            config: BuildConfig from request body

        Returns:
            Response with status code
        """
        lock: asyncio.Lock = app.state.build_lock

        if lock.locked():
            raise HTTPException(status_code=409, detail="Build already in progress")

        async with lock:
            try:
                builder = OutputBuilder(project_manager)
                success = builder.build(config)

                if success:
                    return Response(status_code=200)

                return Response(status_code=500)

            except Exception as e:
                log.error(f"Error creating timeline: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    return router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="DVRE - DaVinci Resolve Video Editor",
        description="Server DVRE",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_router(app))

    return app

if __name__ == "__main__":
    app = create_app()
