# DVRE - DaVinci Resolve Video Editor

Server for creating timelines via DaVinci Resolve scripting API.

## Requirements

- **DaVinci Resolve Studio**
- **Python** ==3.10
- **Windows** (for fusionscript.dll support)
- **ffprobe** (required for `validate_media` to validate videos before load in DaVinci mediapool) — Ensure `ffprobe` is installed and available in your system PATH, or set the `FFPROBE_PATH` environment variable to its location.

## Installation

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
cd dvre
uv sync
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```env
# DaVinci Resolve paths (optional - defaults are used if not specified)
RESOLVE_EXE=C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe
RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules
RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll

# Server settings
HOST=127.0.0.1
PORT=8000

# FFprobe
FFPROBE_PATH=ffprobe
```

## Usage

### Starting the Server

```bash
# Using uv
uv run python main.py

# Or directly
python main.py
```

The server will start on `http://127.0.0.1:8000`

## Build Config

`/build` now accepts separate video and audio placement:

- `video_clips` and `audio_clips`: clips to place on explicit timeline tracks.
- each clip supports `track`, `timeline_start`, `start_frame`, `end_frame`.

The server uses Resolve `AppendToTimeline([{clipInfo}])` with `trackIndex`, `recordFrame` and `mediaType`, so video and audio can be placed independently on different tracks.
Track counts are derived automatically from the highest `track` number in the clip lists. Audio tracks are always created as `stereo`.
