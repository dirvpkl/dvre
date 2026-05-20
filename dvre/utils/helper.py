import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Protocol

import psutil

from dvre.utils.types import Resolve

log = logging.getLogger(__name__)

RESOLVE_EXE = os.getenv(
    "RESOLVE_EXE", r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

RESOLVE_API = os.getenv(
    "RESOLVE_SCRIPT_API",
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
)

RESOLVE_LIB = os.getenv(
    "RESOLVE_SCRIPT_LIB",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll",
)


def ensure_resolve_running() -> bool:
    """Ensure DaVinci Resolve is running, start it if not. Returns True if Resolve was just started."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] == "Resolve.exe":
                log.debug("Resolve already running")
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    log.info("Starting Resolve...")
    subprocess.Popen([RESOLVE_EXE, "-nogui"])
    return True


def get_resolve(timeout: int = 120) -> Resolve:
    """Connect to the DaVinci Resolve scripting API."""
    fresh_start = ensure_resolve_running()

    if RESOLVE_API not in sys.path:
        sys.path.append(RESOLVE_API)

    if RESOLVE_LIB not in sys.path:
        sys.path.append(RESOLVE_LIB)

    import DaVinciResolveScript as dvr  # type: ignore

    start = time.time()
    while time.time() - start < timeout:
        resolve: Resolve = dvr.scriptapp("Resolve")
        if resolve:
            log.debug("Connected to Resolve")
            if fresh_start:
                resolve.DisableBackgroundTasksForCurrentResolveSession()
                log.debug("Background tasks disabled for this Resolve session")
            return resolve
        time.sleep(1)
        log.debug("Waiting for Resolve...")

    raise TimeoutError(f"Resolve didn't start in {timeout} seconds")


def _get_video_meta(path: str) -> dict[str, int | float]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            "-select_streams",
            "v:0",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    num, den = map(int, stream["r_frame_rate"].split("/"))

    return {
        "width": stream["width"],
        "height": stream["height"],
        "fps": num / den,
    }


@dataclass
class VideoValidator:
    width: int
    height: int
    fps: float
    fps_tolerance: float = 0.01

    def assert_meta(self, path: str) -> None:
        meta = _get_video_meta(path)
        if (
            meta["width"] != self.width
            or meta["height"] != self.height
            or abs(meta["fps"] - self.fps) > self.fps_tolerance
        ):
            raise ValueError(
                f"Video meta mismatch: expected {self.width}x{self.height}@{self.fps}fps, "
                f"got {meta['width']}x{meta['height']}@{meta['fps']:.4f}fps — '{path}'"
            )


@dataclass
class AudioValidator:
    @staticmethod
    def assert_meta(path: str) -> None:
        if not path.endswith(".wav"):
            raise ValueError(
                "Audio validator requires the .wav extension.mp3 may cause timing drift"
            )


class MediaValidator(Protocol):
    def assert_meta(self, path: str) -> None: ...
