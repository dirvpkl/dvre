"""
Builder - orchestrates managers from config.
"""

from __future__ import annotations

import logging

from dvre.utils.config import BuildConfig

from dvre.editing.media import MediaManager
from dvre.editing.project import ProjectManager
from dvre.editing.timeline import TimelineManager
from dvre.editing.resolve_client import ResolveClient

from pathlib import Path

log = logging.getLogger(__name__)


class OutputBuilder:
    """
    Orchestrates the complete timeline creation process and its export.
    """
    
    def __init__(self, client: ResolveClient):
        """
        Initialize OutputBuilder.
        
        Args:
            client: ResolveClient instance
        """
        self.timeline_manager = TimelineManager(client)
        self.project_manager = ProjectManager(client)
        self.client = client
        self.media_manager = MediaManager(client)

    # TODO: All the clips MUST BE 1920x1080! The timeline supports only 1920x1080
    # TODO: Moreover you better to make background from that clips and upscale and blur to make it as background image
    # TODO: So if the videos 4:3 and vertically fits fully - adjust the size by 1.777 in zoom to perfectly fit this
    # TODO: You can make even 2 because blur must be enabled.
    def build(self, config: BuildConfig) -> bool:
        """
        Build a complete timeline and export it from configuration.
        
        Args:
            config: BuildConfig object
            
        Returns:
            True if successful
        """
        try:
            log.info(f"got config: {config}")
            log.info(f"Starting timeline build: {config.timeline_name}")
            
            self.project_manager.create_project(config.project_name, config.settings.frame_rate)

            self.timeline_manager.create_timeline(config.timeline_name)

            for clip in config.clips:
                self.media_manager.place_clip(clip)
            log.info(f"Placed {len(config.clips)} video clips")

            log.info(f"Saving the project before export...")
            self.project_manager.save_project()

            export_path = Path(config.export_path)
            self.project_manager.export_project(str(export_path.parent), str(export_path.stem))

            log.info(f"Project '{config.project_name}' exported successfully on path {config.export_path}")
            return True
            
        except Exception as e:
            log.error(f"Error building timeline: {e}")
            return False
