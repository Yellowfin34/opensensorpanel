from __future__ import annotations

import json
from collections.abc import Sequence

from .snapshot import collect_snapshot


def main(argv: Sequence[str] | None = None) -> int:
    _ = argv
    print(json.dumps(collect_snapshot(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
