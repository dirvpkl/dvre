"""
FastAPI server for DVRE.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from dvre.builder import OutputBuilder
from dvre.utils.config import BuildConfig, BuildResponse, RenderJobStatus
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
async def build(
    request: Request, config: BuildConfig, project_manager=Depends(get_project_manager)
) -> BuildResponse:
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
            job_id = OutputBuilder(project_manager).build(config)
            return BuildResponse(job_id=job_id)
        except ResolveError as e:
            log.error(f"Resolve error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception:
            log.exception("Unexpected build failure")
            raise HTTPException(status_code=500, detail="Unexpected build failure")


@router.post("/project/close", status_code=204)
def close_project(project_manager=Depends(get_project_manager)) -> None:
    project = project_manager.GetCurrentProject()
    if project is None:
        raise HTTPException(status_code=404, detail="No active project")
    log.debug("Closing project via API")
    project_manager.CloseProject(project)
    log.debug("Project closed")


@router.get("/render-job/{job_id}/status")
def render_job_status(
    job_id: str, project_manager=Depends(get_project_manager)
) -> RenderJobStatus:
    project = project_manager.GetCurrentProject()
    if project is None:
        raise HTTPException(status_code=404, detail="No active project")
    raw = project.GetRenderJobStatus(job_id)
    return RenderJobStatus.model_validate(raw)


def create_app() -> FastAPI:
    app = FastAPI(
        title="DVRE - DaVinci Resolve Video Editor",
        description="Server DVRE",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def log_requests(request, call_next):
        req_body = await request.body()
        log.debug(f"→ {request.method} {request.url} body={req_body!r}")

        response = await call_next(request)

        res_body = b""
        async for chunk in response.body_iterator:
            res_body += chunk

        log.debug(f"← {response.status_code} {request.url} body={res_body!r}")

        return Response(
            content=res_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
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
