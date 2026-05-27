from __future__ import annotations

import os
from pathlib import Path

from opensensorpanel.desktop_app import (
    build_browser_command,
    build_desktop_entry,
    choose_browser_command,
    panel_url,
)


def test_panel_url_uses_localhost_port_and_kiosk_query():
    assert panel_url(8766, kiosk=True) == "http://127.0.0.1:8766/?mode=panel"
    assert panel_url(8766, kiosk=False) == "http://127.0.0.1:8766/"


def test_choose_browser_command_prefers_app_mode_capable_browser():
    commands = {"firefox", "google-chrome"}

    assert choose_browser_command(commands) == "google-chrome"


def test_build_browser_command_uses_app_window_when_supported():
    command = build_browser_command("chromium", "http://127.0.0.1:8766/?mode=panel")

    assert command == [
        "chromium",
        "--app=http://127.0.0.1:8766/?mode=panel",
        "--new-window",
    ]


def test_build_browser_command_falls_back_to_regular_browser():
    command = build_browser_command("firefox", "http://127.0.0.1:8766/?mode=panel")

    assert command == ["firefox", "http://127.0.0.1:8766/?mode=panel"]


def test_build_desktop_entry_points_to_installed_program(tmp_path: Path):
    launcher = tmp_path / "bin" / "opensensorpanel"
    launcher.parent.mkdir()
    launcher.write_text("#!/bin/sh\n")
    launcher.chmod(0o755)

    entry = build_desktop_entry(launcher)

    assert "Name=OpenSensorPanel" in entry
    assert f"Exec={launcher} app --port 8766 --kiosk" in entry
    assert "Type=Application" in entry
    assert "Categories=System;Monitor;" in entry
    assert "Terminal=false" in entry
