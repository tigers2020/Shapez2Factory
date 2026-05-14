#!/usr/bin/env python3
"""Compile ``locale/*/LC_MESSAGES/django*.po`` to ``.mo`` using polib (no GNU msgfmt)."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import polib
except ImportError as exc:  # pragma: no cover
    print("polib required (dev dependency): pip install -e '.[dev]'", file=sys.stderr)
    raise SystemExit(1) from exc

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    count = 0
    for po_path in sorted(ROOT.glob("locale/*/LC_MESSAGES/django*.po")):
        mo_path = po_path.with_suffix(".mo")
        polib.pofile(str(po_path)).save_as_mofile(str(mo_path))
        print(f"{po_path.relative_to(ROOT)} -> {mo_path.relative_to(ROOT)}")
        count += 1
    if not count:
        print("No locale/*/LC_MESSAGES/django*.po found", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
