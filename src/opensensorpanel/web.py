from __future__ import annotations

import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .snapshot import collect_snapshot

SnapshotCollector = Callable[[], dict[str, Any]]


def available_sensors(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": snapshot["schema_version"],
        "sensors": [
            {
                "id": sensor["id"],
                "label": sensor["label"],
                "category": sensor["category"],
                "device": sensor["device"],
                "unit": sensor["unit"],
            }
            for sensor in snapshot["sensors"]
        ],
    }


WEB_APP_JS = """
const SELECTED_SENSOR_IDS_KEY = 'opensensorpanel.selectedSensorIds';

function formatNumber(value) {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return String(Number(value.toFixed(2)));
}

function formatSensorValue(sensor) {
  const value = Number(sensor.value);
  if (sensor.unit === 'B') {
    return `${formatNumber(value / 1_000_000_000)} GB`;
  }
  if (sensor.unit === 'C') {
    return `${formatNumber(value)} °C`;
  }
  if (sensor.unit === '%') {
    return `${formatNumber(value)}%`;
  }
  if (sensor.unit) {
    return `${formatNumber(value)} ${sensor.unit}`;
  }
  return formatNumber(value);
}

function loadSelectedSensorIds() {
  if (typeof localStorage === 'undefined') {
    return [];
  }
  try {
    const saved = JSON.parse(localStorage.getItem(SELECTED_SENSOR_IDS_KEY) || '[]');
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function saveSelectedSensorIds(sensorIds) {
  if (typeof localStorage === 'undefined') {
    return;
  }
  localStorage.setItem(SELECTED_SENSOR_IDS_KEY, JSON.stringify(sensorIds));
}

function selectVisibleSensors(sensors, selectedSensorIds) {
  if (!selectedSensorIds.length) {
    return sensors;
  }
  const selected = new Set(selectedSensorIds);
  return sensors.filter(sensor => selected.has(sensor.id));
}

function renderSensorCards(sensors) {
  const visibleSensors = selectVisibleSensors(sensors, loadSelectedSensorIds());
  document.querySelector('#sensors').innerHTML = visibleSensors.map(sensor => `
    <article class="card">
      <div class="label">${sensor.label}</div>
      <div class="value">${formatSensorValue(sensor)}</div>
      <div class="device">${sensor.device}</div>
    </article>
  `).join('');
}

function sensorOptionLabel(sensor) {
  return `${sensor.category}: ${sensor.device} — ${sensor.label} (${sensor.unit})`;
}

function renderSensorPicker(sensors) {
  const selected = new Set(loadSelectedSensorIds());
  document.querySelector('#selected-sensors').innerHTML = sensors.map(sensor => `
    <label class="sensor-option">
      <input type="checkbox" value="${sensor.id}" ${selected.size === 0 || selected.has(sensor.id) ? 'checked' : ''}>
      <span>${sensorOptionLabel(sensor)}</span>
    </label>
  `).join('');
  document.querySelectorAll('#selected-sensors input').forEach(input => {
    input.addEventListener('change', () => {
      const selectedIds = [...document.querySelectorAll('#selected-sensors input:checked')].map(checkbox => checkbox.value);
      saveSelectedSensorIds(selectedIds);
      refresh();
    });
  });
}

async function refresh() {
  const response = await fetch('/api/snapshot');
  const snapshot = await response.json();
  renderSensorCards(snapshot.sensors);
}

async function loadSensorPicker() {
  const response = await fetch('/api/sensors');
  const data = await response.json();
  renderSensorPicker(data.sensors);
}

async function startOpenSensorPanel() {
  await loadSensorPicker();
  await refresh();
  setInterval(refresh, 2000);
}

if (typeof window !== 'undefined') {
  startOpenSensorPanel();
}
""".strip()

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
    h2 { margin-top: 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
    .card { background: linear-gradient(135deg, #121827, #1d2638); border: 1px solid #2a3750; border-radius: 18px; padding: 1rem; box-shadow: 0 14px 30px #0008; }
    .label { color: #94a3b8; font-size: .9rem; }
    .value { font-size: 2rem; font-weight: 800; margin-top: .25rem; }
    .device { color: #cbd5e1; font-size: .85rem; margin-top: .25rem; }
    .picker { margin-top: 1rem; background: #0f1724; border: 1px solid #263449; border-radius: 18px; padding: 1rem; }
    .sensor-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: .5rem; }
    .sensor-option { display: flex; gap: .5rem; align-items: center; color: #dbeafe; font-size: .9rem; }
    .hint { color: #94a3b8; font-size: .9rem; }
  </style>
</head>
<body>
  <main>
    <h1>OpenSensorPanel</h1>
    <p>Live Linux hardware sensors from <code>/api/snapshot</code></p>
    <section id="sensors" class="grid"></section>
    <section class="picker" aria-labelledby="available-sensors-heading">
      <h2 id="available-sensors-heading">Available Sensors</h2>
      <p class="hint">Pick the sensors to show on the dashboard. Your choices are saved in this browser.</p>
      <div id="selected-sensors" class="sensor-options"></div>
    </section>
  </main>
  <script>
{web_app_js}
  </script>
</body>
</html>
""".replace("{web_app_js}", WEB_APP_JS)


def make_handler(collector: SnapshotCollector = collect_snapshot) -> type[BaseHTTPRequestHandler]:
    class OpenSensorPanelHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/" or self.path == "/index.html":
                self._send_text(INDEX_HTML, "text/html; charset=utf-8")
                return
            if self.path == "/api/snapshot":
                self._send_json(collector())
                return
            if self.path == "/api/sensors":
                self._send_json(available_sensors(collector()))
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

        def _send_json(self, data: dict[str, Any]) -> None:
            body = json.dumps(data, sort_keys=True).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return OpenSensorPanelHandler


def serve(host: str = "127.0.0.1", port: int = 8766) -> None:
    server = ThreadingHTTPServer((host, port), make_handler())
    print(f"OpenSensorPanel web server listening on http://{host}:{port}")
    server.serve_forever()
