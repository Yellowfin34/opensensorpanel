from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .templates import validate_template


class TemplatePackageError(ValueError):
    pass


@dataclass(frozen=True)
class ImportedTemplatePackage:
    template: dict[str, Any]
    assets: dict[str, bytes]


def _asset_is_redistributable(asset: dict[str, Any]) -> bool:
    if asset.get("redistributable") is False:
        return False
    return asset.get("license") not in {"user-imported-personal-use", "unknown", "proprietary"}


def export_ospanel(template: dict[str, Any], output_path: str | Path, *, public: bool = True) -> Path:
    validated = validate_template(template)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    for asset in validated.get("assets", []):
        if public and not _asset_is_redistributable(asset):
            raise TemplatePackageError(f"asset {asset['id']} is non-redistributable")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("template.json", json.dumps(validated, indent=2, sort_keys=True))
        for asset in validated.get("assets", []):
            source = Path(asset["source"]).expanduser()
            if source.exists() and source.is_file():
                archive.write(source, asset["path"])
    return output


def import_ospanel(package_path: str | Path) -> ImportedTemplatePackage:
    package = Path(package_path)
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if "template.json" not in names:
            raise TemplatePackageError(".ospanel package must include template.json")
        template = validate_template(json.loads(archive.read("template.json")))
        assets: dict[str, bytes] = {}
        for name in names:
            if name.startswith("assets/") and not name.endswith("/"):
                assets[name] = archive.read(name)
    return ImportedTemplatePackage(template=template, assets=assets)
