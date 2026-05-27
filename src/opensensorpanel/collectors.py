from __future__ import annotations

from pathlib import Path

from .linux_sensors import parse_hwmon_temperature, parse_meminfo

Sensor = dict[str, str | float | int]


def collect_memory_snapshot(meminfo_path: Path = Path("/proc/meminfo")) -> list[Sensor]:
    memory = parse_meminfo(meminfo_path.read_text())
    return [
        {
            "id": "memory.ram.used_percent",
            "label": "RAM Used",
            "category": "memory",
            "device": "System Memory",
            "value": memory["used_percent"],
            "unit": "%",
        },
        {
            "id": "memory.ram.used_bytes",
            "label": "RAM Used Bytes",
            "category": "memory",
            "device": "System Memory",
            "value": memory["used_bytes"],
            "unit": "B",
        },
    ]


def collect_hwmon_temperatures(hwmon_root: Path = Path("/sys/class/hwmon")) -> list[Sensor]:
    sensors: list[Sensor] = []
    if not hwmon_root.exists():
        return sensors

    for device_path in sorted(path for path in hwmon_root.iterdir() if path.is_dir()):
        files = _read_hwmon_files(device_path)
        if not any(name.startswith("temp") and name.endswith("_input") for name in files):
            continue
        device_name = files.get("name", device_path.name).strip()
        sensor = parse_hwmon_temperature(device_name, files)
        sensor_id = str(sensor["id"])
        sensor["id"] = sensor_id.replace("hwmon.", f"hwmon.{device_path.name}.", 1)
        sensors.append(sensor)
    return sensors


def _read_hwmon_files(device_path: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for child in sorted(device_path.iterdir()):
        if child.is_file() and (child.name == "name" or child.name.startswith("temp")):
            try:
                files[child.name] = child.read_text()
            except OSError:
                continue
    return files
