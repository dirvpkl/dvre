"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging
from typing import Literal

from dvre.editing.resolve_client import ResolveClient
from dvre.utils.types import Timeline

log = logging.getLogger(__name__)


class TimelineManager:
    """
    Manages timeline creation and configuration in DaVinci Resolve.
    """
    
    def __init__(self, client: ResolveClient):
        """
        Initialize TimelineManager.
        
        Args:
            client: ResolveClient instance
        """
        self.client = client

    @staticmethod
    def ensure_track_count(timeline: Timeline, track_type: Literal['audio', 'video', 'subtitle'], required_tracks: int) -> None:
        current_tracks = timeline.GetTrackCount(track_type)

        for i in range(required_tracks - current_tracks):
            next_index = current_tracks + i + 1
            if track_type == "audio":
                created = timeline.AddTrack(track_type, "stereo")
            else:
                created = timeline.AddTrack(track_type, None)

            if not created:
                raise RuntimeError(f"Failed to add {track_type} track {next_index}")

    def create_timeline(self, timeline_name: str) -> Timeline:
        """
        Create a new timeline with the given configuration.

        Args:
            timeline_name: timeline name

        Returns:
            Timeline object
        """

        # Create new timeline
        log.info(f"Creating timeline: {timeline_name}")
        timeline = self.client.media_pool.CreateEmptyTimeline(timeline_name)

        if timeline is None:
            raise RuntimeError(f"Failed to create timeline: {timeline_name}")

        log.info(f"Timeline '{timeline_name}' created successfully on path")
        return timeline
