"""
Project management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.context import BuildContext
from dvre.utils.errors import ResolveError
from dvre.utils.types import QuickExportRenderSettings

log = logging.getLogger(__name__)


class ProjectService:
    """
    Manages project persistence and export in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def save_project(self) -> None:
        log.info("Saving current project...")

        if not self.context.project_manager.SaveProject():
            raise ResolveError("Failed to save current project")

        log.info("Project saved")

    def export_project(self, export_path: str, export_name: str) -> None:
        # ['H.264 Master', 'HyperDeck', 'H.265 Master', 'ProRes 422 HQ', 'YouTube', 'Vimeo', 'TikTok', 'Presentations', 'Dropbox', 'Replay']
        settings: QuickExportRenderSettings = {
            "TargetDir": export_path,
            "CustomName": export_name,
            "VideoQuality": "Best",
            "EnableUpload": False
        }
        self.context.project.RenderWithQuickExport("ProRes 422 HQ", settings)
