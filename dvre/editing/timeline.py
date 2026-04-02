"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging

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

    def create_timeline(self, timeline_name: str) -> Timeline:
        # TODO: add configuration for resolution specification
        # typically 1920x1080
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
