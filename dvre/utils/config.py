"""
Configuration models for DVRE timeline creation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BaseClip(BaseModel):
    """Common clip placement settings."""

    id: str | None = Field(
        None,
        description="Optional identifier for referencing this clip in fusion_clips",
    )
    path: str = Field(..., description="Absolute path to the video file")
    track: int = Field(
        1, ge=1, description="Target track number in the timeline (1-based)"
    )
    timeline_start: int = Field(
        ..., ge=0, description="Frame on the timeline where the clip starts"
    )
    start_frame: int = Field(..., ge=0, description="Start frame in the source clip")
    end_frame: int = Field(..., ge=0, description="End frame in the source clip")


class VideoClip(BaseClip):
    """Video clip placement configuration."""


class AudioClip(BaseClip):
    """Audio clip placement configuration."""


class TimelineSettings(BaseModel):
    """Timeline resolution and format settings."""

    width: int = Field(1920, gt=0, description="Timeline width in pixels")
    height: int = Field(1080, gt=0, description="Timeline height in pixels")
    frame_rate: float = Field(60, gt=0, description="Frame rate (fps)")


# TODO: This is not `Clip`, this is some kinda `Spec` or something
class FusionClip(BaseModel):
    """Group of clip IDs to merge into a single Fusion clip with an optional Fusion composition."""

    clip_ids: list[str] = Field(
        ...,
        min_length=2,
        description="IDs of clips to combine into a Fusion clip (min 2)",
    )
    comp_path: str | None = Field(
        None, description="Absolute path to a .comp file to import into the Fusion clip"
    )


class BuildResponse(BaseModel):
    """Response from the build endpoint."""

    job_id: str


class RenderJobStatus(BaseModel):
    """Status of a DaVinci Resolve render job."""

    model_config = ConfigDict(populate_by_name=True)

    job_status: str = Field(alias="JobStatus")
    completion_percentage: int = Field(alias="CompletionPercentage")
    estimated_time_remaining_ms: int | None = Field(None, alias="EstimatedTimeRemainingInMs")
    time_taken_to_render_ms: int | None = Field(None, alias="TimeTakenToRenderInMs")
    error: str | None = Field(None, alias="Error")


class BuildConfig(BaseModel):
    """Main configuration for final timeline creation."""

    project_name: str = Field(
        ..., description="Name of the DaVinci Resolve project (must be unique)"
    )
    timeline_name: str = Field(..., description="Name of the timeline to create")
    settings: TimelineSettings = Field(
        default_factory=TimelineSettings, description="Timeline settings"
    )
    video_clips: list[VideoClip] = Field(
        default_factory=list, description="Video clips to add"
    )
    audio_clips: list[AudioClip] = Field(
        default_factory=list, description="Audio clips to add"
    )
    fusion_clips: list[FusionClip] = Field(
        default_factory=list, description="Groups of clips to merge into Fusion clips"
    )
    export_path: str = Field(..., description="Absolute path to the export video file")
    save_project: bool = Field(
        True, description="Whether to save the project in DaVinci library"
    )
