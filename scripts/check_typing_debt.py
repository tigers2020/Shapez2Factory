#!/usr/bin/env python3
"""Fail when typing debt exceeds the recorded baseline (typing-zero guard)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Baseline captured 2026-06-11 before typing-zero loop slice 1.
BASELINE = {
    "any_token_total": 730,
    "files_with_any": 139,
    "dict_str_object_production_files": 84,
}

PRODUCTION_PREFIXES = (
    "django_apps/",
    "src/",
    "config/",
)


def _is_production(path: str) -> bool:
    if path.startswith("tests/") or path.startswith("scripts/") or path.startswith("harness/"):
        return False
    return path.startswith(PRODUCTION_PREFIXES)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    inventory = repo / "scripts" / "typing_debt_inventory.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("typing_debt_inventory", inventory)
    if spec is None or spec.loader is None:
        print("check_typing_debt: cannot load inventory module", file=sys.stderr)
        return 2
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    rows = module.scan(repo)
    summary = module.summarize(rows)

    any_total = int(summary["any_token_total"])
    files_with_any = sum(1 for r in rows if r.any_token > 0)
    prod_object_files = sum(1 for r in rows if r.dict_str_object > 0 and _is_production(r.path))

    failures: list[str] = []
    if any_total > BASELINE["any_token_total"]:
        failures.append(
            f"Any token count increased: {any_total} > baseline {BASELINE['any_token_total']}"
        )
    if files_with_any > BASELINE["files_with_any"]:
        failures.append(
            "Any-containing files increased: "
            f"{files_with_any} > baseline {BASELINE['files_with_any']}"
        )
    if prod_object_files > BASELINE["dict_str_object_production_files"]:
        failures.append(
            "Production dict[str, object] files increased: "
            f"{prod_object_files} > baseline {BASELINE['dict_str_object_production_files']}"
        )

    if failures:
        for msg in failures:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "any_token_total": any_total,
                "files_with_any": files_with_any,
                "dict_str_object_production_files": prod_object_files,
                "baseline": BASELINE,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
