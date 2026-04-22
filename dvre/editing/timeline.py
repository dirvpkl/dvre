"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging
from typing import Literal

from dvre.editing.context import BuildContext
from dvre.utils.config import BaseClip
from dvre.utils.errors import ResolveError
from dvre.utils.types import MediaPoolClipInfo, MediaPoolItem, MediaType, TimelineItem

log = logging.getLogger(__name__)


class TimelineService:
    """
    Manages timeline track configuration and clip placement in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def ensure_track_count(
        self, track_type: Literal["audio", "video", "subtitle"], required_tracks: int
    ) -> None:
        timeline = self.context.timeline
        current_tracks = timeline.GetTrackCount(track_type)

        for i in range(required_tracks - current_tracks):
            next_index = current_tracks + i + 1
            created = timeline.AddTrack(
                track_type, "stereo" if track_type == "audio" else None
            )

            if not created:
                raise ResolveError(f"Failed to add {track_type} track {next_index}")

    def place_clip(
        self, media_item: MediaPoolItem, clip_config: BaseClip, media_type: MediaType
    ) -> TimelineItem:
        """Place an already-imported media item onto the timeline."""
        log.info(
            f"Placing clip on timeline | media_type={media_type} | track={clip_config.track} "
            f"| timeline_start={clip_config.timeline_start} | source={clip_config.start_frame}-{clip_config.end_frame}"
        )

        clip_info: MediaPoolClipInfo = {
            "mediaPoolItem": media_item,
            "startFrame": clip_config.start_frame,
            "endFrame": clip_config.end_frame,
            "mediaType": media_type,
            "trackIndex": clip_config.track,
            "recordFrame": self.context.timeline.GetStartFrame()
            + clip_config.timeline_start,
        }

        result = self.context.media_pool.AppendToTimeline([clip_info])
        if not result:
            raise ResolveError(f"Failed to place clip on track {clip_config.track}")

        log.debug(f"Clip placed on track {clip_config.track}")
        return result[0]
