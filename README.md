# DVRE - DaVinci Resolve Video Editor

Server for creating timelines via DaVinci Resolve scripting API.

## Requirements

- **DaVinci Resolve Studio**
- **Python** ==3.10
- **Windows** (for fusionscript.dll support)
- **ffprobe** (required for `validate_media` to validate videos before load in DaVinci mediapool) — Ensure `ffprobe` is installed and available in your system PATH, or set the `FFPROBE_PATH` environment variable to its location.
- **Audio format:** Always use **WAV** files for audio clips. MP3 files have an encoder delay that DaVinci Resolve does not compensate for, causing audio to be offset by 1–3 frames on the timeline. Convert MP3 to WAV before passing to the build config.

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

The timeline is built as a stack of **layers**, processed in order. Each layer is
collapsed into a compound clip, and the next layer is built on top of it,
referencing the previous compound where needed (gap-fill, fusion segments).

There are two layer types:

- **`BaseLayer`** — places raw video/audio clips on tracks.
- **`FusionLayer`** — slices the previous compound by `[start_frame, end_frame]`
  and applies a `.comp` to each segment. Must follow a `BaseLayer` (raises
  `ResolveError` otherwise).

```json
{
  "project_name": "My Video Project",
  "timeline_name": "Main Timeline",
  "settings": {
    "width": 1920,
    "height": 1080,
    "frame_rate": 60.0
  },
  "layers": [
    {
      "name": "RAW",
      "video_clips": [
        {
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
      ]
    },
    {
      "name": "FX",
      "fusion_clips": [
        {
          "start_frame": 60,
          "end_frame": 180,
          "comp_path": "C:/Comps/overlay.comp"
        }
      ]
    }
  ],
  "export_path": "C:/Videos/output.mp4",
  "save_project": false
}
```

### Layers

- `name` — name of the resulting compound clip for this layer.
- `BaseLayer` carries `video_clips` and/or `audio_clips`.
- `FusionLayer` carries `fusion_clips` and slices the previous compound.

A single layer cannot mix raw clips and fusion clips — they are separate types.
Put fusion effects in their own `FusionLayer` placed after a `BaseLayer`.

### Clip Fields

`video_clips` and `audio_clips` share the same fields:

- `path` — absolute path to the source media.
- `track` — 1-based timeline track.
- `timeline_start` — frame on the timeline where the clip starts.
- `start_frame` / `end_frame` — in/out points within the source media.

### Fusion Clips

- `start_frame` / `end_frame` — segment of the previous compound to apply Fusion to.
- `comp_path` — absolute path to a `.comp` file (required).

### Gap-fill behavior

Inside a `BaseLayer`, gaps on **track 1** between newly placed clips are
automatically filled with slices of the previous compound, so the main
videoline stays continuous across layers. Clips on tracks ≥ 2 do **not**
trigger gap-fill — they are treated as overlays sitting on top of track 1.

### Export

- `export_path` — output file path for rendering.
- `save_project` — whether to save the DaVinci Resolve project file.

The server uses Resolve `AppendToTimeline([{clipInfo}])` with `trackIndex`,
`recordFrame` and `mediaType`, so video and audio can be placed independently
on different tracks. Track counts are derived automatically from the highest
`track` number in each layer's clip lists. Audio tracks are always created as
`stereo`.
