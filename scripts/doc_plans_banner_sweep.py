#!/usr/bin/env python3
"""One-shot: insert PR-F plans/ banners into documents/plans/**/*.md."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLANS = REPO / "documents" / "plans"
ALGORITHM = REPO / "documents" / "Algorithm"

CANONICAL_BANNER = (
    "> **Plans snapshot (ARCHIVED):** Prefer "
    "[`documents/Algorithm/{name}`](../../Algorithm/{name}). "
    "**PR-F (2026-05):** dense server coords removed; island-local only. "
    "Do not treat server X/Y / `neighbors4_server` checklists below as current contract.\n"
)

GENERIC_BANNER = (
    "> **Plans snapshot:** Not mirrored in `documents/Algorithm/`. "
    "For live contracts see [`documents/Algorithm/`](../../Algorithm/). "
    "**PR-F (2026-05):** dense server coords removed from product code.\n"
)

ROOT_BANNER = (
    "> **Plans (misc):** Project planning memo; not Asteroid Lab coordinate canon. "
    "See [`documents/Algorithm/`](../Algorithm/) and [`docs/superpowers/specs/`](../docs/superpowers/specs/) for active specs.\n"
)

README_EXTRA = """
## Doc sweep (2026-05-23)

Each `asteroid_lab_*.md` file has a top-of-file banner pointing at **`documents/Algorithm/`** when a matching CANON doc exists.

- **PR-F:** Product code uses **island-local** `(x, y)` only; `server_coords.py` and dense server HUD are **removed**.
- Checklists mentioning Server X/Y or `neighbors4_server` in this folder are **historical** (pre–PR-F copies).
"""


def has_banner(text: str) -> bool:
    return "**Plans snapshot" in text[:1200] or "**Canonical:**" in text[:1200]


def insert_after_title(text: str, banner: str) -> str:
    if has_banner(text):
        return text
    lines = text.splitlines(keepends=True)
    if not lines:
        return banner + "\n"
    out: list[str] = []
    i = 0
    if lines[0].startswith("---"):
        while i < len(lines) and not (i > 0 and lines[i].strip() == "---"):
            out.append(lines[i])
            i += 1
        if i < len(lines):
            out.append(lines[i])
            i += 1
    if i < len(lines) and lines[i].startswith("#"):
        out.append(lines[i])
        i += 1
        if i < len(lines) and lines[i].strip() == "":
            out.append(lines[i])
            i += 1
        out.append("\n")
        out.append(banner)
        out.append("\n")
    out.extend(lines[i:])
    return "".join(out)


def main() -> None:
    algorithm_names = {p.name for p in ALGORITHM.glob("asteroid_lab_*.md")}
    changed: list[str] = []

    for path in sorted(PLANS.rglob("*.md")):
        rel = path.relative_to(PLANS)
        if rel.parts[0] == "asteroid_lab_optimization" and path.name == "README.md":
            text = path.read_text(encoding="utf-8")
            if "Doc sweep (2026-05-23)" not in text:
                path.write_text(text.rstrip() + README_EXTRA, encoding="utf-8")
                changed.append(str(rel) + " (README appendix)")
            continue

        text = path.read_text(encoding="utf-8")
        if has_banner(text):
            continue

        if path.name.startswith("asteroid_lab_") and path.name in algorithm_names:
            banner = CANONICAL_BANNER.format(name=path.name)
        elif path.parent.name == "asteroid_lab_optimization":
            banner = GENERIC_BANNER
        else:
            banner = ROOT_BANNER

        new_text = insert_after_title(text, banner)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(rel))

    print(f"Updated {len(changed)} file(s):")
    for c in changed:
        print(f"  - documents/plans/{c}")


if __name__ == "__main__":
    main()
