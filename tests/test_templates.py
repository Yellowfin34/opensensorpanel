import pytest

from opensensorpanel.templates import DEFAULT_TEMPLATE, TemplateValidationError, map_template_sensors, validate_template


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
        "redistributable": True,
    }


def test_default_template_declares_borderless_panel_size_and_positioned_widgets():
    template = validate_template(DEFAULT_TEMPLATE)

    assert template["panel"] == {
        "width": 1024,
        "height": 600,
        "borderless": True,
        "background": "#080b12",
        "grid_size": 10,
        "snap_to_grid": False,
    }
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


def test_validate_template_rejects_panel_background_that_does_not_reference_asset():
    bad_template = {
        **DEFAULT_TEMPLATE,
        "panel": {**DEFAULT_TEMPLATE["panel"], "background_asset_id": "asset.missing"},
    }

    with pytest.raises(TemplateValidationError, match="background_asset_id"):
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


def test_validate_template_accepts_explicit_sensor_mappings_for_imported_templates():
    template = {
        **DEFAULT_TEMPLATE,
        "sensor_mappings": {
            "AIDA64/GPU Diode": "gpu.nvidia.0.temperature",
            "AIDA64/CPU Utilization": "cpu.total.used_percent",
        },
    }

    validated = validate_template(template)

    assert validated["sensor_mappings"]["AIDA64/GPU Diode"] == "gpu.nvidia.0.temperature"


def test_map_template_sensors_rewrites_imported_sensor_ids_on_widgets_and_heroes():
    template = {
        **DEFAULT_TEMPLATE,
        "hero_sensor_ids": ["AIDA64/CPU Utilization"],
        "sensor_mappings": {"AIDA64/CPU Utilization": "cpu.total.used_percent"},
        "widgets": [
            {
                **DEFAULT_TEMPLATE["widgets"][0],
                "sensor_id": "AIDA64/CPU Utilization",
            }
        ],
    }

    mapped = map_template_sensors(template)

    assert mapped["hero_sensor_ids"] == ["cpu.total.used_percent"]
    assert mapped["widgets"][0]["sensor_id"] == "cpu.total.used_percent"
