from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from .snapshot import collect_snapshot
from .web import serve


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="opensensorpanel")
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="start the local OpenSensorPanel web UI")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)

    if args.command == "serve":
        serve(host=args.host, port=args.port)
        return 0

    print(json.dumps(collect_snapshot(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
