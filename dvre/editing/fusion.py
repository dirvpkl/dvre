"""
Fusion clip management for DVRE.
"""

from __future__ import annotations

import logging
from pathlib import Path

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
            items: list[TimelineItem],
    ) -> TimelineItem:
        result = self.context.timeline.CreateFusionClip(items)
        if not result:
            raise ResolveError(
                f"Failed to create Fusion clip at frames {fusion_clip.start_frame}-{fusion_clip.end_frame}"
            )
        log.info(f"Created Fusion clip | frames={fusion_clip.start_frame}-{fusion_clip.end_frame}")

        if fusion_clip.comp_path is not None:
            self._import_comp(result, fusion_clip.comp_path)

        return result

    @staticmethod
    def _import_comp(timeline_item: TimelineItem, comp_path: str) -> None:
        """Import a .comp file into the given Fusion clip."""
        path = Path(comp_path)

        if not path.exists():
            raise ResolveError(f"Fusion comp file not found: {comp_path}")

        if path.suffix.lower() != ".comp":
            raise ResolveError(
                f"Expected a .comp file, got '{path.suffix}': {comp_path}"
            )

        comp = timeline_item.ImportFusionComp(str(path))
        if not comp:
            raise ResolveError(f"Failed to import Fusion comp '{comp_path}'")

        log.info(f"Imported Fusion comp: {comp_path}")
