"""Common types for DVRE."""
from __future__ import annotations

from typing import Literal, TYPE_CHECKING

MediaType = Literal[1, 2]
VIDEO_ONLY: MediaType = 1
AUDIO_ONLY: MediaType = 2

if TYPE_CHECKING:
    from fusionscript import (
        MediaPool,
        MediaPoolClipInfo,
        MediaPoolItem,
        Project,
        ProjectManager,
        Resolve,
        Timeline,
        TimelineClipInfo,
        TimelineItem,
        RenderSettings
    )
else:
    MediaPool = object
    MediaPoolClipInfo = object
    MediaPoolItem = object
    Project = object
    ProjectManager = object
    Resolve = object
    Timeline = object
    TimelineClipInfo = object
    TimelineItem = object
    RenderSettings = object
