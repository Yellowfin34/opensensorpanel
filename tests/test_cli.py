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
