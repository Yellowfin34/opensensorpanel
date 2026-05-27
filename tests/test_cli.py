import json
import os
import subprocess
import sys

from opensensorpanel import cli


def test_cli_prints_snapshot_json(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "collect_snapshot",
        lambda: {"schema_version": 1, "updated_at": "now", "sensors": []},
    )

    exit_code = cli.main([])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "schema_version": 1,
        "updated_at": "now",
        "sensors": [],
    }


def test_cli_module_execution_prints_json():
    env = {**os.environ, "PYTHONPATH": "src"}

    result = subprocess.run(
        [sys.executable, "-m", "opensensorpanel.cli"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert json.loads(result.stdout)["schema_version"] == 1


def test_cli_serve_starts_web_server(monkeypatch):
    called = {}

    def fake_serve(host: str, port: int) -> None:
        called["host"] = host
        called["port"] = port

    monkeypatch.setattr(cli, "serve", fake_serve)

    assert cli.main(["serve", "--host", "0.0.0.0", "--port", "9999"]) == 0
    assert called == {"host": "0.0.0.0", "port": 9999}



def test_cli_inspect_aida64_prints_personal_use_report(tmp_path, capsys):
    sensorpanel = tmp_path / "gaming.sensorpanel"
    sensorpanel.write_bytes(b"example")

    assert cli.main(["inspect-aida64", str(sensorpanel)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["source_format"] == "aida64-sensorpanel"
    assert payload["recommended_license"] == "user-imported-personal-use"
    assert payload["redistributable"] is False


def test_cli_export_template_writes_ospanel_package(tmp_path, capsys):
    output = tmp_path / "default.ospanel"

    assert cli.main(["template", "export", str(output)]) == 0

    assert output.exists()
    assert "Exported template package" in capsys.readouterr().out


def test_cli_import_template_prints_summary(tmp_path, capsys):
    output = tmp_path / "default.ospanel"
    assert cli.main(["template", "export", str(output)]) == 0
    capsys.readouterr()

    assert cli.main(["template", "import", str(output)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == "OpenSensorPanel"
    assert payload["widgets"] == 4
    assert payload["assets"] == 0
