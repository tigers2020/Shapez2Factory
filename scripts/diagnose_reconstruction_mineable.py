#!/usr/bin/env python3
"""Print ``ReconstructionDiagnosisDTO`` JSON for a decoded blueprint file (dev helper).

Usage:
  python scripts/diagnose_reconstruction_mineable.py path/to/decoded.json

``decoded.json`` must be a JSON object with a ``BP`` key (same shape as after copy decode).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"not a file: {path}", file=sys.stderr)
        return 2
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print("root must be a JSON object", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
        diagnose_reconstruction_mineable_empty,
    )

    diag = diagnose_reconstruction_mineable_empty(raw)
    payload = asdict(diag)
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
