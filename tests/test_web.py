import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from opensensorpanel.web import make_handler


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
