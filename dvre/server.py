"""
FastAPI server for DVRE.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from dvre.routers.project import router as project_router
from dvre.routers.tasks import router as tasks_router

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("Starting DVRE server...")
    app.state.build_lock = asyncio.Lock()

    yield

    log.info("Bye")


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
        log.debug(f"\u2192 {request.method} {request.url} body={req_body!r}")

        response = await call_next(request)

        res_body = b""
        async for chunk in response.body_iterator:
            res_body += chunk

        log.debug(f"\u2190 {response.status_code} {request.url} body={res_body!r}")

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

    app.include_router(project_router)
    app.include_router(tasks_router)

    return app


if __name__ == "__main__":
    app = create_app()


