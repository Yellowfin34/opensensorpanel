from opensensorpanel.linux_sensors import (
    cpu_usage_percent,
    parse_meminfo,
    parse_proc_stat_cpu,
    parse_hwmon_temperature,
)


def test_parse_meminfo_returns_used_and_total_bytes():
    meminfo = """
MemTotal:       16000000 kB
MemFree:         2000000 kB
MemAvailable:   6000000 kB
Buffers:          100000 kB
Cached:          3000000 kB
"""

    result = parse_meminfo(meminfo)

    assert result["total_bytes"] == 16000000 * 1024
    assert result["available_bytes"] == 6000000 * 1024
    assert result["used_bytes"] == 10000000 * 1024
    assert result["used_percent"] == 62.5


def test_parse_proc_stat_cpu_extracts_total_and_idle_jiffies():
    snapshot = "cpu  100 0 50 850 20 0 0 0 0 0\n"

    result = parse_proc_stat_cpu(snapshot)

    assert result == {"total": 1020, "idle": 870}


def test_cpu_usage_percent_between_two_snapshots():
    before = {"total": 1000, "idle": 800}
    after = {"total": 1200, "idle": 850}

    assert cpu_usage_percent(before, after) == 75.0


def test_parse_hwmon_temperature_converts_millicelsius_and_uses_label():
    files = {
        "temp1_input": "48500\n",
        "temp1_label": "CPU Package\n",
    }

    result = parse_hwmon_temperature("k10temp", files)

    assert result == {
        "id": "hwmon.k10temp.temp1",
        "label": "CPU Package",
        "category": "temperature",
        "device": "k10temp",
        "value": 48.5,
        "unit": "C",
    }
