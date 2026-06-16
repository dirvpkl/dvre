import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from dvre.core.builder.builder import OutputBuilder
from dvre.core.dependencies import get_project_manager
from dvre.schemas.api import BuildConfig, BuildResponse
from dvre.utils.errors import ResolveError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/build", tags=["build"])


@router.post("", status_code=200,
             description="Creates and initializes a project, builds and manages the timeline, validates and processes media assets, then saves and exports the final output.\n"
                         "Due to DaVinci Resolve\u2019s lack of reliable multithreading/async support in this context, the entire pipeline is executed sequentially in a single thread.")
async def build(
    request: Request, config: BuildConfig, project_manager=Depends(get_project_manager)
) -> BuildResponse:
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
