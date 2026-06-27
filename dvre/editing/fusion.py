"""
Fusion clip management for DVRE.
"""

from __future__ import annotations

import logging
from tempfile import NamedTemporaryFile

from dvre.editing.context import BuildContext
from dvre.schemas.clips import FusionSegment
from dvre.utils.errors import ResolveError
from dvre.utils.types import TimelineItem

log = logging.getLogger(__name__)


class FusionService:
    """
    Manages Fusion clip creation in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def create_fusion_segment(
        self,
        fusion_segment: FusionSegment,
        items: list[TimelineItem],
    ) -> TimelineItem:
        result = self.context.timeline.CreateFusionClip(items)
        if not result:
            raise ResolveError(
                f"Failed to create Fusion clip at frames {fusion_segment.start_frame}-{fusion_segment.end_frame}"
            )
        log.info(
            f"Created Fusion clip | frames={fusion_segment.start_frame}-{fusion_segment.end_frame}"
        )

        if fusion_segment.composition is not None:
            self._import_comp(result, fusion_segment.composition)

        return result

    @staticmethod
    def _import_comp(timeline_item: TimelineItem, composition: str) -> None:
        """Import a .comp file into the given Fusion clip."""
        f = NamedTemporaryFile(
            mode="w", suffix=".comp", delete=False
        )  # TODO: it stays forever

        f.write(composition)
        f.close()

        path = f.name

        comp = timeline_item.ImportFusionComp(path)
        if not comp:
            raise ResolveError(f"Failed to import Fusion comp '{path}'")

        log.info(f"Imported Fusion comp: {path}")
