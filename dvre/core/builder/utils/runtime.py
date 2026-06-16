from __future__ import annotations

from dataclasses import dataclass

from dvre.editing.fusion import FusionService
from dvre.editing.media import MediaService
from dvre.editing.project import ProjectService
from dvre.editing.timeline import TimelineService
from dvre.utils.media import AudioValidator, VideoValidator
from dvre.utils.types import MediaPoolItem, TimelineItem


@dataclass
class BuildRuntime:
    project_service: ProjectService
    media_service: MediaService
    timeline_service: TimelineService
    fusion_service: FusionService
    video_validator: VideoValidator
    audio_validator: AudioValidator
    prev_compound: TimelineItem | None = None
    compound_mpi: MediaPoolItem | None = None
    compound_start: int | None = None
    compound_end: int | None = None
