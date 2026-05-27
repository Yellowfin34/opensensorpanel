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


def test_api_template_returns_default_layout_template():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(f"{base_url}/api/template") as response:
            payload = json.loads(response.read())
        assert payload["schema_version"] == 1
        assert payload["hero_sensor_ids"][0] == "cpu.total.used_percent"
        assert {"category": "temperature", "label": "Temperatures"} in payload["groups"]
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
const template = {{
  groups: [
    {{category: 'power', label: 'Watts'}},
    {{category: 'cpu', label: 'Processor'}},
  ]
}};
const groups = groupSensorsByCategory(sensors, template).map(group => [group.label, group.sensors.map(sensor => sensor.id)]);
console.log(JSON.stringify(groups));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [
        ["Watts", ["gpu.nvidia.0.power_watts"]],
        ["Processor", ["cpu.total.used_percent"]],
        ["Other", ["gpu.nvidia.0.temperature", "memory.ram.used_percent"]],
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
const template = {{hero_sensor_ids: ['gpu.nvidia.0.power_watts', 'cpu.total.used_percent']}};
console.log(JSON.stringify(pickHeroSensors(sensors, template).map(sensor => sensor.id)));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [
        'gpu.nvidia.0.power_watts',
        'cpu.total.used_percent',
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


def test_web_app_builds_borderless_panel_style_from_template_size():
    script = f"""
{WEB_APP_JS}
const template = {{panel: {{width: 800, height: 480, borderless: true, background: '#111827'}}}};
console.log(panelStyle(template));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert output.strip() == "width:800px;height:480px;background:#111827;"


def test_web_app_renders_positioned_widget_with_custom_label_font_and_lock_state():
    script = f"""
{WEB_APP_JS}
const widget = {{
  id: 'widget.cpu.used', sensor_id: 'cpu.total.used_percent', label: 'Gaming CPU',
  x: 10, y: 20, width: 180, height: 90, font_family: 'Orbitron', label_size: 14, value_size: 42, locked: true,
}};
const sensor = {{id: 'cpu.total.used_percent', value: 55, unit: '%'}};
const html = layoutWidgetHtml(widget, sensor);
console.log(JSON.stringify([
  html.includes('data-widget-id="widget.cpu.used"'),
  html.includes('data-locked="true"'),
  html.includes('left:10px;top:20px;width:180px;height:90px;font-family:Orbitron;'),
  html.includes('font-size:14px'),
  html.includes('font-size:42px'),
  html.includes('Gaming CPU'),
]));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [True, True, True, True, True, True]


def test_web_app_renders_widget_icon_from_declared_template_asset():
    script = f"""
{WEB_APP_JS}
dashboardTemplate = {{
  assets: [{{id: 'asset.cpu.icon', type: 'icon', path: 'assets/cpu.svg', license: 'CC0', source: 'user'}}]
}};
const widget = {{
  id: 'widget.cpu.used', sensor_id: 'cpu.total.used_percent', label: 'Gaming CPU', icon_asset_id: 'asset.cpu.icon',
  x: 10, y: 20, width: 180, height: 90, font_family: 'Orbitron', label_size: 14, value_size: 42, locked: false,
}};
const sensor = {{id: 'cpu.total.used_percent', value: 55, unit: '%'}};
const html = layoutWidgetHtml(widget, sensor);
console.log(JSON.stringify([
  html.includes('<img'),
  html.includes('src="assets/cpu.svg"'),
  html.includes('alt="Gaming CPU icon"'),
]));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output) == [True, True, True]


def test_home_page_contains_layout_editor_controls():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "layout-canvas" in html
        assert "panel-width" in html
        assert "panel-height" in html
        assert "widget-label" in html
        assert "widget-font-family" in html
        assert "widget-locked" in html
    finally:
        server.shutdown()


def test_web_app_updates_panel_size_and_widget_design_in_template():
    script = f"""
{WEB_APP_JS}
const template = {{
  panel: {{width: 800, height: 480, borderless: true, background: '#111827'}},
  widgets: [{{id: 'widget.cpu.used', label: 'CPU', font_family: 'Inter', label_size: 12, value_size: 36, locked: false}}]
}};
updatePanelSize(template, 1280, 400);
updateWidgetDesign(template, 'widget.cpu.used', {{label: 'Gaming CPU', font_family: 'Orbitron', label_size: 16, value_size: 52, locked: true}});
console.log(JSON.stringify(template));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    template = json.loads(output)

    assert template["panel"]["width"] == 1280
    assert template["panel"]["height"] == 400
    assert template["widgets"][0]["label"] == "Gaming CPU"
    assert template["widgets"][0]["font_family"] == "Orbitron"
    assert template["widgets"][0]["label_size"] == 16
    assert template["widgets"][0]["value_size"] == 52
    assert template["widgets"][0]["locked"] is True


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
