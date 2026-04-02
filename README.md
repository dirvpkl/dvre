# DVRE - DaVinci Resolve Video Editor

Server for creating timelines via DaVinci Resolve scripting API.

## Requirements

- DaVinci Resolve (Studio recommended for full API access)
- Python ==3.10
- Windows (for fusionscript.dll support)

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

In `exapmle_config.json` `video_clips` must be located on correct location by index in list.
