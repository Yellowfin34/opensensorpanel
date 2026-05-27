import json
from pathlib import Path

from opensensorpanel.snapshot import collect_snapshot


def test_collect_snapshot_combines_memory_and_hwmon_sensors(tmp_path: Path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal:       4000000 kB\n"
        "MemAvailable:  1000000 kB\n"
    )
    hwmon_root = tmp_path / "hwmon"
    hwmon0 = hwmon_root / "hwmon0"
    hwmon0.mkdir(parents=True)
    (hwmon0 / "name").write_text("k10temp\n")
    (hwmon0 / "temp1_input").write_text("50000\n")

    snapshot = collect_snapshot(meminfo_path=meminfo, hwmon_root=hwmon_root)

    sensor_ids = [sensor["id"] for sensor in snapshot["sensors"]]
    assert snapshot["schema_version"] == 1
    assert "memory.ram.used_percent" in sensor_ids
    assert "hwmon.hwmon0.k10temp.temp1" in sensor_ids


def test_snapshot_is_json_serializable(tmp_path: Path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal: 1000 kB\nMemAvailable: 250 kB\n")
    hwmon_root = tmp_path / "hwmon"
    hwmon_root.mkdir()

    snapshot = collect_snapshot(meminfo_path=meminfo, hwmon_root=hwmon_root)

    assert json.loads(json.dumps(snapshot))["schema_version"] == 1
