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
- CPU usage from two `/proc/stat` samples
- Temperatures exposed through Linux `hwmon` at `/sys/class/hwmon`, including multiple temperature inputs per device
- NVIDIA GPU usage, memory, temperature, and power through `nvidia-smi` when available

The code is intentionally small and test-driven. It now also includes a tiny local web UI prototype with friendlier value formatting.

## Run the prototype

From this folder:

```bash
python3 -m opensensorpanel.cli
```

For local development without installing:

```bash
PYTHONPATH=src python3 -m opensensorpanel.cli
```

## Run the local web panel

```bash
PYTHONPATH=src python3 -m opensensorpanel.cli serve --host 127.0.0.1 --port 8766
```

Then open:

```text
http://127.0.0.1:8766
```

The live JSON endpoint is:

```text
http://127.0.0.1:8766/api/snapshot
```

## Run tests

```bash
pytest tests -q
```

## Architecture direction

Near-term:

- Python backend prototype for fast hardware discovery
- JSON sensor schema
- CLI snapshot command and local web panel

Long-term:

- Rust host service for efficient, packaged sensor collection
- Tauri/Svelte or Tauri/React panel designer
- WebSocket live sensor feed
- Second-monitor fullscreen display mode
- `.ospanel` template export/import format
