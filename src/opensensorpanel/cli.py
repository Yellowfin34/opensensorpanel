from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from .aida64_import import inspect_sensorpanel_file
from .desktop_app import run_app, write_desktop_entry
from .snapshot import collect_snapshot
from .template_packages import export_ospanel, import_ospanel
from .templates import DEFAULT_TEMPLATE
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
    inspect_parser = subparsers.add_parser("inspect-aida64", help="inspect a user-owned AIDA64 .sensorpanel file safely")
    inspect_parser.add_argument("path", help="path to the .sensorpanel file")
    template_parser = subparsers.add_parser("template", help="manage OpenSensorPanel .ospanel templates")
    template_subparsers = template_parser.add_subparsers(dest="template_command", required=True)
    template_export_parser = template_subparsers.add_parser("export", help="export the default template as a .ospanel package")
    template_export_parser.add_argument("output", help="output .ospanel file")
    template_export_parser.add_argument("--personal", action="store_true", help="allow non-redistributable personal-use assets")
    template_import_parser = template_subparsers.add_parser("import", help="inspect an OpenSensorPanel .ospanel package")
    template_import_parser.add_argument("package", help="input .ospanel file")
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(host=args.host, port=args.port)
        return 0
    if args.command == "app":
        run_app(host=args.host, port=args.port, kiosk=args.kiosk, open_window=not args.no_open)
        return 0
    if args.command == "install-desktop":
        launcher = Path(args.launcher).expanduser().resolve() if args.launcher else Path("opensensorpanel")
        desktop_file = write_desktop_entry(launcher)
        print(f"Installed desktop launcher: {desktop_file}")
        return 0
    if args.command == "inspect-aida64":
        print(json.dumps(inspect_sensorpanel_file(args.path), indent=2, sort_keys=True))
        return 0
    if args.command == "template":
        if args.template_command == "export":
            output = export_ospanel(DEFAULT_TEMPLATE, args.output, public=not args.personal)
            print(f"Exported template package: {output}")
            return 0
        if args.template_command == "import":
            imported = import_ospanel(args.package)
            print(
                json.dumps(
                    {
                        "title": imported.template["title"],
                        "widgets": len(imported.template.get("widgets", [])),
                        "assets": len(imported.assets),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

    print(json.dumps(collect_snapshot(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
