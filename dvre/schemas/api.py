"""API request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from dvre.schemas.layers import BaseLayer, FusionLayer


class TimelineSettings(BaseModel):
    """Timeline resolution and format settings."""

    width: int = Field(1920, gt=0, description="Timeline width in pixels")
    height: int = Field(1080, gt=0, description="Timeline height in pixels")
    frame_rate: float = Field(60, gt=0, description="Frame rate (fps)")
    super_scale: Literal[0, 1, 2, 3, 4] | None = Field(
        None,
        description=(
            "DaVinci Resolve SuperScale project setting. "
            "0=Auto, 1=No scaling, 2=2x, 3=3x, 4=4x. "
            "Applied once on project creation via Project:SetSetting('superScale', x). "
            "2x Enhanced is not yet exposed."
        ),
    )


class BuildConfig(BaseModel):
    """Main configuration for timeline creation."""

    project_name: str = Field(
        ..., description="Name of the DaVinci Resolve project (must be unique)"
    )
    timeline_name: str = Field(..., description="Name of the timeline to create")
    settings: TimelineSettings = Field(
        default_factory=TimelineSettings, description="Timeline settings"
    )
    layers: list[BaseLayer | FusionLayer] = Field(
        default_factory=list, description="Layers to build, processed in order"
    )
    export_path: str = Field(..., description="Absolute path to the export video file")
    save_project: bool = Field(
        True, description="Whether to save the project in DaVinci library"
    )


class OkResponse(BaseModel):
    """Generic OK response."""

    ok: bool


class TaskQueuedResponse(BaseModel):
    """Response when a task is queued."""

    ok: bool
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Status of a task."""

    task_id: str
    task_name: str
    status: str
    result: Any
    error: str
