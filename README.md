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
- Temperatures, fans/RPM, voltage, power, current, energy, humidity, frequency, and PWM values exposed through Linux `hwmon` at `/sys/class/hwmon`, including multiple inputs per device
- NVIDIA GPU usage, memory, temperature, and power through `nvidia-smi` when available

The code is intentionally small and test-driven. It now also includes an installable desktop-style launcher for Bazzite/Linux, a polished local UI with hero stats, grouped sensor cards, friendlier value formatting, a fullscreen button for second-screen use, a separate sensor-list API, a template/layout API, configurable borderless panel dimensions, fixed-position widgets, custom labels/fonts/sizes, custom asset metadata for icons/logos/backgrounds, lock state for positioned items, and browser-saved sensor visibility choices.

## Run the prototype

From this folder:

```bash
python3 -m opensensorpanel.cli
```

For local development without installing:

```bash
PYTHONPATH=src python3 -m opensensorpanel.cli
```

## Install on Bazzite / Linux desktop

From this repo:

```bash
./scripts/install-user.sh
```

That installs OpenSensorPanel for the current user into `~/.local/share/opensensorpanel`, creates a launcher at `~/.local/bin/opensensorpanel`, and adds an app-menu entry named **OpenSensorPanel**.

Launch from the app menu, or run:

```bash
opensensorpanel app --kiosk
```

To remove the user install:

```bash
./scripts/uninstall-user.sh
```

## Run the local web panel for development

```bash
PYTHONPATH=src python3 -m opensensorpanel.cli serve --host 127.0.0.1 --port 8766
```

Then open:

```text
http://127.0.0.1:8766
```

The live JSON endpoints are:

```text
http://127.0.0.1:8766/api/snapshot
http://127.0.0.1:8766/api/sensors
http://127.0.0.1:8766/api/template
```

`/api/snapshot` returns current values. `/api/sensors` returns metadata for the sensor picker. `/api/template` returns the current layout template.

## Run tests

```bash
pytest tests -q
```

## Architecture direction

Near-term:

- Python backend prototype for fast hardware discovery
- JSON sensor schema
- CLI snapshot command, local service, and desktop-style app launcher
- Template schema for fixed-position panel layouts
- Template asset metadata for custom icons, logos, and backgrounds with source/license tracking
- Clean-room AIDA64 import strategy for user-owned local templates
- Browser layout editor controls for panel size and widget label/font/lock settings

Long-term:

- Rust host service for efficient, packaged sensor collection
- Tauri/Svelte or Tauri/React panel designer
- WebSocket live sensor feed
- Second-monitor fullscreen display mode
- `.ospanel` template export/import format
