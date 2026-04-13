import logging
import os
import sys
import time

import json
import subprocess
from dataclasses import dataclass

import psutil
from dotenv import load_dotenv

from dvre.utils.types import Resolve

log = logging.getLogger(__name__)

load_dotenv()

RESOLVE_EXE = os.getenv(
    "RESOLVE_EXE",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"
)

RESOLVE_API = os.getenv(
    "RESOLVE_SCRIPT_API",
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
)

RESOLVE_LIB = os.getenv(
    "RESOLVE_SCRIPT_LIB",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
)


def ensure_resolve_running() -> None:
    """Ensure DaVinci Resolve is running, start it if not."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] == "Resolve.exe":
                log.info("Resolve already running")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    log.info("Starting Resolve...")
    import subprocess
    subprocess.Popen([RESOLVE_EXE, "-nogui"])


def get_resolve(timeout: int = 120) -> Resolve:
    """Connect to the DaVinci Resolve scripting API."""
    ensure_resolve_running()

    if RESOLVE_API not in sys.path:
        sys.path.append(RESOLVE_API)

    if RESOLVE_LIB not in sys.path:
        sys.path.append(RESOLVE_LIB)

    import DaVinciResolveScript as dvr  # type: ignore

    start = time.time()
    while time.time() - start < timeout:
        resolve: Resolve = dvr.scriptapp("Resolve")
        if resolve:
            log.info("Connected to Resolve")
            return resolve
        time.sleep(1)
        log.debug("Waiting for Resolve...")

    raise TimeoutError(f"Resolve didn't start in {timeout} seconds")


def _get_video_meta(path: str) -> dict[str, int | float]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-select_streams", "v:0",
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

    def assert_video_meta(self, path: str) -> None:
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