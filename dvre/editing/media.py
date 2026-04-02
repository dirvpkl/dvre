"""
Media and clip management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.utils.config import AudioClip, BaseClip, VideoClip
from dvre.editing.resolve_client import ResolveClient
from dvre.utils.types import MediaPoolClipInfo, MediaPoolItem, TimelineItem

log = logging.getLogger(__name__)

VIDEO_ONLY = 1
AUDIO_ONLY = 2
TIMELINE_START_TIMECODE = 86400 # DaVinci starts timeline at frame 86400

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

    def _place_clip(self, clip_config: BaseClip, media_type: int) -> TimelineItem:
        """
        Place a clip on the timeline.

        Args:
            clip_config: clip configuration
            media_type: Resolve media type flag
        """
        try:
            log.info(f"Placing media_type {media_type} | track={clip_config.track} | timeline_start={clip_config.timeline_start} | source={clip_config.start_frame}-{clip_config.end_frame}")
            media_item: MediaPoolItem = self.client.media_pool.ImportMedia([clip_config.path])[0] # it will throw an error if needed
            clip_info: MediaPoolClipInfo = {
                "mediaPoolItem": media_item,
                "startFrame": clip_config.start_frame,
                "endFrame": clip_config.end_frame,
                "mediaType": media_type,
                "trackIndex": clip_config.track,
                "recordFrame": TIMELINE_START_TIMECODE + clip_config.timeline_start
            }
            result = self.client.media_pool.AppendToTimeline([clip_info])

            if result:
                log.debug(f"{clip_config.path} clip placed")
                return result[0]

            raise RuntimeError(f"Failed to place clip: {clip_config.path}")

        except Exception as e:
            raise RuntimeError(f"Error placing clip {clip_config.path}: {e}")

    def place_video_clip(self, clip_config: VideoClip) -> TimelineItem:
        """Place a video clip on the timeline."""

        return self._place_clip(clip_config, VIDEO_ONLY)

    def place_audio_clip(self, clip_config: AudioClip) -> TimelineItem:
        """Place an audio clip on the timeline."""

        return self._place_clip(clip_config, AUDIO_ONLY)
