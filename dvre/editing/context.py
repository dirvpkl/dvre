"""
Shared Resolve build context.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from dvre.utils.config import TimelineSettings
from dvre.utils.errors import ResolveError
from dvre.utils.types import MediaPool, Project, ProjectManager as ResolveProjectManager, Timeline

log = logging.getLogger(__name__)


@dataclass(slots=True)
class BuildContext:
    """Resolve objects used during a single build."""

    project_manager: ResolveProjectManager
    _project: Project | None = None
    _media_pool: MediaPool | None = None
    _timeline: Timeline | None = None

    @property
    def project(self) -> Project:
        if self._project is None:
            raise ResolveError("Project has not been created yet")
        return self._project

    @property
    def media_pool(self) -> MediaPool:
        if self._media_pool is None:
            raise ResolveError("Media pool is not available before project creation")
        return self._media_pool

    @property
    def timeline(self) -> Timeline:
        if self._timeline is None:
            raise ResolveError("Timeline has not been created yet")
        return self._timeline


class ContextFactory:
    """Creates and initializes BuildContext with Resolve objects."""

    def __init__(self, project_manager: ResolveProjectManager):
        self.project_manager = project_manager

    def create(self, project_name: str, timeline_name: str, settings: TimelineSettings) -> BuildContext:
        """Create a fully initialized BuildContext with project and timeline."""
        context = BuildContext(self.project_manager)

        self._create_project(context, project_name, settings)
        self._create_timeline(context, timeline_name)

        return context

    def _create_project(self, context: BuildContext, project_name: str, settings: TimelineSettings) -> None:
        log.info(f"Creating new project: {project_name}")
        project = self.project_manager.CreateProject(project_name, None)

        if not project:
            raise ResolveError(f"Failed to create project '{project_name}' (name may already exist)")

        project.SetSetting("timelineResolutionWidth", str(settings.width))
        project.SetSetting("timelineResolutionHeight", str(settings.height))
        project.SetSetting("timelineFrameRate", str(settings.frame_rate))

        context._project = project
        context._media_pool = project.GetMediaPool()
        log.info(f"Project created: {project_name}")

    @staticmethod
    def _create_timeline(context: BuildContext, timeline_name: str) -> None:
        log.info(f"Creating timeline: {timeline_name}")
        timeline = context.media_pool.CreateEmptyTimeline(timeline_name)

        if timeline is None:
            raise ResolveError(f"Failed to create timeline '{timeline_name}'")

        if not context.project.SetCurrentTimeline(timeline):
            raise ResolveError(f"Failed to set current timeline '{timeline_name}'")

        context._timeline = timeline
        log.info(f"Timeline '{timeline_name}' created successfully")
