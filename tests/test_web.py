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
