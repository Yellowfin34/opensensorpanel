from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from .linux_sensors import cpu_usage_percent, parse_hwmon_sensors, parse_meminfo, parse_proc_stat_cpu

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
            "id": "memory.ram.used_gb",
            "label": "RAM Used",
            "category": "memory",
            "device": "System Memory",
            "value": round(float(memory["used_bytes"]) / 1_000_000_000, 2),
            "unit": "GB",
        },
    ]


def collect_cpu_usage(
    stat_path: Path = Path("/proc/stat"),
    *,
    sample_interval_seconds: float = 0.1,
    after_first_read: Callable[[], None] | None = None,
) -> list[Sensor]:
    before = parse_proc_stat_cpu(stat_path.read_text())
    if after_first_read is not None:
        after_first_read()
    elif sample_interval_seconds > 0:
        time.sleep(sample_interval_seconds)
    after = parse_proc_stat_cpu(stat_path.read_text())
    return [
        {
            "id": "cpu.total.used_percent",
            "label": "CPU Used",
            "category": "cpu",
            "device": "CPU",
            "value": cpu_usage_percent(before, after),
            "unit": "%",
        }
    ]


def collect_hwmon_sensors(hwmon_root: Path = Path("/sys/class/hwmon")) -> list[Sensor]:
    sensors: list[Sensor] = []
    if not hwmon_root.exists():
        return sensors

    for device_path in sorted(path for path in hwmon_root.iterdir() if path.is_dir()):
        files = _read_hwmon_files(device_path)
        device_name = files.get("name", device_path.name).strip()
        for sensor in parse_hwmon_sensors(device_name, files):
            sensor_id = str(sensor["id"])
            sensor["id"] = sensor_id.replace("hwmon.", f"hwmon.{device_path.name}.", 1)
            sensors.append(sensor)
    return sensors


def collect_hwmon_temperatures(hwmon_root: Path = Path("/sys/class/hwmon")) -> list[Sensor]:
    return [sensor for sensor in collect_hwmon_sensors(hwmon_root) if sensor["category"] == "temperature"]


def _read_hwmon_files(device_path: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for child in sorted(device_path.iterdir()):
        if child.is_file() and (child.name == "name" or _is_hwmon_sensor_file(child.name)):
            try:
                files[child.name] = child.read_text()
            except OSError:
                continue
    return files


def _is_hwmon_sensor_file(name: str) -> bool:
    prefixes = ("temp", "fan", "in", "power", "curr", "energy", "humidity", "freq", "pwm")
    return name.startswith(prefixes)


def collect_nvidia_gpu_snapshot(
    *,
    run_command: Callable[[list[str]], str] | None = None,
) -> list[Sensor]:
    runner = run_command or _run_command
    command = [
        "nvidia-smi",
        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        output = runner(command)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    sensors: list[Sensor] = []
    for index, line in enumerate(output.splitlines()):
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 6:
            continue
        name, gpu_util, memory_used_mib, memory_total_mib, temperature_c, power_watts = parts
        used_mib = float(memory_used_mib)
        total_mib = float(memory_total_mib)
        device = name
        sensors.extend(
            [
                {
                    "id": f"gpu.nvidia.{index}.utilization_percent",
                    "label": "GPU Used",
                    "category": "gpu",
                    "device": device,
                    "value": float(gpu_util),
                    "unit": "%",
                },
                {
                    "id": f"gpu.nvidia.{index}.memory_used_bytes",
                    "label": "GPU Memory Used",
                    "category": "gpu",
                    "device": device,
                    "value": int(used_mib * 1024 * 1024),
                    "unit": "B",
                },
                {
                    "id": f"gpu.nvidia.{index}.memory_used_percent",
                    "label": "GPU Memory Used",
                    "category": "gpu",
                    "device": device,
                    "value": round((used_mib / total_mib) * 100, 1) if total_mib else 0.0,
                    "unit": "%",
                },
                {
                    "id": f"gpu.nvidia.{index}.temperature",
                    "label": "GPU Temperature",
                    "category": "temperature",
                    "device": device,
                    "value": float(temperature_c),
                    "unit": "C",
                },
                {
                    "id": f"gpu.nvidia.{index}.power_watts",
                    "label": "GPU Power",
                    "category": "power",
                    "device": device,
                    "value": float(power_watts),
                    "unit": "W",
                },
            ]
        )
    return sensors


def _run_command(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
