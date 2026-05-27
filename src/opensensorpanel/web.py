from __future__ import annotations

import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .snapshot import collect_snapshot
from .templates import DEFAULT_TEMPLATE, validate_template

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
const DEFAULT_DASHBOARD_TEMPLATE = {
  schema_version: 1,
  title: 'OpenSensorPanel',
  hero_sensor_ids: [
    'cpu.total.used_percent',
    'memory.ram.used_percent',
    'gpu.nvidia.0.temperature',
    'gpu.nvidia.0.power_watts',
  ],
  groups: [
    {category: 'cpu', label: 'CPU'},
    {category: 'memory', label: 'Memory'},
    {category: 'gpu', label: 'GPU'},
    {category: 'temperature', label: 'Temperatures'},
    {category: 'fan', label: 'Fans'},
    {category: 'voltage', label: 'Voltages'},
    {category: 'power', label: 'Power'},
    {category: 'current', label: 'Current'},
    {category: 'energy', label: 'Energy'},
    {category: 'humidity', label: 'Humidity'},
    {category: 'frequency', label: 'Frequency'},
    {category: 'pwm', label: 'PWM'},
  ],
};
let dashboardTemplate = DEFAULT_DASHBOARD_TEMPLATE;

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

function pickHeroSensors(sensors, template = dashboardTemplate) {
  const heroSensorIds = template.hero_sensor_ids || [];
  const byId = new Map(sensors.map(sensor => [sensor.id, sensor]));
  return heroSensorIds.map(sensorId => byId.get(sensorId)).filter(Boolean);
}

function groupSensorsByCategory(sensors, template = dashboardTemplate) {
  const templateGroups = template.groups || [];
  const groups = [];
  for (const group of templateGroups) {
    const groupSensors = sensors.filter(sensor => sensor.category === group.category);
    if (groupSensors.length) {
      groups.push({category: group.category, label: group.label, sensors: groupSensors});
    }
  }
  const knownCategories = new Set(templateGroups.map(group => group.category));
  const otherSensors = sensors.filter(sensor => !knownCategories.has(sensor.category));
  if (otherSensors.length) {
    groups.push({category: 'other', label: 'Other', sensors: otherSensors});
  }
  return groups;
}

function sensorCardHtml(sensor, extraClass = '') {
  return `
    <article class="card ${extraClass}">
      <div class="label">${sensor.label}</div>
      <div class="value">${formatSensorValue(sensor)}</div>
      <div class="device">${sensor.device || ''}</div>
    </article>
  `;
}

function renderHeroStats(sensors) {
  const heroSensors = pickHeroSensors(sensors);
  document.querySelector('#hero-stats').innerHTML = heroSensors.map(sensor => sensorCardHtml(sensor, 'hero-card')).join('');
}

function renderGroupedCards(sensors) {
  const heroIds = new Set(pickHeroSensors(sensors).map(sensor => sensor.id));
  const nonHeroSensors = sensors.filter(sensor => !heroIds.has(sensor.id));
  const groups = groupSensorsByCategory(nonHeroSensors);
  document.querySelector('#sensor-groups').innerHTML = groups.map(group => `
    <section class="sensor-group" data-category="${group.category}">
      <h2>${group.label}</h2>
      <div class="grid">${group.sensors.map(sensor => sensorCardHtml(sensor)).join('')}</div>
    </section>
  `).join('');
}

function renderSensorCards(sensors) {
  const visibleSensors = selectVisibleSensors(sensors, loadSelectedSensorIds());
  renderHeroStats(visibleSensors);
  renderGroupedCards(visibleSensors);
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

function setupFullscreenButton() {
  document.querySelector('#fullscreen-button').addEventListener('click', async () => {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
      return;
    }
    await document.documentElement.requestFullscreen();
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

async function loadTemplate() {
  const response = await fetch('/api/template');
  dashboardTemplate = await response.json();
}

async function startOpenSensorPanel() {
  setupFullscreenButton();
  await loadTemplate();
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
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #080b12; color: #f4f7fb; }
    body { margin: 0; min-height: 100vh; background: radial-gradient(circle at 20% 0%, #1e3a8a55, transparent 32rem), #080b12; }
    main { max-width: 1280px; margin: 0 auto; padding: 2rem; }
    .top-bar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    h1 { margin: 0 0 .25rem; letter-spacing: -.04em; }
    h2 { margin: 2rem 0 .8rem; color: #dbeafe; }
    .subtitle { color: #94a3b8; margin: 0; }
    .button { background: #2563eb; color: white; border: 0; border-radius: 999px; padding: .65rem 1rem; font-weight: 700; cursor: pointer; box-shadow: 0 10px 24px #1d4ed855; }
    .button:hover { background: #3b82f6; }
    .hero-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; }
    .card { background: linear-gradient(135deg, #121827, #1d2638); border: 1px solid #2a3750; border-radius: 18px; padding: 1rem; box-shadow: 0 14px 30px #0008; }
    .hero-card { min-height: 7rem; border-color: #38bdf8aa; background: linear-gradient(135deg, #172554, #0f172a 65%); }
    .label { color: #94a3b8; font-size: .9rem; }
    .value { font-size: 2rem; font-weight: 800; margin-top: .25rem; }
    .hero-card .value { font-size: clamp(2.3rem, 5vw, 4.2rem); }
    .device { color: #cbd5e1; font-size: .85rem; margin-top: .25rem; }
    .sensor-group { margin-top: 1rem; }
    .picker { margin-top: 2rem; background: #0f1724; border: 1px solid #263449; border-radius: 18px; padding: 1rem; }
    .sensor-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: .5rem; }
    .sensor-option { display: flex; gap: .5rem; align-items: center; color: #dbeafe; font-size: .9rem; }
    .hint { color: #94a3b8; font-size: .9rem; }
    @media (display-mode: fullscreen), (max-width: 700px) {
      main { max-width: none; padding: 1rem; }
      .picker { display: none; }
      .top-bar { align-items: flex-start; }
    }
  </style>
</head>
<body>
  <main>
    <header class="top-bar">
      <div>
        <h1>OpenSensorPanel</h1>
        <p class="subtitle">Live Linux hardware sensors from <code>/api/snapshot</code></p>
      </div>
      <button id="fullscreen-button" class="button" type="button">Fullscreen</button>
    </header>
    <section id="hero-stats" class="hero-grid" aria-label="Hero stats"></section>
    <section id="sensor-groups" aria-label="Grouped sensors"></section>
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
            if self.path == "/api/template":
                self._send_json(validate_template(DEFAULT_TEMPLATE))
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
