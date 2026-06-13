"""Clip placement models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class _BaseClip(BaseModel):
    """Common clip placement settings."""

    path: str = Field(..., description="Absolute path to the video file")
    track: int = Field(
        1, ge=1, description="Target track number in the timeline (1-based)"
    )
    timeline_start_frame: int = Field(
        ..., ge=0, description="Frame on the timeline where the clip starts"
    )
    start_frame: int = Field(..., ge=0, description="Start frame in the source clip")
    end_frame: int = Field(..., ge=0, description="End frame in the source clip")


class VideoClip(_BaseClip):
    """Video clip placement configuration."""


class AudioClip(_BaseClip):
    """Audio clip placement configuration."""


class FusionClip(BaseModel):
    """A segment of the previous compound clip on which a Fusion composition is applied."""

    start_frame: int = Field(..., ge=0, description="Start frame within the source compound")
    end_frame: int = Field(..., ge=0, description="End frame within the source compound")
    comp_path: str = Field(
        ..., description="Absolute path to a .comp file to import into the Fusion clip"
    )
