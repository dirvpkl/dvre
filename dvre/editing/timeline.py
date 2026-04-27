"""
Timeline management for DVRE.
"""

from __future__ import annotations

import logging
from typing import Literal

from dvre.editing.context import BuildContext
from dvre.utils.errors import ResolveError
from dvre.utils.types import MediaPoolClipInfo, MediaPoolItem, MediaType, TimelineItem, TimelineClipInfo

log = logging.getLogger(__name__)


class TimelineService:
    """
    Manages timeline track configuration and clip placement in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def ensure_track_count(
        self, track_type: Literal["audio", "video"], required_tracks: int
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
            self,
            media_item: MediaPoolItem,
            track: int,
            start_frame: int,
            end_frame: int,
            timeline_start: int,
            media_type: MediaType,
    ) -> TimelineItem:
        """Place an already-imported media item onto the timeline."""
        log.info(
            f"Placing clip on timeline | media_type={media_type} | track={track} "
            f"| timeline_start={timeline_start} | source={start_frame}-{end_frame}"
        )

        clip_info: MediaPoolClipInfo = {
            "mediaPoolItem": media_item,
            "startFrame": start_frame,
            "endFrame": end_frame,
            "mediaType": media_type,
            "trackIndex": track,
            "recordFrame": self.context.timeline.GetStartFrame()
            + timeline_start,
        }

        result = self.context.media_pool.AppendToTimeline([clip_info])
        if not result:
            raise ResolveError(f"Failed to place a clip {media_item}: {start_frame}/{end_frame} on {timeline_start} on track {track}")

        log.debug(f"Clip placed on track {track}")
        return result[0]

    def compound_clip(self, compound_clip_info: TimelineClipInfo) -> TimelineItem:
        """Compound all items on the timeline into a single compound clip."""
        log.info(f"Creating compound clip | name={compound_clip_info['name']}")

        # Getting all items from all tracks
        items: list[TimelineItem] = []
        for track_type in ("audio", "video"):
            track_count = self.context.timeline.GetTrackCount(track_type)
            for i in range(1, track_count + 1):
                track_items = self.context.timeline.GetItemListInTrack(track_type, i)
                if track_items:
                    items.extend(track_items)

        result = self.context.timeline.CreateCompoundClip(items, compound_clip_info)
        if result:
            return result

        else:
            # Resolve can return None even on successful compound clip creation —
            # when items contain both audio and video tracks simultaneously.
            # In that case we must search the newly created compound clip on the timeline.
            # Since this method compounds every clip into a single one,
            # the result is always the first item on video track 1.
            track_item = self.context.timeline.GetItemListInTrack("video", 1)
            name = compound_clip_info["name"]
            if len(track_item) > 0 and track_item[0].GetName() == name:
                return track_item[0]

        raise ResolveError(f"Failed to create compound clip '{name}'")

    def delete_clips(self, items: list[TimelineItem]) -> bool:
        log.info(f"Deleting clip {items}")
        result = self.context.timeline.DeleteClips(items, False)
        if not result:
            raise ResolveError("Failed to delete clips from timeline")
        return result

    @property
    def start_frame(self) -> int:
        return self.context.timeline.GetStartFrame()

    def get_compound_info(self, item: TimelineItem) -> tuple[MediaPoolItem, int, int]:
        mpi = item.GetMediaPoolItem()
        start = item.GetStart(False) - self.start_frame
        end = item.GetEnd(False) - self.start_frame
        return mpi, start, end
