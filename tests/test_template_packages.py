import json
import zipfile
from pathlib import Path

import pytest

from opensensorpanel.template_packages import (
    TemplatePackageError,
    export_ospanel,
    import_ospanel,
)
from opensensorpanel.templates import DEFAULT_TEMPLATE


def test_export_ospanel_writes_template_json_and_declared_assets(tmp_path):
    asset_source = tmp_path / "logo.svg"
    asset_source.write_text("<svg></svg>")
    template = {
        **DEFAULT_TEMPLATE,
        "assets": [
            {
                "id": "asset.logo.test",
                "type": "logo",
                "path": "assets/logo.svg",
                "license": "project-created",
                "source": str(asset_source),
                "redistributable": True,
            }
        ],
    }
    output = tmp_path / "panel.ospanel"

    export_ospanel(template, output)

    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist()) == ["assets/logo.svg", "template.json"]
        exported_template = json.loads(archive.read("template.json"))
        assert exported_template["assets"][0]["path"] == "assets/logo.svg"
        assert archive.read("assets/logo.svg") == b"<svg></svg>"


def test_export_ospanel_blocks_nonredistributable_assets_for_public_packages(tmp_path):
    asset_source = tmp_path / "aida64.png"
    asset_source.write_bytes(b"copied-art")
    template = {
        **DEFAULT_TEMPLATE,
        "assets": [
            {
                "id": "asset.user.aida64",
                "type": "background",
                "path": "assets/aida64.png",
                "license": "user-imported-personal-use",
                "source": str(asset_source),
                "redistributable": False,
            }
        ],
    }

    with pytest.raises(TemplatePackageError, match="non-redistributable"):
        export_ospanel(template, tmp_path / "public.ospanel", public=True)


def test_import_ospanel_loads_template_and_asset_bytes(tmp_path):
    package = tmp_path / "panel.ospanel"
    template = {
        **DEFAULT_TEMPLATE,
        "assets": [
            {
                "id": "asset.icon.cpu",
                "type": "icon",
                "path": "assets/cpu.svg",
                "license": "CC0",
                "source": "unit test",
                "redistributable": True,
            }
        ],
    }
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("template.json", json.dumps(template))
        archive.writestr("assets/cpu.svg", "<svg>cpu</svg>")

    imported = import_ospanel(package)

    assert imported.template["assets"][0]["id"] == "asset.icon.cpu"
    assert imported.assets["assets/cpu.svg"] == b"<svg>cpu</svg>"
