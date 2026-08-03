import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from dvre.core.dependencies import get_project_manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/project", tags=["project"])


@router.post("/close", status_code=204)
def close_project(
    request: Request, project_manager=Depends(get_project_manager)
) -> None:
    lock: asyncio.Lock = request.app.state.build_lock

    if lock.locked():
        raise HTTPException(
            status_code=403, detail="Project is currently building. Try again later."
        )

    project = project_manager.GetCurrentProject()
    if project is None:
        raise HTTPException(status_code=404, detail="No active project")
    log.debug("Closing project via API")
    project_manager.CloseProject(project)
    log.debug("Project closed")
