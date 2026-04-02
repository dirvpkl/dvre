"""
DaVinci Resolve connection and client management.
"""

from __future__ import annotations

import logging

from dvre.editing.utils.helper import get_resolve
from dvre.utils.types import Resolve, ProjectManager, Project, Fusion, MediaPool, MediaPoolItem, Timeline, TimelineItem

log = logging.getLogger(__name__)


class ResolveClient:
    """
    Client for interacting with DaVinci Resolve.
    """
    
    def __init__(self, timeout: int = 120):
        """
        Initialize Resolve client.
        
        Args:
            timeout: Connection timeout in seconds
        """
        self._resolve: Resolve = get_resolve(timeout)
        self._project_manager: ProjectManager | None = None
        self._media_pool: MediaPool | None = None
        self._timeout: int = timeout

    @property
    def resolve(self) -> Resolve:
        """Get the Resolve scripting object."""
        if self._resolve is None:
            self._resolve = get_resolve(self._timeout)
        return self._resolve

    @property
    def project_manager(self) -> ProjectManager:
        return self.resolve.GetProjectManager()

    @property
    def project(self) -> Project:
        return self.project_manager.GetCurrentProject()

    @property
    def media_pool(self) -> MediaPool:
        return self.project.GetMediaPool()

    @property
    def fusion(self) -> Fusion:
        return self.resolve.Fusion()

    @property
    def timeline(self) -> Timeline:
        return self.project.GetTimelineByIndex(1)
