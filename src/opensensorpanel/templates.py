from __future__ import annotations

from copy import deepcopy
from typing import Any


class TemplateValidationError(ValueError):
    pass


DEFAULT_TEMPLATE: dict[str, Any] = {
    "schema_version": 1,
    "title": "OpenSensorPanel",
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
}


def validate_template(template: dict[str, Any]) -> dict[str, Any]:
    if template.get("schema_version") != 1:
        raise TemplateValidationError("template schema_version must be 1")
    if not isinstance(template.get("title"), str) or not template["title"]:
        raise TemplateValidationError("template title must be a non-empty string")
    hero_sensor_ids = template.get("hero_sensor_ids")
    if not isinstance(hero_sensor_ids, list) or not all(isinstance(sensor_id, str) for sensor_id in hero_sensor_ids):
        raise TemplateValidationError("template hero_sensor_ids must be a list of strings")
    groups = template.get("groups")
    if not isinstance(groups, list):
        raise TemplateValidationError("template groups must be a list")
    for group in groups:
        if not isinstance(group, dict):
            raise TemplateValidationError("template group must be an object")
        if not isinstance(group.get("category"), str) or not group["category"]:
            raise TemplateValidationError("template group category must be a non-empty string")
        if not isinstance(group.get("label"), str) or not group["label"]:
            raise TemplateValidationError("template group label must be a non-empty string")
    return deepcopy(template)
