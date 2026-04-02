"""
FastAPI server for DVRE.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dvre.builder import OutputBuilder
from dvre.utils.config import BuildConfig
from dvre.editing.resolve_client import ResolveClient

log = logging.getLogger(__name__)

_resolve_client: ResolveClient

class BuildResponse(BaseModel):
    """Timeline build response."""
    success: bool


def create_router() -> APIRouter:
    """
    Create API router with timeline endpoints.
    
    Returns:
        APIRouter instance
    """
    router = APIRouter()

    @router.post("/build", response_model=BuildResponse)
    async def build(config: BuildConfig) -> BuildResponse:
        """
        Create a timeline from JSON configuration.

        Accepts a JSON config with project settings, track layout,
        video clips, audio clips and export path. Creates the complete
        timeline in DaVinci Resolve and exports it to the target path.

        Args:
            config: BuildConfig from request body
            
        Returns:
            BuildResponse with result
        """

        try:
            builder = OutputBuilder(_resolve_client)
            success = builder.build(config)
            
            return BuildResponse(success=success)
                
        except Exception as e:
            log.error(f"Error creating timeline: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global _resolve_client
    
    log.info("Starting DVRE server...")
    _resolve_client = ResolveClient()
    
    yield
    
    log.info("Bye")


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
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include router
    app.include_router(create_router())

    return app

if __name__ == "__main__":
    app = create_app()
