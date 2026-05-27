from __future__ import annotations

from copy import deepcopy
from typing import Any


class TemplateValidationError(ValueError):
    pass


DEFAULT_TEMPLATE: dict[str, Any] = {
    "schema_version": 1,
    "title": "OpenSensorPanel",
    "panel": {
        "width": 1024,
        "height": 600,
        "borderless": True,
        "background": "#080b12",
    },
    "hero_sensor_ids": [
        "cpu.total.used_percent",
        "memory.ram.used_percent",
        "gpu.nvidia.0.temperature",
        "gpu.nvidia.0.power_watts",
    ],
    "groups": [
        {"category": "cpu", "label": "CPU"},
        {"category": "memory", "label": "Memory"},
        {"category": "gpu", "label": "GPU"},
        {"category": "temperature", "label": "Temperatures"},
        {"category": "fan", "label": "Fans"},
        {"category": "voltage", "label": "Voltages"},
        {"category": "power", "label": "Power"},
        {"category": "current", "label": "Current"},
        {"category": "energy", "label": "Energy"},
        {"category": "humidity", "label": "Humidity"},
        {"category": "frequency", "label": "Frequency"},
        {"category": "pwm", "label": "PWM"},
    ],
    "assets": [
        {
            "id": "asset.logo.opensensorpanel",
            "type": "logo",
            "path": "assets/opensensorpanel-logo.svg",
            "license": "project-created",
            "source": "OpenSensorPanel project",
        }
    ],
    "widgets": [
        {
            "id": "widget.cpu.used",
            "sensor_id": "cpu.total.used_percent",
            "label": "CPU",
            "x": 32,
            "y": 32,
            "width": 220,
            "height": 130,
            "font_family": "Inter, system-ui, sans-serif",
            "label_size": 18,
            "value_size": 48,
            "locked": False,
        },
        {
            "id": "widget.ram.used",
            "sensor_id": "memory.ram.used_percent",
            "label": "RAM",
            "x": 284,
            "y": 32,
            "width": 220,
            "height": 130,
            "font_family": "Inter, system-ui, sans-serif",
            "label_size": 18,
            "value_size": 48,
            "locked": False,
        },
        {
            "id": "widget.gpu.temperature",
            "sensor_id": "gpu.nvidia.0.temperature",
            "label": "GPU Temp",
            "x": 536,
            "y": 32,
            "width": 220,
            "height": 130,
            "font_family": "Inter, system-ui, sans-serif",
            "label_size": 18,
            "value_size": 48,
            "locked": False,
        },
        {
            "id": "widget.gpu.power",
            "sensor_id": "gpu.nvidia.0.power_watts",
            "label": "GPU Watts",
            "x": 788,
            "y": 32,
            "width": 204,
            "height": 130,
            "font_family": "Inter, system-ui, sans-serif",
            "label_size": 18,
            "value_size": 48,
            "locked": False,
        },
    ],
}


def _require_string(mapping: dict[str, Any], key: str, context: str) -> None:
    if not isinstance(mapping.get(key), str) or not mapping[key]:
        raise TemplateValidationError(f"template {context} {key} must be a non-empty string")


def _require_number(mapping: dict[str, Any], key: str, context: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TemplateValidationError(f"template {context} {key} must be a number")


def _validate_assets(assets: Any) -> set[str]:
    if not isinstance(assets, list):
        raise TemplateValidationError("template assets must be a list")
    asset_ids: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            raise TemplateValidationError("template asset must be an object")
        for key in ["id", "type", "path", "license", "source"]:
            _require_string(asset, key, "asset")
        if asset["type"] not in {"icon", "logo", "background"}:
            raise TemplateValidationError("template asset type must be icon, logo, or background")
        if not asset["path"].startswith("assets/") or ".." in asset["path"].split("/"):
            raise TemplateValidationError("template asset path must stay under assets/")
        asset_ids.add(asset["id"])
    return asset_ids


def validate_template(template: dict[str, Any]) -> dict[str, Any]:
    if template.get("schema_version") != 1:
        raise TemplateValidationError("template schema_version must be 1")
    if not isinstance(template.get("title"), str) or not template["title"]:
        raise TemplateValidationError("template title must be a non-empty string")

    panel = template.get("panel")
    if panel is not None:
        if not isinstance(panel, dict):
            raise TemplateValidationError("template panel must be an object")
        _require_number(panel, "width", "panel")
        _require_number(panel, "height", "panel")
        if panel["width"] <= 0 or panel["height"] <= 0:
            raise TemplateValidationError("template panel width and height must be positive")
        if not isinstance(panel.get("borderless"), bool):
            raise TemplateValidationError("template panel borderless must be a boolean")
        _require_string(panel, "background", "panel")

    hero_sensor_ids = template.get("hero_sensor_ids")
    if not isinstance(hero_sensor_ids, list) or not all(isinstance(sensor_id, str) for sensor_id in hero_sensor_ids):
        raise TemplateValidationError("template hero_sensor_ids must be a list of strings")

    groups = template.get("groups")
    if not isinstance(groups, list):
        raise TemplateValidationError("template groups must be a list")
    for group in groups:
        if not isinstance(group, dict):
            raise TemplateValidationError("template group must be an object")
        _require_string(group, "category", "group")
        _require_string(group, "label", "group")

    asset_ids = _validate_assets(template.get("assets", []))

    widgets = template.get("widgets", [])
    if not isinstance(widgets, list):
        raise TemplateValidationError("template widgets must be a list")
    for widget in widgets:
        if not isinstance(widget, dict):
            raise TemplateValidationError("template widget must be an object")
        for key in ["id", "sensor_id", "label", "font_family"]:
            _require_string(widget, key, "widget")
        for key in ["x", "y", "width", "height", "label_size", "value_size"]:
            _require_number(widget, key, "widget")
        if widget["width"] <= 0 or widget["height"] <= 0:
            raise TemplateValidationError("template widget width and height must be positive")
        if not isinstance(widget.get("locked"), bool):
            raise TemplateValidationError("template widget locked must be a boolean")
        if "icon_asset_id" in widget:
            _require_string(widget, "icon_asset_id", "widget")
            if widget["icon_asset_id"] not in asset_ids:
                raise TemplateValidationError("template widget icon_asset_id must reference a declared asset")

    return deepcopy(template)
