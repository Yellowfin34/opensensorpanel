from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collectors import (
    collect_cpu_usage,
    collect_hwmon_temperatures,
    collect_memory_snapshot,
    collect_nvidia_gpu_snapshot,
)


def collect_snapshot(
    *,
    meminfo_path: Path = Path("/proc/meminfo"),
    hwmon_root: Path = Path("/sys/class/hwmon"),
) -> dict[str, Any]:
    sensors = []
    sensors.extend(collect_memory_snapshot(meminfo_path))
    sensors.extend(collect_cpu_usage())
    sensors.extend(collect_hwmon_temperatures(hwmon_root))
    sensors.extend(collect_nvidia_gpu_snapshot())
    return {
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sensors": sensors,
    }
