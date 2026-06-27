import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from dvre.core.dependencies import get_project_manager
from dvre.schemas.api import OkResponse, TaskStatusResponse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# original `job_id` from docs davinci resolve now called `task_id` (celery compatible)
@router.get("/{task_id}")
def get_task_status(
    task_id: str, project_manager=Depends(get_project_manager)
) -> TaskStatusResponse:
    project = project_manager.GetCurrentProject()
    if project is None:
        raise HTTPException(status_code=404, detail="No active project")
    raw = project.GetRenderJobStatus(task_id)
    job_status = raw["JobStatus"]
    # celery-like status
    status = (
        "PENDING"
        if job_status == "Rendering"
        else "SUCCESS"
        if job_status == "Complete"
        else "FAILURE"
    )
    return TaskStatusResponse(
        task_id=task_id,
        task_name="dvre.render.status",
        status=status,
        result=OkResponse(ok=True) if status == "SUCCESS" else None,
        error=raw.get("Error", ""),
    )
