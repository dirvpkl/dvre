"""
Builder - orchestrates services from config.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dvre.editing.context import ContextFactory
from dvre.editing.fusion import FusionService
from dvre.editing.media import MediaService
from dvre.editing.project import ProjectService
from dvre.editing.timeline import TimelineService
from dvre.utils.config import BuildConfig, BaseLayer, FusionLayer
from dvre.utils.errors import ResolveError
from dvre.utils.helper import VideoValidator, AudioValidator
from dvre.utils.types import (
    ProjectManager as ResolveProjectManager,
    TimelineItem,
    MediaPoolItem,
    VIDEO_ONLY,
    AUDIO_ONLY,
    TimelineClipInfo
)

log = logging.getLogger(__name__)


class OutputBuilder:
    """
    Orchestrates the complete timeline creation process and its export.
    """

    def __init__(self, project_manager: ResolveProjectManager):
        self.factory = ContextFactory(project_manager)

    # TODO: All the clips MUST BE 1920x1080! The timeline supports only 1920x1080
    # TODO: Moreover you better to make background from that clips and upscale and blur to make it as background image
    # TODO: So if the videos 4:3 and vertically fits fully - adjust the size by 1.777 in zoom to perfectly fit this
    # TODO: You can make even 2 because blur must be enabled.
    def build(self, config: BuildConfig) -> str:
        log.info(
            f"Starting build: project='{config.project_name}' timeline='{config.timeline_name}'"
        )

        context = self.factory.create(
            config.project_name, config.timeline_name, config.settings
        )

        project_service = ProjectService(context)
        media_service = MediaService(context)
        timeline_service = TimelineService(context)
        fusion_service = FusionService(context)

        _vv = VideoValidator(config.settings.width, config.settings.height, config.settings.frame_rate)
        _av = AudioValidator()

        prev_compound: TimelineItem | None = None
        compound_mpi: MediaPoolItem | None = None
        compound_start: int
        compound_end: int

        for layer in config.layers:

            if prev_compound:
                compound_mpi, compound_start, compound_end = timeline_service.get_compound_info(prev_compound)
                timeline_service.delete_clips([prev_compound])
                log.info(f"[{layer.name}] Cleared previous compound from timeline")

            if isinstance(layer, BaseLayer):
                if layer.video_clips:
                    timeline_service.ensure_track_count(
                        "video", max(clip.track for clip in layer.video_clips)
                    )
                if layer.audio_clips:
                    timeline_service.ensure_track_count(
                        "audio", max(clip.track for clip in layer.audio_clips)
                    )

                if compound_mpi:
                    for track_type, clips in (("video", layer.video_clips), ("audio", layer.audio_clips)):
                        # only track #1 must be gapping. e.g. notification appear suddenly in a video
                        # it is required typically only for background
                        track_clips = sorted(
                            [c for c in clips if c.track == 1], 
                            key=lambda c: c.timeline_start
                        )

                        prev_end = compound_start
                        for clip in track_clips:
                            if prev_end < clip.timeline_start:
                                timeline_service.place_clip(
                                    compound_mpi, 1, prev_end, clip.timeline_start, prev_end,
                                    VIDEO_ONLY if track_type == "video" else AUDIO_ONLY
                                )
                            prev_end = clip.timeline_start + (clip.end_frame - clip.start_frame)

                        if prev_end < compound_end:
                            timeline_service.place_clip(
                                compound_mpi, 1, prev_end, compound_end, prev_end,
                                VIDEO_ONLY if track_type == "video" else AUDIO_ONLY
                            )

                for clip in layer.video_clips:
                    media_item = media_service.import_media(clip.path, _vv)
                    timeline_service.place_clip(
                        media_item, clip.track, clip.start_frame, clip.end_frame, clip.timeline_start, VIDEO_ONLY
                    )
                log.info(f"[{layer.name}] Placed {len(layer.video_clips)} video clips")

                for clip in layer.audio_clips:
                    media_item = media_service.import_media(clip.path, _av)
                    timeline_service.place_clip(
                        media_item, clip.track, clip.start_frame, clip.end_frame, clip.timeline_start, AUDIO_ONLY
                    )
                log.info(f"[{layer.name}] Placed {len(layer.audio_clips)} audio clips")

            # `place_clip` sets track 1 because the fusion works only with track 1
            elif isinstance(layer, FusionLayer):
                if not compound_mpi:
                    raise ResolveError(
                        f"FusionLayer '{layer.name}' has no previous compound. "
                        f"FusionLayer must follow a BaseLayer."
                    )

                prev_end = compound_start
                for fusion_clip in layer.fusion_clips:
                    # gap before the fusion segment
                    if prev_end < fusion_clip.start_frame:
                        timeline_service.place_clip(
                            compound_mpi, 1, prev_end, fusion_clip.start_frame, prev_end, VIDEO_ONLY
                        )
                    # fusion segment
                    item = timeline_service.place_clip(
                        compound_mpi, 1, fusion_clip.start_frame, fusion_clip.end_frame,
                        fusion_clip.start_frame, VIDEO_ONLY
                    )
                    fusion_service.create_fusion_clip(fusion_clip, [item])
                    prev_end = fusion_clip.end_frame

                # gap after the last fusion segment
                if prev_end < compound_end:
                    timeline_service.place_clip(
                        compound_mpi, 1, prev_end, compound_end, prev_end, VIDEO_ONLY
                    )

                # audio — entire compound as-is
                timeline_service.place_clip(
                    compound_mpi, 1, compound_start, compound_end, compound_start, AUDIO_ONLY
                )

                log.info(f"[{layer.name}] Created {len(layer.fusion_clips)} fusion clips")

            compound_clip_info: TimelineClipInfo = {
                "startTimecode": None,
                "name": layer.name,
            }
            prev_compound = timeline_service.compound_clip(compound_clip_info)
            log.info(f"[{layer.name}] Compound clip created")

        if config.save_project:
            project_service.save_current_project()

        export_path = Path(config.export_path)
        job_id = project_service.export_project(
            str(export_path.parent),
            str(export_path.stem),
            config.settings.width,
            config.settings.height,
            config.settings.frame_rate,
        )

        log.info(f"Export started: {config.export_path} job_id={job_id}")

        return job_id
