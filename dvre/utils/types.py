"""Common types for DVRE."""
from __future__ import annotations

from typing import TYPE_CHECKING

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
        QuickExportRenderSettings
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
    QuickExportRenderSettings = object
