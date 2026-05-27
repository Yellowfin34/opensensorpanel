# OpenSensorPanel Backend Prototype Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the first usable Linux sensor backend for a Bazzite-friendly SensorPanel alternative.

**Architecture:** Start with a Python prototype so hardware discovery can move quickly on this machine. Keep the public output as a clean JSON schema so the backend can later be replaced with a Rust daemon without changing the UI/template layer.

**Tech Stack:** Python 3.11, pytest, Linux `/proc`, Linux `hwmon` sysfs.

---

## Task 1: Parse RAM data from `/proc/meminfo`

**Objective:** Convert raw Linux memory data into total, available, used bytes, and used percentage.

**Files:**
- Create: `src/opensensorpanel/linux_sensors.py`
- Test: `tests/test_linux_sensors.py`

**Verification:**

```bash
pytest tests/test_linux_sensors.py::test_parse_meminfo_returns_used_and_total_bytes -v
```

Expected: PASS.

## Task 2: Parse aggregate CPU jiffy snapshots

**Objective:** Extract total and idle jiffies from the aggregate `cpu` line in `/proc/stat`.

**Files:**
- Modify: `src/opensensorpanel/linux_sensors.py`
- Test: `tests/test_linux_sensors.py`

**Verification:**

```bash
pytest tests/test_linux_sensors.py::test_parse_proc_stat_cpu_extracts_total_and_idle_jiffies -v
pytest tests/test_linux_sensors.py::test_cpu_usage_percent_between_two_snapshots -v
```

Expected: PASS.

## Task 3: Parse one `hwmon` temperature sensor

**Objective:** Convert Linux millidegree Celsius temperature files into a normalized sensor dictionary.

**Files:**
- Modify: `src/opensensorpanel/linux_sensors.py`
- Test: `tests/test_linux_sensors.py`

**Verification:**

```bash
pytest tests/test_linux_sensors.py::test_parse_hwmon_temperature_converts_millicelsius_and_uses_label -v
```

Expected: PASS.

## Task 4: Collect RAM and `hwmon` sensors from real filesystem paths

**Objective:** Read `meminfo` and `hwmon` directories and return normalized sensor rows.

**Files:**
- Create: `src/opensensorpanel/collectors.py`
- Test: `tests/test_collectors.py`

**Verification:**

```bash
pytest tests/test_collectors.py -v
```

Expected: PASS.

## Task 5: Combine sensors into one snapshot schema

**Objective:** Create a JSON-serializable snapshot with schema version, timestamp, and sensors.

**Files:**
- Create: `src/opensensorpanel/snapshot.py`
- Test: `tests/test_snapshot.py`

**Verification:**

```bash
pytest tests/test_snapshot.py -v
```

Expected: PASS.

## Task 6: Add CLI output

**Objective:** Print the current sensor snapshot as JSON.

**Files:**
- Create: `src/opensensorpanel/cli.py`
- Test: `tests/test_cli.py`

**Verification:**

```bash
pytest tests/test_cli.py -v
PYTHONPATH=src python3 -m opensensorpanel.cli
```

Expected: tests pass and CLI prints JSON.

## Next plan after this prototype

1. Add real CPU usage sampling with two `/proc/stat` reads.
2. Add NVIDIA GPU collector using `nvidia-smi --query-gpu=... --format=csv,noheader,nounits` first, then NVML later.
3. Add FastAPI or bare WebSocket live feed.
4. Build a fixed HTML/Tauri panel layout.
5. Add template JSON format and renderer.
