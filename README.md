# OpenSensorPanel

A Linux-native SensorPanel-style hardware dashboard for Bazzite gamers and PC builders.

## Product goal

Build the Linux equivalent of the AIDA64 SensorPanel experience:

- Live hardware stats
- Beautiful custom panels
- Template sharing
- Second-screen display
- Easy setup for gamers and PC builders

## Current status

This repo currently contains the first tested backend prototype. It can collect:

- RAM usage from `/proc/meminfo`
- Temperatures exposed through Linux `hwmon` at `/sys/class/hwmon`

The code is intentionally small and test-driven. The next step is CPU usage sampling, then NVIDIA GPU support.

## Run the prototype

From this folder:

```bash
python3 -m opensensorpanel.cli
```

For local development without installing:

```bash
PYTHONPATH=src python3 -m opensensorpanel.cli
```

## Run tests

```bash
pytest tests -q
```

## Architecture direction

Near-term:

- Python backend prototype for fast hardware discovery
- JSON sensor schema
- CLI snapshot command

Long-term:

- Rust host service for efficient, packaged sensor collection
- Tauri/Svelte or Tauri/React panel designer
- WebSocket live sensor feed
- Second-monitor fullscreen display mode
- `.ospanel` template export/import format
