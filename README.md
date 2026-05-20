# DVRE — DaVinci Resolve Video Editor

HTTP server that builds DaVinci Resolve timelines programmatically via the Resolve scripting API. Accepts a JSON layer-based config and produces a rendered MP4.

## How it works

A build config is a **stack of layers**. Each layer is collapsed into a compound clip. The next layer references the previous compound — gap-fill on track 1, Fusion `.comp` segments, overlays on track 2+.

Layer types:
- **BaseLayer** — places raw video/audio clips on tracks
- **FusionLayer** — slices the previous compound and applies `.comp` files as transitions/effects

```
BaseLayer (RAW clips) → compound clip
    ↓
FusionLayer (comp effects) → compound clip
    ↓
Export MP4/H.264
```

## Requirements

- **DaVinci Resolve Studio 21B3+** (Free version has no scripting API)
- **Python** 3.10
- **Windows** (fusionscript.dll)
- **ffprobe** — in PATH or set `FFPROBE_PATH`

> **Audio:** only **WAV**. MP3 has encoder delay that Resolve doesn't compensate (1–3 frame drift). Convert to WAV first.

## Quick start

```bash
uv sync
# configure .env (copy from .env.example)
uv run python main.py
```

Server starts on `http://127.0.0.1:8000`.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/build` | Submit a build config, returns `job_id` |
| GET | `/render-job/{job_id}/status` | Poll render progress |
| POST | `/project/close` | Close current Resolve project |

Builds are serialized — only one at a time (409 if busy).

## Build config

```json
{
  "project_name": "My Video",
  "timeline_name": "Main Timeline",
  "settings": {
    "width": 1920,
    "height": 1080,
    "frame_rate": 60
  },
  "layers": [
    {
      "name": "RAW",
      "video_clips": [
        {
          "path": "C:/Videos/intro.mp4",
          "track": 1,
          "timeline_start_frame": 0,
          "start_frame": 0,
          "end_frame": 240
        }
      ],
      "audio_clips": [
        {
          "path": "C:/Audio/voiceover.wav",
          "track": 1,
          "timeline_start_frame": 0,
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

### Clip fields (video / audio)

| Field | Description |
|-------|-------------|
| `path` | Absolute path to source media |
| `track` | 1-based timeline track |
| `timeline_start_frame` | Position on timeline |
| `start_frame` / `end_frame` | In/out points in source |

### Fusion clips

| Field | Description |
|-------|-------------|
| `start_frame` / `end_frame` | Segment of previous compound to apply comp to |
| `comp_path` | Absolute path to `.comp` file |

### Gap-fill

Gaps on **track 1** between clips are automatically filled with slices of the previous compound. Tracks ≥ 2 are overlays — no gap-fill.

### Export

Output is MP4/H.264. Set `save_project: true` to keep the Resolve project file.

## Project structure

```
dvre/
├── dvre/
│   ├── server.py          # FastAPI app, routes, middleware
│   ├── builder.py         # OutputBuilder — layer processing pipeline
│   ├── editing/
│   │   ├── context.py     # BuildContext, Resolve project/timeline init
│   │   ├── timeline.py    # Track management, clip placement, compounding
│   │   ├── media.py       # Media pool import
│   │   ├── fusion.py      # Fusion comp clip creation
│   │   └── project.py     # Save, export, render job control
│   └── utils/
│       ├── config.py      # Pydantic models (BuildConfig, layer types)
│       ├── helper.py      # Resolve connection, ffprobe validation
│       ├── errors.py      # ResolveError
│       ├── logger.py      # Logging config (file + console)
│       └── types.py       # Resolve API type stubs
├── main.py                # Entry point
└── pyproject.toml
```

## Tech

- **FastAPI** / **uvicorn** — HTTP server
- **Pydantic** — config validation
- **psutil** — Resolve process management
- **python-dotenv** — env config
- **fusionscript-stubs** — Resolve API type hints
- **uv** — package manager
- **black** + **ruff** + **isort** — code quality (pre-commit)
