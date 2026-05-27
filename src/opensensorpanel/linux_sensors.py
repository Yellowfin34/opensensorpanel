from __future__ import annotations


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


def parse_hwmon_temperatures(device: str, files: dict[str, str]) -> list[dict[str, str | float]]:
    sensors: list[dict[str, str | float]] = []
    input_names = [name for name in sorted(files) if name.startswith("temp") and name.endswith("_input")]
    for input_name in input_names:
        index = input_name.removeprefix("temp").removesuffix("_input")
        label = files.get(f"temp{index}_label", f"temp{index}").strip()
        value_c = int(files[input_name].strip()) / 1000
        sensors.append(
            {
                "id": f"hwmon.{device}.temp{index}",
                "label": label,
                "category": "temperature",
                "device": device,
                "value": value_c,
                "unit": "C",
            }
        )
    return sensors


def parse_hwmon_temperature(device: str, files: dict[str, str]) -> dict[str, str | float]:
    return parse_hwmon_temperatures(device, files)[0]
