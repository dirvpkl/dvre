"""
Configuration models for DVRE timeline creation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BaseClip(BaseModel):
    """Common clip placement settings."""

    path: str = Field(..., description="Absolute path to the video file")
    track: int = Field(1, ge=1, description="Target track number in the timeline (1-based)")
    timeline_start: int = Field(0, ge=0, description="Frame on the timeline where the clip starts")
    start_frame: int = Field(0, ge=0, description="Start frame in the source clip")
    end_frame: int = Field(0, ge=0, description="End frame in the source clip")


class VideoClip(BaseClip):
    """Video clip placement configuration."""


class AudioClip(BaseClip):
    """Audio clip placement configuration."""


class TimelineSettings(BaseModel):

    frame_rate: int = Field(60, gt=0, description="Frame rate (fps)")


class BuildConfig(BaseModel):
    """Main configuration for final timeline creation."""

    project_name: str = Field(..., description="Name of the DaVinci Resolve project (UNIQUE)")
    timeline_name: str = Field(..., description="Name of the timeline to create")
    settings: TimelineSettings = Field(default_factory=TimelineSettings, description="Timeline settings")
    video_clips: list[VideoClip] = Field(default_factory=list, description="Video clips to add")
    audio_clips: list[AudioClip] = Field(default_factory=list, description="Audio clips to add")
    export_path: str = Field(..., description="Absolute path to the export video file")
