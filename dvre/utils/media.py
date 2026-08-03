import json
import subprocess
from dataclasses import dataclass
from typing import Protocol


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
