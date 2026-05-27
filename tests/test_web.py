import json
import subprocess
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from opensensorpanel.web import WEB_APP_JS, make_handler


def _serve_once(handler_class):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_api_snapshot_returns_json():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(f"{base_url}/api/snapshot") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/json"
            assert json.loads(response.read()) == {"schema_version": 1, "updated_at": "now", "sensors": []}
    finally:
        server.shutdown()


def test_api_sensors_returns_available_sensor_metadata_without_live_values():
    handler = make_handler(
        lambda: {
            "schema_version": 1,
            "updated_at": "now",
            "sensors": [
                {
                    "id": "cpu.total.used_percent",
                    "label": "CPU Used",
                    "category": "cpu",
                    "device": "CPU",
                    "value": 12.3,
                    "unit": "%",
                }
            ],
        }
    )
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(f"{base_url}/api/sensors") as response:
            assert response.status == 200
            assert response.headers["Content-Type"] == "application/json"
            assert json.loads(response.read()) == {
                "schema_version": 1,
                "sensors": [
                    {
                        "id": "cpu.total.used_percent",
                        "label": "CPU Used",
                        "category": "cpu",
                        "device": "CPU",
                        "unit": "%",
                    }
                ],
            }
    finally:
        server.shutdown()


def test_home_page_contains_panel_shell():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "OpenSensorPanel" in html
        assert "/api/snapshot" in html
    finally:
        server.shutdown()


def test_web_app_formats_sensor_values_for_display():
    script = f"""
{WEB_APP_JS}
const examples = [
  formatSensorValue({{value: 5368709120, unit: 'B'}}),
  formatSensorValue({{value: 43, unit: 'C'}}),
  formatSensorValue({{value: 16.3, unit: 'W'}}),
  formatSensorValue({{value: 62.5, unit: '%'}}),
  formatSensorValue({{value: 5.12, unit: 'GB'}}),
];
console.log(JSON.stringify(examples));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == ["5.37 GB", "43 °C", "16.3 W", "62.5%", "5.12 GB"]


def test_web_app_filters_visible_sensors_from_saved_selection():
    script = f"""
{WEB_APP_JS}
const sensors = [
  {{id: 'cpu.total.used_percent'}},
  {{id: 'memory.ram.used_gb'}},
  {{id: 'gpu.nvidia.0.temperature'}},
];
const selected = ['memory.ram.used_gb', 'gpu.nvidia.0.temperature'];
console.log(JSON.stringify(selectVisibleSensors(sensors, selected).map(sensor => sensor.id)));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == ['memory.ram.used_gb', 'gpu.nvidia.0.temperature']


def test_web_app_groups_sensors_for_dashboard_sections():
    script = f"""
{WEB_APP_JS}
const sensors = [
  {{id: 'gpu.nvidia.0.temperature', category: 'temperature'}},
  {{id: 'cpu.total.used_percent', category: 'cpu'}},
  {{id: 'gpu.nvidia.0.power_watts', category: 'power'}},
  {{id: 'memory.ram.used_percent', category: 'memory'}},
];
const groups = groupSensorsByCategory(sensors).map(group => [group.label, group.sensors.map(sensor => sensor.id)]);
console.log(JSON.stringify(groups));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [
        ["CPU", ["cpu.total.used_percent"]],
        ["Memory", ["memory.ram.used_percent"]],
        ["Temperatures", ["gpu.nvidia.0.temperature"]],
        ["Power", ["gpu.nvidia.0.power_watts"]],
    ]


def test_web_app_picks_hero_stats_for_top_bar():
    script = f"""
{WEB_APP_JS}
const sensors = [
  {{id: 'memory.ram.used_percent', label: 'RAM Used'}},
  {{id: 'gpu.nvidia.0.temperature', label: 'GPU Temperature'}},
  {{id: 'gpu.nvidia.0.power_watts', label: 'GPU Power'}},
  {{id: 'cpu.total.used_percent', label: 'CPU Used'}},
];
console.log(JSON.stringify(pickHeroSensors(sensors).map(sensor => sensor.id)));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [
        'cpu.total.used_percent',
        'memory.ram.used_percent',
        'gpu.nvidia.0.temperature',
        'gpu.nvidia.0.power_watts',
    ]


def test_home_page_contains_polished_dashboard_shell():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "hero-stats" in html
        assert "sensor-groups" in html
        assert "fullscreen" in html.lower()
    finally:
        server.shutdown()


def test_home_page_contains_sensor_picker_shell():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "Available Sensors" in html
        assert "selected-sensors" in html
    finally:
        server.shutdown()
