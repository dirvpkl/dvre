"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.resolve_client import ResolveClient
from dvre.utils.config import TimelineSettings
from dvre.utils.types import Project, QuickExportRenderSettings

log = logging.getLogger(__name__)


class ProjectManager:
    """
    Manages project creation, saving, exporting and configuration in DaVinci Resolve.
    """

    def __init__(self, client: ResolveClient):
        """
        Initialize ProjectManager.

        Args:
            client: ResolveClient instance
        """
        self.client = client

    def create_project(self, project_name: str, settings: TimelineSettings) -> Project:
        """
        Create a new project.

        Args:
            project_name: name of the project
            settings: timeline settings for the project
        """

        log.info(f"Creating new project: {project_name}")
        project = self.client.project_manager.CreateProject(project_name, None)

        if not project:
            raise RuntimeError(f"Failed to create a project (check if project name already exists): {project_name}")

        try:
            project.SetSetting("timelineResolutionWidth", str(settings.width))
            project.SetSetting("timelineResolutionHeight", str(settings.height))
            project.SetSetting("timelineFrameRate", str(settings.frame_rate))

            log.info(f"Project created {project_name}")
            return project

        except Exception as e:
            raise RuntimeError(f"Error configuring project {project_name}: {e}")

    def save_project(self):
        """
        Saving a currently opened project.
        """

        log.info(f"Saving current project...")
        project = self.client.project_manager.SaveProject()
        try:

            if project:
                log.info(f"Current project saved")
                return

            raise RuntimeError(f"Failed to save current project: {project}")

        except Exception as e:
            raise RuntimeError(f"Error saving current project: {e}")

    def export_project(self, export_path: str, export_name: str):
        """
        Exports a currently opened project.

        Args:
            export_path: path to save the video
            export_name: name of the video to be saved
        """

        # ['H.264 Master', 'HyperDeck', 'H.265 Master', 'ProRes 422 HQ', 'YouTube', 'Vimeo', 'TikTok', 'Presentations', 'Dropbox', 'Replay']
        settings: QuickExportRenderSettings = {
            "TargetDir": export_path,
            "CustomName": export_name,
            "VideoQuality": "Best",
            "EnableUpload": False
        }
        self.client.project.RenderWithQuickExport("ProRes 422 HQ", settings)
