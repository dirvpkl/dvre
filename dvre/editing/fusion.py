"""
Fusion clip management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.context import BuildContext
from dvre.utils.config import FusionClip
from dvre.utils.errors import ResolveError
from dvre.utils.types import TimelineItem

log = logging.getLogger(__name__)


class FusionService:
    """
    Manages Fusion clip creation in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def create_fusion_clip(
        self,
        fusion_clip: FusionClip,
        placed_items: dict[str, TimelineItem],
    ) -> TimelineItem:
        """Create a Fusion clip from previously placed timeline items referenced by ID."""
        items: list[TimelineItem] = []
        for clip_id in fusion_clip.clip_ids:
            if clip_id not in placed_items:
                raise ResolveError(
                    f"Fusion clip references unknown clip id '{clip_id}'. "
                    f"Available ids: {list(placed_items.keys())}"
                )
            items.append(placed_items[clip_id])

        result = self.context.timeline.CreateFusionClip(items)
        if not result:
            raise ResolveError(f"Failed to create Fusion clip from ids {fusion_clip.clip_ids}")

        log.info(f"Created Fusion clip from ids: {fusion_clip.clip_ids}")
        return result
