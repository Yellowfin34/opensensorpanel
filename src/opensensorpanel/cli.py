from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .desktop_app import run_app, write_desktop_entry
from .snapshot import collect_snapshot
from .web import serve


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opensensorpanel")
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="start the local OpenSensorPanel web UI")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8766)
    app_parser = subparsers.add_parser("app", help="start OpenSensorPanel as a desktop-style app window")
    app_parser.add_argument("--host", default="127.0.0.1")
    app_parser.add_argument("--port", type=int, default=8766)
    app_parser.add_argument("--kiosk", action="store_true", help="open the dedicated panel URL for second-screen use")
    app_parser.add_argument("--no-open", action="store_true", help="start the local service without opening a browser window")
    install_parser = subparsers.add_parser("install-desktop", help="install an OpenSensorPanel app launcher for this user")
    install_parser.add_argument("--launcher", help="path to the installed opensensorpanel command")
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(host=args.host, port=args.port)
        return 0
    if args.command == "app":
        run_app(host=args.host, port=args.port, kiosk=args.kiosk, open_window=not args.no_open)
        return 0
    if args.command == "install-desktop":
        from pathlib import Path

        launcher = Path(args.launcher).expanduser().resolve() if args.launcher else Path("opensensorpanel")
        desktop_file = write_desktop_entry(launcher)
        print(f"Installed desktop launcher: {desktop_file}")
        return 0

    print(json.dumps(collect_snapshot(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
