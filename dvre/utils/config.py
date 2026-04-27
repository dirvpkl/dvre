"""
Configuration models for DVRE timeline creation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TimelineSettings(BaseModel):
    """Timeline resolution and format settings."""

    width: int = Field(1920, gt=0, description="Timeline width in pixels")
    height: int = Field(1080, gt=0, description="Timeline height in pixels")
    frame_rate: float = Field(60, gt=0, description="Frame rate (fps)")


class _BaseClip(BaseModel):
    """Common clip placement settings."""

    path: str = Field(..., description="Absolute path to the video file")
    track: int = Field(
        1, ge=1, description="Target track number in the timeline (1-based)"
    )
    timeline_start: int = Field(
        ..., ge=0, description="Frame on the timeline where the clip starts"
    )
    start_frame: int = Field(..., ge=0, description="Start frame in the source clip")
    end_frame: int = Field(..., ge=0, description="End frame in the source clip")


class VideoClip(_BaseClip):
    """Video clip placement configuration."""


class AudioClip(_BaseClip):
    """Audio clip placement configuration."""


class BaseLayer(BaseModel):
    """A compound clip layer containing media clips."""

    name: str = Field(..., description="Name of the compound clip")
    video_clips: list[VideoClip] = Field(
        default_factory=list, description="Video clips to place on the timeline, in placement order"
    )
    audio_clips: list[AudioClip] = Field(
        default_factory=list, description="Audio clips to place on the timeline"
    )


class FusionClip(BaseModel):
    """A segment of the previous compound clip on which a Fusion composition is applied."""

    start_frame: int = Field(..., ge=0, description="Start frame within the source compound")
    end_frame: int = Field(..., ge=0, description="End frame within the source compound")
    comp_path: str = Field(
        ..., description="Absolute path to a .comp file to import into the Fusion clip"
    )


class FusionLayer(BaseModel):
    """A compound clip layer that slices the previous compound and applies Fusion compositions."""

    name: str = Field(..., description="Name of the compound clip")
    fusion_clips: list[FusionClip] = Field(
        ..., min_length=1,
        description="Segments of the previous compound clip on which Fusion compositions are applied. Order matters."
    )

class BuildResponse(BaseModel):
    """Response from the build endpoint."""

    job_id: str


class RenderJobStatus(BaseModel):
    """Status of a DaVinci Resolve render job."""

    model_config = ConfigDict(populate_by_name=True)

    job_status: str = Field(validation_alias="JobStatus")
    completion_percentage: int = Field(validation_alias="CompletionPercentage")
    estimated_time_remaining_ms: int | None = Field(None, validation_alias="EstimatedTimeRemainingInMs")
    time_taken_to_render_ms: int | None = Field(None, validation_alias="TimeTakenToRenderInMs")
    error: str | None = Field(None, validation_alias="Error")


class BuildConfig(BaseModel):
    """Main configuration for final timeline creation."""

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
