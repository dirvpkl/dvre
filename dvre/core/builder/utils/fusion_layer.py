from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dvre.schemas.layers import FusionLayer
from dvre.utils.errors import ResolveError
from dvre.utils.types import AUDIO_ONLY, VIDEO_ONLY

if TYPE_CHECKING:
    from dvre.core.builder.utils.runtime import BuildRuntime

log = logging.getLogger(__name__)


def process_fusion_layer(runtime: BuildRuntime, layer: FusionLayer) -> None:
    if (
        runtime.compound_mpi is None
        or runtime.compound_start is None
        or runtime.compound_end is None
    ):
        raise ResolveError(
            f"FusionLayer '{layer.name}' has no previous compound. "
            f"FusionLayer must follow a BaseLayer."
        )

    prev_end = runtime.compound_start
    for fusion_clip in layer.fusion_clips:
        if prev_end < fusion_clip.start_frame:
            runtime.timeline_service.place_clip(
                runtime.compound_mpi,
                1,
                prev_end,
                fusion_clip.start_frame,
                prev_end,
                VIDEO_ONLY,
            )

        item = runtime.timeline_service.place_clip(
            runtime.compound_mpi,
            1,
            fusion_clip.start_frame,
            fusion_clip.end_frame,
            fusion_clip.start_frame,
            VIDEO_ONLY,
        )
        runtime.fusion_service.create_fusion_clip(fusion_clip, [item])
        prev_end = fusion_clip.end_frame

    if prev_end < runtime.compound_end:
        runtime.timeline_service.place_clip(
            runtime.compound_mpi,
            1,
            prev_end,
            runtime.compound_end,
            prev_end,
            VIDEO_ONLY,
        )

    runtime.timeline_service.place_clip(
        runtime.compound_mpi,
        1,
        runtime.compound_start,
        runtime.compound_end,
        runtime.compound_start,
        AUDIO_ONLY,
    )

    log.info(f"[{layer.name}] Created {len(layer.fusion_clips)} fusion clips")
