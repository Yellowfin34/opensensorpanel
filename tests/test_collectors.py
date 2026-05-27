from pathlib import Path

from opensensorpanel.collectors import (
    collect_cpu_usage,
    collect_hwmon_temperatures,
    collect_memory_snapshot,
    collect_nvidia_gpu_snapshot,
)


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


def test_collect_cpu_usage_samples_proc_stat_twice(tmp_path: Path):
    stat = tmp_path / "stat"
    stat.write_text("cpu  100 0 0 900 0 0 0 0 0 0\n")

    def after_first_read() -> None:
        stat.write_text("cpu  150 0 50 1000 0 0 0 0 0 0\n")

    sensors = collect_cpu_usage(stat_path=stat, sample_interval_seconds=0, after_first_read=after_first_read)

    assert sensors == [
        {
            "id": "cpu.total.used_percent",
            "label": "CPU Used",
            "category": "cpu",
            "device": "CPU",
            "value": 50.0,
            "unit": "%",
        }
    ]


def test_collect_nvidia_gpu_snapshot_parses_nvidia_smi_csv():
    def fake_runner(command: list[str]) -> str:
        assert command[0] == "nvidia-smi"
        return "NVIDIA GeForce RTX 5090, 17, 125, 32607, 43, 16.30\n"

    sensors = collect_nvidia_gpu_snapshot(run_command=fake_runner)

    assert sensors == [
        {
            "id": "gpu.nvidia.0.utilization_percent",
            "label": "GPU Used",
            "category": "gpu",
            "device": "NVIDIA GeForce RTX 5090",
            "value": 17.0,
            "unit": "%",
        },
        {
            "id": "gpu.nvidia.0.memory_used_bytes",
            "label": "GPU Memory Used",
            "category": "gpu",
            "device": "NVIDIA GeForce RTX 5090",
            "value": 125 * 1024 * 1024,
            "unit": "B",
        },
        {
            "id": "gpu.nvidia.0.memory_used_percent",
            "label": "GPU Memory Used",
            "category": "gpu",
            "device": "NVIDIA GeForce RTX 5090",
            "value": 0.4,
            "unit": "%",
        },
        {
            "id": "gpu.nvidia.0.temperature",
            "label": "GPU Temperature",
            "category": "temperature",
            "device": "NVIDIA GeForce RTX 5090",
            "value": 43.0,
            "unit": "C",
        },
        {
            "id": "gpu.nvidia.0.power_watts",
            "label": "GPU Power",
            "category": "power",
            "device": "NVIDIA GeForce RTX 5090",
            "value": 16.3,
            "unit": "W",
        },
    ]
