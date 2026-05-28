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


def test_web_app_selects_updates_moves_and_resizes_layout_widgets():
    script = f"""
{WEB_APP_JS}
const template = {{
  widgets: [
    {{id: 'widget.cpu', x: 10, y: 20, width: 180, height: 90, locked: false}},
    {{id: 'widget.locked', x: 1, y: 2, width: 100, height: 50, locked: true}},
  ]
}};
selectLayoutWidget(template, 'widget.cpu');
moveLayoutWidget(template, 'widget.cpu', 35, 45);
resizeLayoutWidget(template, 'widget.cpu', 220, 110);
moveLayoutWidget(template, 'widget.locked', 99, 99);
console.log(JSON.stringify({{
  selected: template.selected_widget_id,
  moved: template.widgets[0],
  locked: template.widgets[1],
}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["selected"] == "widget.cpu"
    assert result["moved"]["x"] == 35
    assert result["moved"]["y"] == 45
    assert result["moved"]["width"] == 220
    assert result["moved"]["height"] == 110
    assert result["locked"]["x"] == 1
    assert result["locked"]["y"] == 2


def test_web_app_updates_selected_widget_instead_of_first_widget():
    script = f"""
{WEB_APP_JS}
const template = {{
  selected_widget_id: 'widget.gpu',
  widgets: [
    {{id: 'widget.cpu', label: 'CPU', font_family: 'Inter', label_size: 12, value_size: 36, locked: false}},
    {{id: 'widget.gpu', label: 'GPU', font_family: 'Inter', label_size: 14, value_size: 40, locked: false}},
  ]
}};
updateSelectedWidgetDesign(template, {{label: 'Gaming GPU', value_size: 52, locked: true}});
console.log(JSON.stringify(template.widgets));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    widgets = json.loads(output)

    assert widgets[0]["label"] == "CPU"
    assert widgets[0]["value_size"] == 36
    assert widgets[1]["label"] == "Gaming GPU"
    assert widgets[1]["value_size"] == 52
    assert widgets[1]["locked"] is True


