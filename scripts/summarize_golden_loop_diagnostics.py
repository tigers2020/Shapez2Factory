#!/usr/bin/env python
"""Print a markdown summary from golden loop output JSON files.

Reads ``best_config.json`` and ``diagnostics.json`` under the loop output dir.
Does not run the solver.

Usage::

    python scripts/summarize_golden_loop_diagnostics.py
    python scripts/summarize_golden_loop_diagnostics.py --dir var/experiments/golden_loop
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_DIR = _REPO / "var" / "experiments" / "golden_loop"


def _load_json(path: Path) -> dict[str, object]:
    payload: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return payload


def render_markdown(*, out_dir: Path) -> str:
    best_path = out_dir / "best_config.json"
    diag_path = out_dir / "diagnostics.json"
    if not best_path.is_file():
        msg = f"missing {best_path}"
        raise FileNotFoundError(msg)
    if not diag_path.is_file():
        msg = f"missing {diag_path}"
        raise FileNotFoundError(msg)

    best = _load_json(best_path)
    diag = _load_json(diag_path)
    result = best.get("result", {})
    if not isinstance(result, dict):
        result = {}

    lines = [
        "## Golden loop diagnostics summary",
        "",
        f"- Output dir: `{out_dir.as_posix()}`",
        f"- Run count: `{diag.get('run_count')}`",
        f"- Best valid: `{diag.get('best_valid')}`",
        f"- Best score: `{diag.get('best_score')}`",
        "",
        "### Best config result",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in (
        "valid",
        "score",
        "miner_count",
        "belt_count",
        "routed_throughput",
        "anchor_f1_direct",
        "anchor_f1_normalized",
        "route_island_count",
        "orphan_count",
    ):
        lines.append(f"| `{key}` | `{result.get(key)}` |")

    diagnostics = result.get("diagnostics", [])
    lines.extend(
        [
            "",
            "### Run diagnostics",
            "",
        ],
    )
    bucket_rows: list[tuple[str, str]] = []
    reason_rows: list[tuple[str, str]] = []
    examples: list[str] = []
    other_diag: list[str] = []
    if isinstance(diagnostics, list):
        for item in diagnostics:
            text = str(item)
            if text.startswith("l5_failure_bucket:"):
                _, payload = text.split(":", 1)
                bucket, count = payload.rsplit("=", 1)
                bucket_rows.append((bucket, count))
            elif text.startswith("l5_failure_reason:"):
                _, payload = text.split(":", 1)
                reason, count = payload.rsplit("=", 1)
                reason_rows.append((reason, count))
            elif text.startswith("l5_failed_example:"):
                examples.append(text.removeprefix("l5_failed_example:"))
            else:
                other_diag.append(text)

    if other_diag:
        for item in other_diag:
            lines.append(f"- `{item}`")
    else:
        lines.append("- _(none)_")

    lines.extend(["", "### L5 failure bucket histogram", ""])
    if bucket_rows:
        lines.append("| Bucket | Count |")
        lines.append("| --- | --- |")
        for bucket, count in sorted(bucket_rows):
            lines.append(f"| `{bucket}` | `{count}` |")
    else:
        lines.append("- _(none)_")

    lines.extend(["", "### L5 failure reason histogram", ""])
    if reason_rows:
        lines.append("| Reason | Count |")
        lines.append("| --- | --- |")
        for reason, count in sorted(reason_rows):
            lines.append(f"| `{reason}` | `{count}` |")
    else:
        lines.append("- _(none)_")

    lines.extend(["", "### L5 failed source examples", ""])
    if examples:
        for example in examples:
            lines.append(f"- `{example}`")
    else:
        lines.append("- _(none)_")

    patterns = diag.get("failure_patterns", {})
    lines.extend(["", "### Failure patterns", ""])
    if isinstance(patterns, dict) and patterns:
        lines.append("| Pattern | Count |")
        lines.append("| --- | --- |")
        for pattern, count in sorted(patterns.items()):
            lines.append(f"| `{pattern}` | `{count}` |")
    else:
        lines.append("- _(none)_")

    best_copy = out_dir / "best_result.shapez.txt"
    lines.extend(
        [
            "",
            "### Export",
            "",
            f"- `best_result.shapez.txt`: `{'present' if best_copy.is_file() else 'absent'}`",
        ],
    )
    if not best_copy.is_file() and result.get("valid") is False:
        lines.append("- Absent is expected when no valid run exists (`--write-best-copy` opt-in).")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize golden loop diagnostics as markdown")
    parser.add_argument(
        "--dir",
        default=str(_DEFAULT_DIR),
        help="Golden loop output directory",
    )
    args = parser.parse_args(argv)
    print(render_markdown(out_dir=Path(args.dir)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
