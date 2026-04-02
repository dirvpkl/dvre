"""
Configuration models for DVRE timeline creation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VideoClip(BaseModel):

    path: str = Field(..., description="Absolute path to the video file")
    start_frame: int = Field(0, ge=0, description="Start frame in the source clip")
    end_frame: int | None = Field(None, ge=0, description="End frame in the source clip (optional)")


class TimelineSettings(BaseModel):

    frame_rate: int = Field(60, gt=0, description="Frame rate (fps)")


class BuildConfig(BaseModel):
    """Main configuration for final timeline creation."""

    project_name: str = Field(..., description="Name of the DaVinci Resolve project (UNIQUE)")
    timeline_name: str = Field(..., description="Name of the timeline to create")
    settings: TimelineSettings = Field(default_factory=TimelineSettings, description="Timeline settings")
    clips: list[VideoClip] = Field(default_factory=list, description="Clips to add")
    export_path: str = Field(..., description="Absolute path to the export video file")
