import zipfile

from opensensorpanel.aida64_import import inspect_sensorpanel_file


def test_inspect_sensorpanel_file_marks_user_import_as_local_personal_only(tmp_path):
    sensorpanel = tmp_path / "gaming.sensorpanel"
    sensorpanel.write_bytes(b"AIDA64 SensorPanel settings with embedded graphics")

    report = inspect_sensorpanel_file(sensorpanel)

    assert report["source_format"] == "aida64-sensorpanel"
    assert report["recommended_license"] == "user-imported-personal-use"
    assert report["redistributable"] is False
    assert "Do not redistribute" in report["warnings"][0]


def test_inspect_sensorpanel_zip_lists_candidate_embedded_assets(tmp_path):
    sensorpanel = tmp_path / "gaming.sensorpanel"
    with zipfile.ZipFile(sensorpanel, "w") as archive:
        archive.writestr("SensorPanelManager.ini", "[SensorPanel]\n")
        archive.writestr("Images/logo.png", b"png")
        archive.writestr("Images/bg.jpg", b"jpg")
        archive.writestr("README.txt", "not an asset")

    report = inspect_sensorpanel_file(sensorpanel)

    assert report["candidate_assets"] == ["Images/bg.jpg", "Images/logo.png"]
    assert report["redistributable"] is False
