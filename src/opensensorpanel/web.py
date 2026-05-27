from __future__ import annotations

import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .snapshot import collect_snapshot

SnapshotCollector = Callable[[], dict[str, Any]]

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenSensorPanel</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; background: #080b12; color: #f4f7fb; }
    body { margin: 0; padding: 2rem; }
    main { max-width: 1100px; margin: 0 auto; }
    h1 { margin-bottom: .25rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
    .card { background: linear-gradient(135deg, #121827, #1d2638); border: 1px solid #2a3750; border-radius: 18px; padding: 1rem; box-shadow: 0 14px 30px #0008; }
    .label { color: #94a3b8; font-size: .9rem; }
    .value { font-size: 2rem; font-weight: 800; margin-top: .25rem; }
    .device { color: #cbd5e1; font-size: .85rem; margin-top: .25rem; }
  </style>
</head>
<body>
  <main>
    <h1>OpenSensorPanel</h1>
    <p>Live Linux hardware sensors from <code>/api/snapshot</code></p>
    <section id="sensors" class="grid"></section>
  </main>
  <script>
    async function refresh() {
      const response = await fetch('/api/snapshot');
      const snapshot = await response.json();
      document.querySelector('#sensors').innerHTML = snapshot.sensors.map(sensor => `
        <article class="card">
          <div class="label">${sensor.label}</div>
          <div class="value">${sensor.value} ${sensor.unit}</div>
          <div class="device">${sensor.device}</div>
        </article>
      `).join('');
    }
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""


def make_handler(collector: SnapshotCollector = collect_snapshot) -> type[BaseHTTPRequestHandler]:
    class OpenSensorPanelHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/" or self.path == "/index.html":
                self._send_text(INDEX_HTML, "text/html; charset=utf-8")
                return
            if self.path == "/api/snapshot":
                body = json.dumps(collector(), sort_keys=True).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_text(self, text: str, content_type: str) -> None:
            body = text.encode()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return OpenSensorPanelHandler


def serve(host: str = "127.0.0.1", port: int = 8766) -> None:
    server = ThreadingHTTPServer((host, port), make_handler())
    print(f"OpenSensorPanel web server listening on http://{host}:{port}")
    server.serve_forever()
