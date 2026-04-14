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

The server accepts a JSON config with separate video and audio placement:

```json
{
  "project_name": "My Video Project",
  "timeline_name": "Main Timeline",
  "settings": {
    "width": 1920,
    "height": 1080,
    "frame_rate": 60.0
  },
  "video_clips": [
    {
      "id": "intro",
      "path": "C:/Videos/intro.mp4",
      "track": 1,
      "timeline_start": 0,
      "start_frame": 0,
      "end_frame": 240
    }
  ],
  "audio_clips": [
    {
      "path": "C:/Audio/voiceover.wav",
      "track": 1,
      "timeline_start": 0,
      "start_frame": 0,
      "end_frame": 740
    }
  ],
  "fusion_clips": [
    {
      "clip_ids": ["main", "broll"],
      "comp_path": "C:/Comps/overlay.comp"
    }
  ],
  "export_path": "C:/Videos/output.mp4",
  "save_project": false
}
```

### Clip Fields

- `video_clips` and `audio_clips`: clips to place on explicit timeline tracks.
- each clip supports `track`, `timeline_start`, `start_frame`, `end_frame`.
- `id` (optional for audio): unique identifier for video clips, used by `fusion_clips`.

### Fusion Comps

- `fusion_clips`: list of Fusion compositions referencing video clips by `clip_ids`.
- `comp_path`: path to a `.comp` file.

### Export

- `export_path`: output file path for rendering.
- `save_project`: whether to save the DaVinci Resolve project file.

The server uses Resolve `AppendToTimeline([{clipInfo}])` with `trackIndex`, `recordFrame` and `mediaType`, so video and audio can be placed independently on different tracks.
Track counts are derived automatically from the highest `track` number in the clip lists. Audio tracks are always created as `stereo`.
