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
