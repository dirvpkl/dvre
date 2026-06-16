import logging

from fastapi import APIRouter, Depends, HTTPException

from dvre.core.dependencies import get_project_manager
from dvre.schemas.api import RenderJobStatus

log = logging.getLogger(__name__)

router = APIRouter(prefix="/render-job", tags=["render"])


@router.get("/{job_id}/status")
def render_job_status(
    job_id: str, project_manager=Depends(get_project_manager)
) -> RenderJobStatus:
    project = project_manager.GetCurrentProject()
    if project is None:
        raise HTTPException(status_code=404, detail="No active project")
    raw = project.GetRenderJobStatus(job_id)
    return RenderJobStatus.model_validate(raw)
