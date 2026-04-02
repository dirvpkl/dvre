"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging
from typing import Literal

from dvre.editing.context import BuildContext
from dvre.utils.errors import ResolveError

log = logging.getLogger(__name__)


class TimelineService:
    """
    Manages timeline track configuration in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def ensure_track_count(self, track_type: Literal['audio', 'video', 'subtitle'], required_tracks: int) -> None:
        timeline = self.context.timeline
        current_tracks = timeline.GetTrackCount(track_type)

        for i in range(required_tracks - current_tracks):
            next_index = current_tracks + i + 1
            created = timeline.AddTrack(track_type, "stereo" if track_type == "audio" else None)

            if not created:
                raise ResolveError(f"Failed to add {track_type} track {next_index}")
