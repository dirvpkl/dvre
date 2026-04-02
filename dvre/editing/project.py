"""
Project management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.context import BuildContext
from dvre.utils.types import QuickExportRenderSettings

log = logging.getLogger(__name__)


class ProjectService:
    """
    Manages project persistence and export in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        """
        Initialize ProjectService.

        Args:
            context: active build context
        """
        self.context = context

    def save_project(self):
        """
        Saving a currently opened project.
        """

        log.info(f"Saving current project...")
        is_saved = self.context.project_manager.SaveProject()
        try:

            if is_saved:
                log.info(f"Current project saved")
                return

            raise RuntimeError(f"Failed to save current project: {is_saved}")

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
        self.context.project.RenderWithQuickExport("ProRes 422 HQ", settings)
