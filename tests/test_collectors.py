from pathlib import Path

from opensensorpanel.collectors import collect_hwmon_temperatures, collect_memory_snapshot


def test_collect_memory_snapshot_reads_proc_meminfo(tmp_path: Path):
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal:       8000000 kB\n"
        "MemFree:        1000000 kB\n"
        "MemAvailable:  3000000 kB\n"
    )

    sensors = collect_memory_snapshot(meminfo)

    assert sensors == [
        {
            "id": "memory.ram.used_percent",
            "label": "RAM Used",
            "category": "memory",
            "device": "System Memory",
            "value": 62.5,
            "unit": "%",
        },
        {
            "id": "memory.ram.used_bytes",
            "label": "RAM Used Bytes",
            "category": "memory",
            "device": "System Memory",
            "value": 5000000 * 1024,
            "unit": "B",
        },
    ]


def test_collect_hwmon_temperatures_reads_each_hwmon_device(tmp_path: Path):
    hwmon0 = tmp_path / "hwmon0"
    hwmon0.mkdir()
    (hwmon0 / "name").write_text("k10temp\n")
    (hwmon0 / "temp1_label").write_text("CPU Package\n")
    (hwmon0 / "temp1_input").write_text("51000\n")

    hwmon1 = tmp_path / "hwmon1"
    hwmon1.mkdir()
    (hwmon1 / "name").write_text("nvme\n")
    (hwmon1 / "temp1_input").write_text("42000\n")

    sensors = collect_hwmon_temperatures(tmp_path)

    assert sensors == [
        {
            "id": "hwmon.hwmon0.k10temp.temp1",
            "label": "CPU Package",
            "category": "temperature",
            "device": "k10temp",
            "value": 51.0,
            "unit": "C",
        },
        {
            "id": "hwmon.hwmon1.nvme.temp1",
            "label": "temp1",
            "category": "temperature",
            "device": "nvme",
            "value": 42.0,
            "unit": "C",
        },
    ]


def test_collect_hwmon_temperatures_keeps_duplicate_device_names_unique(tmp_path: Path):
    for index, value in [(0, "42000\n"), (1, "43000\n")]:
        hwmon = tmp_path / f"hwmon{index}"
        hwmon.mkdir()
        (hwmon / "name").write_text("nvme\n")
        (hwmon / "temp1_input").write_text(value)

    sensors = collect_hwmon_temperatures(tmp_path)

    assert [sensor["id"] for sensor in sensors] == [
        "hwmon.hwmon0.nvme.temp1",
        "hwmon.hwmon1.nvme.temp1",
    ]
