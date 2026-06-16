from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dvre.schemas.layers import BaseLayer
from dvre.utils.types import AUDIO_ONLY, VIDEO_ONLY

if TYPE_CHECKING:
    from dvre.core.builder.utils.runtime import BuildRuntime

log = logging.getLogger(__name__)


def process_base_layer(runtime: BuildRuntime, layer: BaseLayer) -> None:
    if layer.video_clips:
        runtime.timeline_service.ensure_track_count(
            "video", max(clip.track for clip in layer.video_clips)
        )
    if layer.audio_clips:
        runtime.timeline_service.ensure_track_count(
            "audio", max(clip.track for clip in layer.audio_clips)
        )

    if runtime.compound_mpi:
        _fill_compound_gaps(runtime, layer.video_clips, VIDEO_ONLY)
        _fill_compound_gaps(runtime, layer.audio_clips, AUDIO_ONLY)

    for clip in layer.video_clips:
        media_item = runtime.media_service.import_media(clip.path, runtime.video_validator)
        runtime.timeline_service.place_clip(
            media_item,
            clip.track,
            clip.start_frame,
            clip.end_frame,
            clip.timeline_start_frame,
            VIDEO_ONLY,
        )
    log.info(f"[{layer.name}] Placed {len(layer.video_clips)} video clips")

    for clip in layer.audio_clips:
        media_item = runtime.media_service.import_media(clip.path, runtime.audio_validator)
        runtime.timeline_service.place_clip(
            media_item,
            clip.track,
            clip.start_frame,
            clip.end_frame,
            clip.timeline_start_frame,
            AUDIO_ONLY,
        )
    log.info(f"[{layer.name}] Placed {len(layer.audio_clips)} audio clips")


def _fill_compound_gaps(runtime: BuildRuntime, clips: list, media_type: int) -> None:
    if runtime.compound_mpi is None or runtime.compound_start is None or runtime.compound_end is None:
        return

    track_clips = sorted(
        [clip for clip in clips if clip.track == 1],
        key=lambda clip: clip.timeline_start_frame,
    )

    prev_end = runtime.compound_start
    for clip in track_clips:
        if prev_end < clip.timeline_start_frame:
            runtime.timeline_service.place_clip(
                runtime.compound_mpi,
                1,
                prev_end,
                clip.timeline_start_frame,
                prev_end,
                media_type,
            )
        prev_end = clip.timeline_start_frame + (clip.end_frame - clip.start_frame)

    if prev_end < runtime.compound_end:
        runtime.timeline_service.place_clip(
            runtime.compound_mpi,
            1,
            prev_end,
            runtime.compound_end,
            prev_end,
            media_type,
        )
