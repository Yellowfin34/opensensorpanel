from opensensorpanel.linux_sensors import (
    cpu_usage_percent,
    parse_hwmon_sensor,
    parse_hwmon_sensors,
    parse_hwmon_temperature,
    parse_meminfo,
    parse_proc_stat_cpu,
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


def test_parse_hwmon_sensor_converts_common_hwmon_units():
    files = {
        "fan1_input": "1420\n",
        "fan1_label": "CPU Fan\n",
        "in2_input": "12050\n",
        "in2_label": "+12V\n",
        "power3_input": "65400000\n",
        "power3_label": "CPU Package\n",
        "curr4_input": "12500\n",
        "curr4_label": "GPU Current\n",
        "pwm5": "128\n",
        "freq6_input": "3200000000\n",
        "energy7_input": "123456789\n",
        "humidity8_input": "45300\n",
    }

    assert parse_hwmon_sensor("nct6799", "fan1_input", files) == {
        "id": "hwmon.nct6799.fan1",
        "label": "CPU Fan",
        "category": "fan",
        "device": "nct6799",
        "value": 1420.0,
        "unit": "RPM",
    }
    assert parse_hwmon_sensor("nct6799", "in2_input", files) == {
        "id": "hwmon.nct6799.in2",
        "label": "+12V",
        "category": "voltage",
        "device": "nct6799",
        "value": 12.05,
        "unit": "V",
    }
    assert parse_hwmon_sensor("nct6799", "power3_input", files) == {
        "id": "hwmon.nct6799.power3",
        "label": "CPU Package",
        "category": "power",
        "device": "nct6799",
        "value": 65.4,
        "unit": "W",
    }
    assert parse_hwmon_sensor("nct6799", "curr4_input", files) == {
        "id": "hwmon.nct6799.curr4",
        "label": "GPU Current",
        "category": "current",
        "device": "nct6799",
        "value": 12.5,
        "unit": "A",
    }
    assert parse_hwmon_sensor("nct6799", "pwm5", files) == {
        "id": "hwmon.nct6799.pwm5",
        "label": "pwm5",
        "category": "pwm",
        "device": "nct6799",
        "value": 128.0,
        "unit": "PWM",
    }
    assert parse_hwmon_sensor("nct6799", "freq6_input", files) == {
        "id": "hwmon.nct6799.freq6",
        "label": "freq6",
        "category": "frequency",
        "device": "nct6799",
        "value": 3200000000.0,
        "unit": "Hz",
    }
    assert parse_hwmon_sensor("nct6799", "energy7_input", files) == {
        "id": "hwmon.nct6799.energy7",
        "label": "energy7",
        "category": "energy",
        "device": "nct6799",
        "value": 123.456789,
        "unit": "J",
    }
    assert parse_hwmon_sensor("nct6799", "humidity8_input", files) == {
        "id": "hwmon.nct6799.humidity8",
        "label": "humidity8",
        "category": "humidity",
        "device": "nct6799",
        "value": 45.3,
        "unit": "%",
    }


def test_parse_hwmon_sensors_returns_all_supported_sensor_inputs():
    files = {
        "name": "nct6799\n",
        "temp1_input": "48500\n",
        "fan2_input": "1420\n",
        "in3_input": "3300\n",
        "power4_input": "65400000\n",
        "curr5_input": "12500\n",
        "pwm6": "128\n",
        "temp1_max": "90000\n",
        "fan2_min": "500\n",
    }

    sensors = parse_hwmon_sensors("nct6799", files)

    assert [sensor["id"] for sensor in sensors] == [
        "hwmon.nct6799.temp1",
        "hwmon.nct6799.fan2",
        "hwmon.nct6799.in3",
        "hwmon.nct6799.power4",
        "hwmon.nct6799.curr5",
        "hwmon.nct6799.pwm6",
    ]