def test_web_app_drags_widget_by_delta_with_canvas_bounds_and_locking():
    script = f"""
{WEB_APP_JS}
const template = {{
  panel: {{width: 300, height: 200}},
  widgets: [
    {{id: 'widget.cpu', x: 40, y: 50, width: 100, height: 80, locked: false}},
    {{id: 'widget.locked', x: 20, y: 30, width: 80, height: 60, locked: true}},
  ]
}};
dragLayoutWidgetBy(template, 'widget.cpu', 500, -100);
dragLayoutWidgetBy(template, 'widget.locked', 100, 100);
console.log(JSON.stringify(template.widgets));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    widgets = json.loads(output)

    assert widgets[0]["x"] == 200
    assert widgets[0]["y"] == 0
    assert widgets[1]["x"] == 20
    assert widgets[1]["y"] == 30


def test_web_app_resizes_widget_by_delta_with_minimum_and_canvas_bounds():
    script = f"""
{WEB_APP_JS}
const template = {{
  panel: {{width: 320, height: 220}},
  widgets: [{{id: 'widget.cpu', x: 100, y: 60, width: 100, height: 80, locked: false}}]
}};
resizeLayoutWidgetBy(template, 'widget.cpu', -500, -500);
const small = JSON.parse(JSON.stringify(template.widgets[0]));
resizeLayoutWidgetBy(template, 'widget.cpu', 500, 500);
console.log(JSON.stringify({{small, large: template.widgets[0]}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["small"]["width"] == 80
    assert result["small"]["height"] == 48
    assert result["large"]["width"] == 220
    assert result["large"]["height"] == 160


def test_web_app_autosaves_template_after_editor_mutation():
    script = f"""
{WEB_APP_JS}
global.localStorage = {{
  data: {{}},
  setItem(key, value) {{ this.data[key] = value; }},
  getItem(key) {{ return this.data[key] || null; }},
}};
dashboardTemplate = {{
  panel: {{width: 300, height: 200}},
  selected_widget_id: 'widget.cpu',
  widgets: [{{id: 'widget.cpu', label: 'CPU', x: 0, y: 0, width: 100, height: 80, locked: false}}]
}};
applyEditorMutation(() => dragLayoutWidgetBy(dashboardTemplate, 'widget.cpu', 25, 35));
console.log(JSON.stringify(loadCustomTemplate()));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    template = json.loads(output)

    assert template["widgets"][0]["x"] == 25
    assert template["widgets"][0]["y"] == 35


def test_web_app_saves_and_loads_custom_template_from_browser_storage():
    script = f"""
{WEB_APP_JS}
global.localStorage = {{
  data: {{}},
  setItem(key, value) {{ this.data[key] = value; }},
  getItem(key) {{ return this.data[key] || null; }},
}};
const template = {{schema_version: 1, title: 'Custom', widgets: [{{id: 'widget.cpu'}}]}};
saveCustomTemplate(template);
console.log(JSON.stringify(loadCustomTemplate()));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)

    assert json.loads(output)["title"] == "Custom"


def test_web_app_updates_selected_widget_sensor_binding():
    script = f"""
{WEB_APP_JS}
const template = {{
  selected_widget_id: 'widget.gpu',
  widgets: [
    {{id: 'widget.cpu', sensor_id: 'cpu.total.used_percent', label: 'CPU'}},
    {{id: 'widget.gpu', sensor_id: 'gpu.nvidia.0.temperature', label: 'GPU'}},
  ]
}};
updateSelectedWidgetDesign(template, {{sensor_id: 'gpu.nvidia.0.power_watts'}});
console.log(JSON.stringify(template.widgets));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    widgets = json.loads(output)

    assert widgets[0]["sensor_id"] == "cpu.total.used_percent"
    assert widgets[1]["sensor_id"] == "gpu.nvidia.0.power_watts"


def test_web_app_builds_sensor_options_for_selected_widget_dropdown():
    script = f"""
{WEB_APP_JS}
const sensors = [
  {{id: 'cpu.total.used_percent', label: 'CPU Used', category: 'cpu', device: 'CPU', unit: '%'}},
  {{id: 'memory.ram.used_percent', label: 'RAM Used', category: 'memory', device: 'System Memory', unit: '%'}},
];
console.log(JSON.stringify(sensorBindingOptionsHtml(sensors, 'memory.ram.used_percent')));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    html = json.loads(output)

    assert 'value="cpu.total.used_percent"' in html
    assert 'value="memory.ram.used_percent" selected' in html
    assert 'memory: System Memory — RAM Used (%)' in html


def test_web_app_duplicates_selected_widget_with_new_id_and_offset():
    script = f"""
{WEB_APP_JS}
const template = {{
  selected_widget_id: 'widget.cpu',
  widgets: [{{id: 'widget.cpu', label: 'CPU', x: 10, y: 20, width: 100, height: 80, locked: false}}]
}};
const duplicate = duplicateSelectedWidget(template);
console.log(JSON.stringify({{duplicate, template}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["duplicate"]["id"] == "widget.cpu.copy1"
    assert result["duplicate"]["label"] == "CPU Copy"
    assert result["duplicate"]["x"] == 34
    assert result["duplicate"]["y"] == 44
    assert result["template"]["selected_widget_id"] == "widget.cpu.copy1"
    assert len(result["template"]["widgets"]) == 2


def test_web_app_deletes_selected_widget_and_selects_neighbor():
    script = f"""
{WEB_APP_JS}
const template = {{
  selected_widget_id: 'widget.gpu',
  widgets: [
    {{id: 'widget.cpu', label: 'CPU'}},
    {{id: 'widget.gpu', label: 'GPU'}},
    {{id: 'widget.ram', label: 'RAM'}},
  ]
}};
deleteSelectedWidget(template);
console.log(JSON.stringify(template));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    template = json.loads(output)

    assert [widget["id"] for widget in template["widgets"]] == ["widget.cpu", "widget.ram"]
    assert template["selected_widget_id"] == "widget.ram"


def test_web_app_updates_panel_background_color():
    script = f"""
{WEB_APP_JS}
const template = {{panel: {{width: 800, height: 480, background: '#111827'}}}};
updatePanelAppearance(template, '#ff00aa');
console.log(JSON.stringify({{panel: template.panel, style: panelStyle(template)}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["panel"]["background"] == "#ff00aa"
    assert "background:#ff00aa;" in result["style"]


def test_home_page_contains_widget_actions_sensor_binding_and_background_controls():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "widget-sensor-id" in html
        assert "panel-background" in html
        assert "duplicate-widget-button" in html
        assert "delete-widget-button" in html
    finally:
        server.shutdown()


def test_home_page_contains_template_asset_and_import_export_controls():
    handler = make_handler(lambda: {"schema_version": 1, "updated_at": "now", "sensors": []})
    server, base_url = _serve_once(handler)
    try:
        with urllib.request.urlopen(base_url) as response:
            html = response.read().decode()
        assert "template-export-button" in html
        assert "template-import-file" in html
        assert "asset-upload-file" in html
        assert "widget-icon-asset" in html
        assert "sensor-mapping-panel" in html
    finally:
        server.shutdown()



def test_web_app_exports_template_as_downloadable_json_blob():
    script = f"""
{WEB_APP_JS}
global.URL = {{ createObjectURL(blob) {{ global.createdBlob = blob; return 'blob:template'; }} }};
global.Blob = class {{ constructor(parts, options) {{ this.parts = parts; this.options = options; }} }};
const link = {{ clickCalled: false, click() {{ this.clickCalled = true; }} }};
global.document = {{ createElement(tag) {{ return link; }}, body: {{ appendChild() {{}}, removeChild() {{}} }} }};
const result = exportTemplateDownload({{title: 'Custom', widgets: []}});
console.log(JSON.stringify({{
  href: result.href,
  download: result.download,
  clicked: result.clickCalled,
  blobType: global.createdBlob.options.type,
  body: global.createdBlob.parts[0],
}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["href"] == "blob:template"
    assert result["download"] == "opensensorpanel-template.json"
    assert result["clicked"] is True
    assert result["blobType"] == "application/json"
    assert json.loads(result["body"])["title"] == "Custom"


def test_web_app_imports_template_json_text_and_saves_it():
    script = f"""
{WEB_APP_JS}
global.localStorage = {{
  data: {{}},
  setItem(key, value) {{ this.data[key] = value; }},
  getItem(key) {{ return this.data[key] || null; }},
}};
const imported = importTemplateJsonText('{{"schema_version":1,"title":"Imported","hero_sensor_ids":[],"groups":[],"assets":[],"widgets":[]}}');
console.log(JSON.stringify({{imported, saved: loadCustomTemplate()}}));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    result = json.loads(output)

    assert result["imported"]["title"] == "Imported"
    assert result["saved"]["title"] == "Imported"


def test_web_app_builds_asset_options_for_icon_selector():
    script = f"""
{WEB_APP_JS}
const template = {{assets: [
  {{id: 'asset.logo', type: 'logo', path: 'assets/logo.svg'}},
  {{id: 'asset.bg', type: 'background', path: 'assets/bg.png'}},
  {{id: 'asset.icon.cpu', type: 'icon', path: 'assets/cpu.svg'}},
]}};
console.log(JSON.stringify(assetOptionsHtml(template)));
"""

    output = subprocess.check_output(["node", "-e", script], text=True)
    html = json.loads(output)

    assert 'value="asset.logo"' in html
    assert 'value="asset.icon.cpu"' in html
    assert 'asset.bg' not in html
