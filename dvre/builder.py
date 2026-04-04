"""
Builder - orchestrates services from config.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dvre.editing.context import ContextFactory
from dvre.editing.media import MediaService
from dvre.editing.project import ProjectService
from dvre.editing.timeline import TimelineService
from dvre.utils.config import BuildConfig
from dvre.utils.types import ProjectManager as ResolveProjectManager

log = logging.getLogger(__name__)


class OutputBuilder:
    """
    Orchestrates the complete timeline creation process and its export.
    """

    def __init__(self, project_manager: ResolveProjectManager):
        self.factory = ContextFactory(project_manager)

    # TODO: All the clips MUST BE 1920x1080! The timeline supports only 1920x1080
    # TODO: Moreover you better to make background from that clips and upscale and blur to make it as background image
    # TODO: So if the videos 4:3 and vertically fits fully - adjust the size by 1.777 in zoom to perfectly fit this
    # TODO: You can make even 2 because blur must be enabled.
    def build(self, config: BuildConfig) -> None:
        log.info(f"Starting build: project='{config.project_name}' timeline='{config.timeline_name}'")

        context = self.factory.create(config.project_name, config.timeline_name, config.settings)

        project_service = ProjectService(context)
        media_service = MediaService(context)
        timeline_service = TimelineService(context)

        if config.video_clips:
            timeline_service.ensure_track_count("video", max(clip.track for clip in config.video_clips))

        if config.audio_clips:
            timeline_service.ensure_track_count("audio", max(clip.track for clip in config.audio_clips))

        for clip in config.video_clips:
            media_service.place_video_clip(clip)
        log.info(f"Placed {len(config.video_clips)} video clips")

        for clip in config.audio_clips:
            media_service.place_audio_clip(clip)
        log.info(f"Placed {len(config.audio_clips)} audio clips")

        project_service.save_project()

        export_path = Path(config.export_path)
        project_service.export_project(str(export_path.parent), str(export_path.stem))

        log.info(f"Export complete: {config.export_path}")
