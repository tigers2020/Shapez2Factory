#!/usr/bin/env python3
"""Emit AGENT_LOOP_WAKE_typing_zero for the inventory-driven typing-zero chain."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BRANCH = "typing-zero/phase-5-persistent-exterior-overlay"
PR = 284
MANUAL = "documents/ai/manuals/typing_boundary_layers.md"

AUTHORITY = (
    "Authority: read " + MANUAL + ". "
    "domain=dataclass, wire=TypedDict, raw decode=JsonValue/object+validator, "
    "never long-lived dict[str,object] contracts."
)


def _load_inventory() -> dict[str, object]:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "typing_debt_inventory",
        REPO / "scripts" / "typing_debt_inventory.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load typing_debt_inventory")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = module.scan(REPO)
    return module.summarize(rows)


def main() -> int:
    summary = _load_inventory()
    any_total = int(summary["any_token_total"])

    if any_total == 0:
        prompt = (
            f"typing-zero FINAL on PR #{PR} ({BRANCH}): Any count is 0. "
            f"{AUTHORITY} "
            "Run full validation ONCE only: python manage.py check, "
            "powershell -File scripts/test_full.ps1, mypy django_apps config src, "
            "ruff check ., black --check ., python scripts/check_typing_debt.py "
            "(set zero baseline). Push if needed; wait for CI + Bugbot once. Stop slicing."
        )
    else:
        prompt = (
            f"typing-zero chain on PR #{PR} ({BRANCH}): {any_total} Any remaining. "
            f"{AUTHORITY} "
            "1) python scripts/typing_debt_inventory.py "
            "2) smallest safe bucket per checklist "
            "3) convert: Any→remove; wire→TypedDict+converter; domain→dataclass; "
            "raw→JsonValue/object then validator "
            "4) local gates only (ruff/black/mypy touched paths, targeted pytest, "
            "python scripts/check_typing_debt.py) "
            "5) commit+push same PR. NO test_full, NO Bugbot wait until Any=0. "
            "Immediately start next slice; re-arm: "
            "powershell -NoProfile -File .cursor/typing-zero-loop.ps1"
        )

    payload = {"prompt": prompt, "any_remaining": any_total, "manual": MANUAL}
    print(f"AGENT_LOOP_WAKE_typing_zero {json.dumps(payload, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
