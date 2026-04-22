"""
Project management for DVRE.
"""

from __future__ import annotations

import logging

from dvre.editing.context import BuildContext
from dvre.utils.errors import ResolveError
from dvre.utils.types import RenderSettings

log = logging.getLogger(__name__)


class ProjectService:
    """
    Manages project persistence and export in DaVinci Resolve.
    """

    def __init__(self, context: BuildContext):
        self.context = context

    def save_current_project(self) -> None:
        log.info("Saving current project...")

        if not self.context.project_manager.SaveProject():
            raise ResolveError("Failed to save current project")

        log.info("Project saved")

    def export_project(
        self,
        export_path: str,
        export_name: str,
        width: int,
        height: int,
        frame_rate: float,
    ) -> None:
        self.context.project.SetCurrentRenderFormatAndCodec("MP4", "H264")
        settings: RenderSettings = {
            "SelectAllFrames": True,
            "MarkIn": 0,  # ignoring because of SelectAllFrames=True
            "MarkOut": 0,  # ignoring because of SelectAllFrames=True
            "TargetDir": export_path,
            "CustomName": export_name,
            "UniqueFilenameStyle": 1,  # 0=Prefix, 1=Suffix
            "ReplaceExistingFilesInPlace": False,
            "ClipStartFrame": 0,
            "TimelineStartTimecode": "01:00:00:00",  # stock value
            "FormatWidth": width,
            "FormatHeight": height,
            "FrameRate": frame_rate,
            "PixelAspectRatio": "square",
            "ExportVideo": True,
            "VideoQuality": 0,  # 0=auto | int=bitrate kbps | "Least".."Best"
            "EncodingProfile": "High",  # H.264/H.265 only
            "MultiPassEncode": False,  # H.264 only
            "ExportAlpha": False,
            "AlphaMode": 0,  # 0=Premultiplied | 1=Straight (ExportAlpha only)
            "NetworkOptimization": True,  # QuickTime & MP4 only
            "ColorSpaceTag": "Same as Project",
            "GammaTag": "Same as Project",
            "ExportAudio": True,
            "AudioCodec": "aac",
            "AudioBitDepth": 16,
            "AudioSampleRate": 48000,
            "ExportSubtitle": False,
            "SubtitleFormat": "BurnIn",  # "BurnIn" | "EmbeddedCaptions" | "SeparateFile"
        }

        self.context.project.SetRenderSettings(settings)
        job_id = self.context.project.AddRenderJob()
        self.context.project.StartRendering([job_id], isInteractiveMode=False)

    def close_project(self):
        log.debug("Closing the project")
        self.context.project_manager.CloseProject(self.context.project)
        log.debug("Closed the project")
