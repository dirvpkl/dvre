"""
Builder - orchestrates services from config.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dvre.core.builder.utils.layers import (
    compound_layer,
    load_previous_compound,
    process_layer,
)
from dvre.core.builder.utils.runtime import BuildRuntime
from dvre.editing.context import ContextFactory
from dvre.editing.fusion import FusionService
from dvre.editing.media import MediaService
from dvre.editing.project import ProjectService
from dvre.editing.timeline import TimelineService
from dvre.schemas.api import BuildConfig
from dvre.utils.media import AudioValidator, VideoValidator
from dvre.utils.types import ProjectManager as ResolveProjectManager

log = logging.getLogger(__name__)


class OutputBuilder:
    """
    Orchestrates the complete timeline creation process and its export.
    """

    def __init__(self, project_manager: ResolveProjectManager):
        self.factory = ContextFactory(project_manager)

    def build(self, config: BuildConfig) -> str:
        log.info(
            f"Starting build: project='{config.project_name}' timeline='{config.timeline_name}'"
        )

        runtime = self._create_runtime(config)

        for layer in config.layers:
            load_previous_compound(runtime, layer.name)
            process_layer(runtime, layer)
            compound_layer(runtime, layer.name)

        return self._export(runtime, config)

    def _create_runtime(self, config: BuildConfig) -> BuildRuntime:
        context = self.factory.create(
            config.project_name, config.timeline_name, config.settings
        )

        return BuildRuntime(
            project_service=ProjectService(context),
            media_service=MediaService(context),
            timeline_service=TimelineService(context),
            fusion_service=FusionService(context),
            video_validator=VideoValidator(
                config.settings.width,
                config.settings.height,
                config.settings.frame_rate,
            ),
            audio_validator=AudioValidator(),
        )

    @staticmethod
    def _export(runtime: BuildRuntime, config: BuildConfig) -> str:
        if config.save_project:
            runtime.project_service.save_current_project()

        export_path = Path(config.export_path)
        task_id = runtime.project_service.export_project(
            str(export_path.parent),
            str(export_path.stem),
            config.settings.width,
            config.settings.height,
            config.settings.frame_rate,
        )

        log.info(f"Export started: {config.export_path} task_id={task_id}")

        return task_id
