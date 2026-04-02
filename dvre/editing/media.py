"""
Media and clip management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.utils.config import VideoClip
from dvre.editing.resolve_client import ResolveClient
from dvre.utils.types import MediaPoolItem

log = logging.getLogger(__name__)


class MediaManager:
    """
    Manages clip placement (and import) in DaVinci Resolve.
    """
    
    def __init__(self, client: ResolveClient):
        """
        Initialize MediaManager.
        
        Args:
            client: ResolveClient instance
        """
        self.client = client

    def _import_media_item(self, path: str) -> MediaPoolItem:
        """
        Import media to media pool.

        Args:
            path: paths to the media files

        Returns:
            True if successful
        """
        try:
            log.info(f"Importing: {path}...")
            media_items = self.client.media_pool.ImportMedia([path])

            if media_items:
                log.debug(f"Imported successfully: {path}")
                return media_items[0]

            raise RuntimeError(f"Failed to import {path}")

        except Exception as e:
            raise RuntimeError(f"Error importing {path}: {e}")

    def place_clip(self, clip_config: VideoClip):
        """
        Place a video clip on the timeline.
        
        Args:
            clip_config: VideoClip configuration
        """
        try:

            log.info(f"Placing video clip {clip_config.start_frame}-{clip_config.end_frame}")
            _clip = self._import_media_item(clip_config.path)
            _clip.SetMarkInOut(clip_config.start_frame, clip_config.end_frame)

            result = self.client.media_pool.AppendToTimeline([_clip])

            if result:
                log.debug(f"Video clip placed: {clip_config.path}")
                return

            raise RuntimeError(f"Failed to place a video clip: {clip_config.path}")

        except Exception as e:
            raise RuntimeError(f"Error placing video clip {clip_config.path}: {e}")
