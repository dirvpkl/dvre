"""
Media pool management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.context import BuildContext
from dvre.utils.errors import ResolveError
from dvre.utils.helper import MediaValidator
from dvre.utils.types import MediaPoolItem

log = logging.getLogger(__name__)


class MediaService:
    """
    Manages media import into the DaVinci Resolve Media Pool.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def import_media(
        self, path: str, source_validator: MediaValidator
    ) -> MediaPoolItem:
        """Import a media file into the Media Pool and return the created item."""
        log.info(f"Importing media: {path}")

        source_validator.assert_meta(path)

        result = self.context.media_pool.ImportMedia([path])
        if not result:
            raise ResolveError(f"Failed to import media '{path}'")

        log.debug(f"Media imported: {path}")
        return result[0]
