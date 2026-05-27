from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico"}


def inspect_sensorpanel_file(path: str | Path) -> dict[str, Any]:
    """Inspect a user-owned AIDA64 .sensorpanel file without redistributing it.

    This intentionally does not claim ownership or safe redistribution. It only
    identifies candidate embedded assets so OpenSensorPanel can import locally
    and mark everything as personal-use unless the user supplies licenses.
    """

    sensorpanel = Path(path)
    candidate_assets: list[str] = []
    if zipfile.is_zipfile(sensorpanel):
        with zipfile.ZipFile(sensorpanel) as archive:
            candidate_assets = sorted(
                name
                for name in archive.namelist()
                if Path(name).suffix.lower() in _IMAGE_EXTENSIONS and not name.endswith("/")
            )

    return {
        "source_format": "aida64-sensorpanel",
        "path": str(sensorpanel),
        "candidate_assets": candidate_assets,
        "recommended_license": "user-imported-personal-use",
        "redistributable": False,
        "warnings": [
            "Do not redistribute imported AIDA64 templates, fonts, logos, icons, or artwork unless you own the rights or have a clear license.",
            "OpenSensorPanel should store these as local personal-use assets by default.",
        ],
    }
