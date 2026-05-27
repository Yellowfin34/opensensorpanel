from __future__ import annotations

import re
from typing import NamedTuple


class HwmonSensorSpec(NamedTuple):
    prefix: str
    suffix: str
    category: str
    unit: str
    scale: float


HWMON_SENSOR_SPECS = (
    HwmonSensorSpec("temp", "_input", "temperature", "C", 1000),
    HwmonSensorSpec("fan", "_input", "fan", "RPM", 1),
    HwmonSensorSpec("in", "_input", "voltage", "V", 1000),
    HwmonSensorSpec("power", "_input", "power", "W", 1_000_000),
    HwmonSensorSpec("curr", "_input", "current", "A", 1000),
    HwmonSensorSpec("energy", "_input", "energy", "J", 1_000_000),
    HwmonSensorSpec("humidity", "_input", "humidity", "%", 1000),
    HwmonSensorSpec("freq", "_input", "frequency", "Hz", 1),
    HwmonSensorSpec("pwm", "", "pwm", "PWM", 1),
)


def parse_meminfo(text: str) -> dict[str, float | int]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, rest = line.split(":", 1)
        parts = rest.strip().split()
        if not parts:
            continue
        values[key] = int(parts[0]) * 1024

    total = values["MemTotal"]
    available = values["MemAvailable"]
    used = total - available
    return {
        "total_bytes": total,
        "available_bytes": available,
        "used_bytes": used,
        "used_percent": round((used / total) * 100, 1),
    }


def parse_proc_stat_cpu(text: str) -> dict[str, int]:
    for line in text.splitlines():
        if line.startswith("cpu "):
            parts = [int(value) for value in line.split()[1:]]
            idle = parts[3] + parts[4]
            return {"total": sum(parts), "idle": idle}
    raise ValueError("/proc/stat text did not contain aggregate cpu line")


def cpu_usage_percent(before: dict[str, int], after: dict[str, int]) -> float:
    total_delta = after["total"] - before["total"]
    idle_delta = after["idle"] - before["idle"]
    if total_delta <= 0:
        return 0.0
    return round(((total_delta - idle_delta) / total_delta) * 100, 1)


def parse_hwmon_sensors(device: str, files: dict[str, str]) -> list[dict[str, str | float]]:
    sensors: list[dict[str, str | float]] = []
    for name in sorted(files, key=_hwmon_sort_key):
        sensor = parse_hwmon_sensor(device, name, files)
        if sensor is not None:
            sensors.append(sensor)
    return sensors


def parse_hwmon_temperatures(device: str, files: dict[str, str]) -> list[dict[str, str | float]]:
    return [sensor for sensor in parse_hwmon_sensors(device, files) if sensor["category"] == "temperature"]


def parse_hwmon_temperature(device: str, files: dict[str, str]) -> dict[str, str | float]:
    return parse_hwmon_temperatures(device, files)[0]


def parse_hwmon_sensor(device: str, name: str, files: dict[str, str]) -> dict[str, str | float] | None:
    spec = _sensor_spec_for_name(name)
    if spec is None:
        return None

    sensor_name = name.removesuffix(spec.suffix) if spec.suffix else name
    index = sensor_name.removeprefix(spec.prefix)
    label = files.get(f"{spec.prefix}{index}_label", sensor_name).strip()
    raw_value = float(files[name].strip())
    value = raw_value / spec.scale
    if spec.scale != 1:
        value = round(value, 6)
    return {
        "id": f"hwmon.{device}.{sensor_name}",
        "label": label,
        "category": spec.category,
        "device": device,
        "value": value,
        "unit": spec.unit,
    }


def _sensor_spec_for_name(name: str) -> HwmonSensorSpec | None:
    for spec in HWMON_SENSOR_SPECS:
        if spec.suffix:
            if re.fullmatch(rf"{spec.prefix}\d+{re.escape(spec.suffix)}", name):
                return spec
        elif re.fullmatch(rf"{spec.prefix}\d+", name):
            return spec
    return None


def _hwmon_sort_key(name: str) -> tuple[int, int, str]:
    spec = _sensor_spec_for_name(name)
    if spec is None:
        return (len(HWMON_SENSOR_SPECS), 0, name)
    sensor_name = name.removesuffix(spec.suffix) if spec.suffix else name
    index_text = sensor_name.removeprefix(spec.prefix)
    return (HWMON_SENSOR_SPECS.index(spec), int(index_text), name)
