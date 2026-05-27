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
const CUSTOM_TEMPLATE_KEY = 'opensensorpanel.customTemplate';
const DEFAULT_DASHBOARD_TEMPLATE = {
  schema_version: 1,
  title: 'OpenSensorPanel',
  panel: {width: 1024, height: 600, borderless: true, background: '#080b12'},
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
  assets: [
    {id: 'asset.logo.opensensorpanel', type: 'logo', path: 'assets/opensensorpanel-logo.svg', license: 'project-created', source: 'OpenSensorPanel project', redistributable: true},
  ],
  widgets: [
    {id: 'widget.cpu.used', sensor_id: 'cpu.total.used_percent', label: 'CPU', x: 32, y: 32, width: 220, height: 130, font_family: 'Inter, system-ui, sans-serif', label_size: 18, value_size: 48, locked: false},
    {id: 'widget.ram.used', sensor_id: 'memory.ram.used_percent', label: 'RAM', x: 284, y: 32, width: 220, height: 130, font_family: 'Inter, system-ui, sans-serif', label_size: 18, value_size: 48, locked: false},
    {id: 'widget.gpu.temperature', sensor_id: 'gpu.nvidia.0.temperature', label: 'GPU Temp', x: 536, y: 32, width: 220, height: 130, font_family: 'Inter, system-ui, sans-serif', label_size: 18, value_size: 48, locked: false},
    {id: 'widget.gpu.power', sensor_id: 'gpu.nvidia.0.power_watts', label: 'GPU Watts', x: 788, y: 32, width: 204, height: 130, font_family: 'Inter, system-ui, sans-serif', label_size: 18, value_size: 48, locked: false},
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

function saveCustomTemplate(template) {
  if (typeof localStorage === 'undefined') {
    return;
  }
  localStorage.setItem(CUSTOM_TEMPLATE_KEY, JSON.stringify(template));
}

function loadCustomTemplate() {
  if (typeof localStorage === 'undefined') {
    return null;
  }
  try {
    const saved = JSON.parse(localStorage.getItem(CUSTOM_TEMPLATE_KEY) || 'null');
    return saved && typeof saved === 'object' ? saved : null;
  } catch {
    return null;
  }
}

function exportTemplateJson(template = dashboardTemplate) {
  return JSON.stringify(template, null, 2);
}

function addLocalAsset(template, fileName, assetType = 'icon') {
  template.assets = template.assets || [];
  const safeName = String(fileName).replace(/[^a-zA-Z0-9._-]/g, '-');
  const asset = {
    id: `asset.user.${Date.now()}.${safeName}`,
    type: assetType,
    path: `assets/${safeName}`,
    license: 'user-imported-personal-use',
    source: 'browser local file',
    redistributable: false,
  };
  template.assets.push(asset);
  return asset;
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

function panelStyle(template = dashboardTemplate) {
  const panel = template.panel || DEFAULT_DASHBOARD_TEMPLATE.panel;
  return `width:${panel.width}px;height:${panel.height}px;background:${panel.background};`;
}

function layoutWidgetHtml(widget, sensor) {
  const valueHtml = sensor ? formatSensorValue(sensor) : '—';
  const iconHtml = widgetIconHtml(widget);
  return `
    <article class="layout-widget ${widget.locked ? 'locked' : ''}" data-widget-id="${widget.id}" data-locked="${widget.locked}" style="left:${widget.x}px;top:${widget.y}px;width:${widget.width}px;height:${widget.height}px;font-family:${widget.font_family};">
      ${iconHtml}
      <div class="layout-widget-label" style="font-size:${widget.label_size}px">${widget.label}</div>
      <div class="layout-widget-value" style="font-size:${widget.value_size}px">${valueHtml}</div>
    </article>
  `;
}

function widgetIconHtml(widget) {
  if (!widget.icon_asset_id) {
    return '';
  }
  const asset = (dashboardTemplate.assets || []).find(candidate => candidate.id === widget.icon_asset_id);
  if (!asset) {
    return '';
  }
  return `<img class="layout-widget-icon" src="${asset.path}" alt="${widget.label} icon">`;
}

function renderLayoutCanvas(sensors) {
  const byId = new Map(sensors.map(sensor => [sensor.id, sensor]));
  const canvas = document.querySelector('#layout-canvas');
  canvas.setAttribute('style', panelStyle(dashboardTemplate));
  canvas.innerHTML = (dashboardTemplate.widgets || [])
    .map(widget => layoutWidgetHtml(widget, byId.get(widget.sensor_id)))
    .join('');
}

function updatePanelSize(template, width, height) {
  template.panel = template.panel || {};
  template.panel.width = Number(width);
  template.panel.height = Number(height);
}

function updateWidgetDesign(template, widgetId, changes) {
  const widget = (template.widgets || []).find(candidate => candidate.id === widgetId);
  if (!widget) {
    return;
  }
  for (const key of ['label', 'font_family', 'label_size', 'value_size', 'locked', 'icon_asset_id']) {
    if (Object.prototype.hasOwnProperty.call(changes, key)) {
      widget[key] = ['label_size', 'value_size'].includes(key) ? Number(changes[key]) : changes[key];
    }
  }
}

function selectLayoutWidget(template, widgetId) {
  if ((template.widgets || []).some(widget => widget.id === widgetId)) {
    template.selected_widget_id = widgetId;
  }
}

function moveLayoutWidget(template, widgetId, x, y) {
  const widget = (template.widgets || []).find(candidate => candidate.id === widgetId);
  if (!widget || widget.locked) {
    return;
  }
  widget.x = Number(x);
  widget.y = Number(y);
}

function resizeLayoutWidget(template, widgetId, width, height) {
  const widget = (template.widgets || []).find(candidate => candidate.id === widgetId);
  if (!widget || widget.locked) {
    return;
  }
  widget.width = Number(width);
  widget.height = Number(height);
}

function populateLayoutEditorControls() {
  const firstWidget = (dashboardTemplate.widgets || [])[0];
  document.querySelector('#panel-width').value = dashboardTemplate.panel?.width || '';
  document.querySelector('#panel-height').value = dashboardTemplate.panel?.height || '';
  if (firstWidget) {
    document.querySelector('#widget-label').value = firstWidget.label;
    document.querySelector('#widget-font-family').value = firstWidget.font_family;
    document.querySelector('#widget-label-size').value = firstWidget.label_size;
    document.querySelector('#widget-value-size').value = firstWidget.value_size;
    document.querySelector('#widget-locked').checked = firstWidget.locked;
  }
}

function setupLayoutEditorControls() {
  const apply = () => {
    const firstWidget = (dashboardTemplate.widgets || [])[0];
    updatePanelSize(dashboardTemplate, document.querySelector('#panel-width').value, document.querySelector('#panel-height').value);
    if (firstWidget) {
      updateWidgetDesign(dashboardTemplate, firstWidget.id, {
        label: document.querySelector('#widget-label').value,
        font_family: document.querySelector('#widget-font-family').value,
        label_size: document.querySelector('#widget-label-size').value,
        value_size: document.querySelector('#widget-value-size').value,
        locked: document.querySelector('#widget-locked').checked,
      });
    }
    refresh();
  };
  ['#panel-width', '#panel-height', '#widget-label', '#widget-font-family', '#widget-label-size', '#widget-value-size', '#widget-locked']
    .forEach(selector => document.querySelector(selector).addEventListener('input', apply));
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
  renderLayoutCanvas(visibleSensors);
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
  dashboardTemplate = loadCustomTemplate() || await response.json();
}

async function startOpenSensorPanel() {
  setupFullscreenButton();
  setupLayoutEditorControls();
  await loadTemplate();
  populateLayoutEditorControls();
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
    .layout-editor { margin-top: 2rem; display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 1rem; align-items: start; }
    .layout-canvas { position: relative; overflow: hidden; border: 1px solid #38bdf8aa; border-radius: 0; box-shadow: 0 16px 40px #000a; }
    .layout-widget { position: absolute; box-sizing: border-box; padding: .8rem; border: 1px dashed #60a5fa; border-radius: 14px; background: #0f172acc; cursor: move; }
    .layout-widget.locked { border-style: solid; border-color: #22c55e; cursor: not-allowed; }
    .layout-widget-label { color: #93c5fd; font-weight: 700; }
    .layout-widget-icon { max-width: 32px; max-height: 32px; object-fit: contain; margin-bottom: .35rem; }
    .layout-widget-value { color: #f8fafc; font-weight: 900; line-height: 1; }
    .editor-controls { background: #0f1724; border: 1px solid #263449; border-radius: 18px; padding: 1rem; }
    .editor-controls label { display: grid; gap: .25rem; margin: .6rem 0; color: #bfdbfe; font-size: .9rem; }
    .editor-controls input { background: #020617; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; padding: .45rem; }
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
    <section class="layout-editor" aria-labelledby="layout-editor-heading">
      <div>
        <h2 id="layout-editor-heading">Custom Layout Canvas</h2>
        <div id="layout-canvas" class="layout-canvas" aria-label="Borderless panel layout canvas"></div>
      </div>
      <aside class="editor-controls" aria-label="Layout editor controls">
        <h2>Layout Settings</h2>
        <label>Panel width <input id="panel-width" type="number" min="100" step="1"></label>
        <label>Panel height <input id="panel-height" type="number" min="100" step="1"></label>
        <label>Custom label <input id="widget-label" type="text" placeholder="CPU, GPU Temp, etc."></label>
        <label>Font family <input id="widget-font-family" type="text" placeholder="Inter, Orbitron, monospace"></label>
        <label>Icon/logo asset <select id="widget-icon-asset"><option value="">No icon</option></select></label>
        <label>Label size <input id="widget-label-size" type="number" min="8" step="1"></label>
        <label>Value size <input id="widget-value-size" type="number" min="12" step="1"></label>
        <label><input id="widget-locked" type="checkbox"> Lock selected item position</label>
        <div class="template-tools" aria-label="Template import export controls">
          <button id="template-export-button" class="button" type="button">Export .ospanel</button>
          <label>Import .ospanel <input id="template-import-file" type="file" accept=".ospanel,application/zip"></label>
          <label>Add icon/logo/background <input id="asset-upload-file" type="file" accept="image/*,.svg"></label>
        </div>
        <section id="sensor-mapping-panel" aria-label="Sensor remapping panel">
          <h3>Sensor Remapping</h3>
          <p class="hint">Imported templates can map old sensor names, like AIDA64 labels, to this PC's Linux sensor IDs.</p>
        </section>
        <p class="hint">MVP editor schema supports borderless panel size, fixed widget positions, custom labels, font choices, sizes, custom icons/logos/background assets, sensor remapping, and locked items.</p>
      </aside>
    </section>
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
