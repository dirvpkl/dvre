"""Layer models for timeline composition."""

from __future__ import annotations

from pydantic import BaseModel, Field

from dvre.schemas.clips import AudioClip, FusionSegment, VideoClip


class BaseLayer(BaseModel):
    """A compound clip layer containing media clips."""

    name: str = Field(..., description="Name of the compound clip")
    video_clips: list[VideoClip] = Field(
        default_factory=list,
        description="Video clips to place on the timeline, in placement order",
    )
    audio_clips: list[AudioClip] = Field(
        default_factory=list, description="Audio clips to place on the timeline"
    )


class FusionLayer(BaseModel):
    """A compound clip layer that slices the previous compound and applies Fusion compositions."""

    name: str = Field(..., description="Name of the compound clip")
    fusion_segments: list[FusionSegment] = Field(
        ...,
        min_length=1,
        description="Segments of the previous compound clip on which Fusion compositions are applied. Order matters.",
    )
