from __future__ import annotations

import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from collections.abc import Iterable
from pathlib import Path

from .web import serve

APP_MODE_BROWSERS = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge",
)
REGULAR_BROWSERS = APP_MODE_BROWSERS + ("firefox", "xdg-open")


def panel_url(port: int, *, kiosk: bool) -> str:
    suffix = "?mode=panel" if kiosk else ""
    return f"http://127.0.0.1:{port}/{suffix}"


def choose_browser_command(available_commands: Iterable[str] | None = None) -> str | None:
    if available_commands is None:
        for command in REGULAR_BROWSERS:
            if shutil.which(command):
                return command
        return None

    available = set(available_commands)
    for command in REGULAR_BROWSERS:
        if command in available:
            return command
    return None


def build_browser_command(browser: str, url: str) -> list[str]:
    if browser in APP_MODE_BROWSERS:
        return [browser, f"--app={url}", "--new-window"]
    return [browser, url]


def build_desktop_entry(launcher_path: Path) -> str:
    return "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            "Name=OpenSensorPanel",
            "Comment=Linux-native SensorPanel-style hardware dashboard",
            f"Exec={launcher_path} app --port 8766 --kiosk",
            "Icon=utilities-system-monitor",
            "Terminal=false",
            "Categories=System;Monitor;",
            "StartupNotify=true",
            "",
        ]
    )


def open_panel_window(url: str) -> None:
    browser = choose_browser_command()
    if browser:
        subprocess.Popen(build_browser_command(browser, url), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    webbrowser.open(url)


def run_app(*, host: str = "127.0.0.1", port: int = 8766, kiosk: bool = True, open_window: bool = True) -> None:
    url = panel_url(port, kiosk=kiosk)
    if open_window:
        threading.Thread(target=_delayed_open, args=(url,), daemon=True).start()
    serve(host=host, port=port)


def _delayed_open(url: str) -> None:
    time.sleep(0.8)
    open_panel_window(url)


def write_desktop_entry(launcher_path: Path, applications_dir: Path | None = None) -> Path:
    if applications_dir is None:
        applications_dir = Path.home() / ".local" / "share" / "applications"
    applications_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = applications_dir / "opensensorpanel.desktop"
    desktop_file.write_text(build_desktop_entry(launcher_path), encoding="utf-8")
    desktop_file.chmod(0o755)
    return desktop_file


def default_launcher_path() -> Path:
    return Path(sys.executable).resolve()
