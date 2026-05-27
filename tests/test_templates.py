import pytest

from opensensorpanel.templates import DEFAULT_TEMPLATE, TemplateValidationError, validate_template


def test_default_template_declares_hero_and_group_layout():
    template = validate_template(DEFAULT_TEMPLATE)

    assert template["schema_version"] == 1
    assert template["title"] == "OpenSensorPanel"
    assert template["hero_sensor_ids"] == [
        "cpu.total.used_percent",
        "memory.ram.used_percent",
        "gpu.nvidia.0.temperature",
        "gpu.nvidia.0.power_watts",
    ]
    assert template["groups"][0] == {"category": "cpu", "label": "CPU"}


def test_validate_template_rejects_unknown_schema_version():
    bad_template = {"schema_version": 99, "title": "Bad", "hero_sensor_ids": [], "groups": []}

    with pytest.raises(TemplateValidationError, match="schema_version"):
        validate_template(bad_template)


def test_validate_template_rejects_group_without_category():
    bad_template = {"schema_version": 1, "title": "Bad", "hero_sensor_ids": [], "groups": [{"label": "CPU"}]}

    with pytest.raises(TemplateValidationError, match="category"):
        validate_template(bad_template)
