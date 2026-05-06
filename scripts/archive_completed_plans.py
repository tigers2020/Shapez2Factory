"""Move implemented plan+research pairs into documents/archive/completed-implementation/.

Run from repo root:
  python scripts/archive_completed_plans.py

Excludes stems listed in EXCLUDE_STEMS (long-horizon or design-only plans).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS = REPO_ROOT / "documents" / "plans"
RESEARCH = REPO_ROOT / "documents" / "research"
DEST_BASE = REPO_ROOT / "documents" / "archive" / "completed-implementation" / "by-stem"

# Keep in documents/plans (and optionally documents/research): backlog /
# design-only / no paired research policy.
EXCLUDE_STEMS = frozenset(
    {
        "factory_throughput",
        "solve_progress_rendering_2026-05-01",
        "solver_graph_horizontal_layout_2026-05-01",
    }
)

# From documents/plans or documents/research → repo root is two levels.
OLD_ROOT_PREFIX = "../../"
# From documents/archive/completed-implementation/by-stem/<stem>/file.md → repo root is five levels.
NEW_ROOT_PREFIX = "../../../../../"


def _rewrite_markdown_links(text: str) -> str:
    """Adjust relative links after moving one directory deeper under archive."""
    text = text.replace(OLD_ROOT_PREFIX, NEW_ROOT_PREFIX)
    # plan ↔ research used to live in sibling folders plans/ and research/
    text = re.sub(
        r"\]\((\.\./)+research/(research_[^)]+\.md)\)",
        r"](./\2)",
        text,
    )
    text = re.sub(
        r"\]\((\.\./)+plans/(plan_[^)]+\.md)\)",
        r"](./\2)",
        text,
    )
    return text


def main() -> None:
    if not PLANS.is_dir():
        raise SystemExit(f"missing plans dir: {PLANS}")
    DEST_BASE.mkdir(parents=True, exist_ok=True)

    movable = [
        p
        for p in sorted(PLANS.glob("plan_*.md"))
        if p.name.removeprefix("plan_").removesuffix(".md") not in EXCLUDE_STEMS
    ]
    if not movable:
        print("Nothing to move (all remaining plans are excluded or already archived).")
        return

    moved: list[str] = []

    for plan_path in movable:
        stem = plan_path.name.removeprefix("plan_").removesuffix(".md")

        dest_dir = DEST_BASE / stem
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_plan = dest_dir / plan_path.name
        shutil.move(str(plan_path), str(dest_plan))
        text = dest_plan.read_text(encoding="utf-8")
        dest_plan.write_text(_rewrite_markdown_links(text), encoding="utf-8")
        moved.append(f"{stem}: {dest_plan.relative_to(REPO_ROOT)}")

        research_name = f"research_{stem}.md"
        research_path = RESEARCH / research_name
        if research_path.is_file():
            dest_research = dest_dir / research_name
            shutil.move(str(research_path), str(dest_research))
            text = dest_research.read_text(encoding="utf-8")
            dest_research.write_text(_rewrite_markdown_links(text), encoding="utf-8")
            moved.append(f"{stem}: {dest_research.relative_to(REPO_ROOT)}")

    print("Moved:", len(moved), "entries")
    for line in moved:
        print(" ", line)
    print("Excluded stems (kept under documents/plans):", ", ".join(sorted(EXCLUDE_STEMS)))


if __name__ == "__main__":
    main()
