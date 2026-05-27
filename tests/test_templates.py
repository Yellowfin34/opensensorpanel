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
    assert template["assets"][0] == {
        "id": "asset.logo.opensensorpanel",
        "type": "logo",
        "path": "assets/opensensorpanel-logo.svg",
        "license": "project-created",
        "source": "OpenSensorPanel project",
    }


def test_default_template_declares_borderless_panel_size_and_positioned_widgets():
    template = validate_template(DEFAULT_TEMPLATE)

    assert template["panel"] == {"width": 1024, "height": 600, "borderless": True, "background": "#080b12"}
    assert template["widgets"][0] == {
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
    }


def test_validate_template_rejects_unknown_schema_version():
    bad_template = {"schema_version": 99, "title": "Bad", "hero_sensor_ids": [], "groups": []}

    with pytest.raises(TemplateValidationError, match="schema_version"):
        validate_template(bad_template)


def test_validate_template_rejects_group_without_category():
    bad_template = {"schema_version": 1, "title": "Bad", "hero_sensor_ids": [], "groups": [{"label": "CPU"}]}

    with pytest.raises(TemplateValidationError, match="category"):
        validate_template(bad_template)


def test_validate_template_rejects_asset_without_license():
    bad_template = {
        "schema_version": 1,
        "title": "Bad",
        "hero_sensor_ids": [],
        "groups": [],
        "assets": [{"id": "asset.logo", "type": "logo", "path": "assets/logo.png", "source": "unknown"}],
    }

    with pytest.raises(TemplateValidationError, match="license"):
        validate_template(bad_template)


def test_validate_template_rejects_asset_path_outside_template_assets():
    bad_template = {
        "schema_version": 1,
        "title": "Bad",
        "hero_sensor_ids": [],
        "groups": [],
        "assets": [
            {"id": "asset.logo", "type": "logo", "path": "../copied-aida64/logo.png", "license": "user-owned", "source": "user import"}
        ],
    }

    with pytest.raises(TemplateValidationError, match="asset path"):
        validate_template(bad_template)


def test_validate_template_rejects_widget_icon_that_does_not_reference_asset():
    bad_template = {
        "schema_version": 1,
        "title": "Bad",
        "hero_sensor_ids": [],
        "groups": [],
        "assets": [],
        "panel": {"width": 1024, "height": 600, "borderless": True, "background": "#080b12"},
        "widgets": [
            {
                "id": "widget.cpu.used",
                "sensor_id": "cpu.total.used_percent",
                "label": "CPU",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 120,
                "font_family": "Inter",
                "label_size": 16,
                "value_size": 42,
                "locked": False,
                "icon_asset_id": "asset.missing",
            }
        ],
    }

    with pytest.raises(TemplateValidationError, match="icon_asset_id"):
        validate_template(bad_template)


def test_validate_template_rejects_widget_without_lock_state():
    bad_template = {
        "schema_version": 1,
        "title": "Bad",
        "hero_sensor_ids": [],
        "groups": [],
        "panel": {"width": 1024, "height": 600, "borderless": True, "background": "#080b12"},
        "widgets": [
            {
                "id": "widget.cpu.used",
                "sensor_id": "cpu.total.used_percent",
                "label": "CPU",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 120,
                "font_family": "Inter",
                "label_size": 16,
                "value_size": 42,
            }
        ],
    }

    with pytest.raises(TemplateValidationError, match="locked"):
        validate_template(bad_template)
