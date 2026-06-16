from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dvre.core.builder.utils.base_layer import process_base_layer
from dvre.core.builder.utils.fusion_layer import process_fusion_layer
from dvre.schemas.layers import BaseLayer, FusionLayer
from dvre.utils.types import TimelineClipInfo

if TYPE_CHECKING:
    from dvre.core.builder.utils.runtime import BuildRuntime

log = logging.getLogger(__name__)


def load_previous_compound(runtime: BuildRuntime, layer_name: str) -> None:
    if not runtime.prev_compound:
        return

    runtime.compound_mpi, runtime.compound_start, runtime.compound_end = (
        runtime.timeline_service.get_compound_info(runtime.prev_compound)
    )
    runtime.timeline_service.delete_clips([runtime.prev_compound])
    log.info(f"[{layer_name}] Cleared previous compound from timeline")


def process_layer(runtime: BuildRuntime, layer: BaseLayer | FusionLayer) -> None:
    if isinstance(layer, BaseLayer):
        process_base_layer(runtime, layer)
        return

    if isinstance(layer, FusionLayer):
        process_fusion_layer(runtime, layer)


def compound_layer(runtime: BuildRuntime, layer_name: str) -> None:
    compound_clip_info: TimelineClipInfo = {
        "startTimecode": None,
        "name": layer_name,
    }
    runtime.prev_compound = runtime.timeline_service.compound_clip(compound_clip_info)
    log.info(f"[{layer_name}] Compound clip created")
