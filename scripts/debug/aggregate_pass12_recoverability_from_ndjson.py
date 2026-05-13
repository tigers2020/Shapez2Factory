#!/usr/bin/env python3
"""Aggregate Pass12 preserve / recoverability fields from solver NDJSON (replay or legacy).

Each NDJSON line that represents a ``solver_summary`` trace contributes one row:

- **Legacy** (debug file): ``kind`` == ``trace`` and ``message`` == ``solver_summary``.
- **Replay wire** (replay file): ``message`` == ``solver_summary`` and ``data.solver_summary``
  (``location`` / ``message`` / ``data`` shape; no ``kind``).

**Contract (important)**:

- ``recovery_rate_by_class`` and per-class OFF→ON **recovered** counts require the
  same blueprint run twice (recovery OFF vs ON). A single production trace cannot
  compute that; use ``scripts/debug/pass12_preserve_recovery_ab.py`` for A/B join metrics.
- This script only aggregates **per-run summaries**: class histograms, drop reason
  counts, ``preserve_quality_score`` distribution, ``existing_layout_source_kind``
  breakdown, and PQS version histograms.

Examples (from repo root)::

  python scripts/debug/aggregate_pass12_recoverability_from_ndjson.py PATH.ndjson
  python scripts/debug/aggregate_pass12_recoverability_from_ndjson.py DEBUG_DIR --max-files 50

Optional ``--run-id`` filters lines whose top-level ``run_id`` or ``data.run_id`` matches.

Output includes ``total_runs`` (same meaning as ``solver_summary_rows_used``: number
of matching solver_summary lines scanned). With ``--split-by-ndjson-run-id``,
``pass12_recoverability_class_counts_by_ndjson_run_id`` is still emitted; global
``class_counts`` remains the merge across all those lines.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import solver_trace_ndjson_read as _trace_read  # noqa: E402


def _merge_class_counts(acc: dict[str, int], raw: Any) -> None:
    if not isinstance(raw, dict):
        return
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        try:
            acc[k] = acc.get(k, 0) + int(v)
        except (TypeError, ValueError):
            continue


def _float_pqs(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        if isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw)):
            return None
        return float(raw)
    return None


def _linear_percentile(sorted_vals: list[float], pct: float) -> float | None:
    """Linear interpolation percentile; ``pct`` in [0, 100]."""

    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    if pct <= 0:
        return sorted_vals[0]
    if pct >= 100:
        return sorted_vals[-1]
    pos = (pct / 100.0) * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    w = pos - lo
    return sorted_vals[lo] + w * (sorted_vals[hi] - sorted_vals[lo])


def _iter_ndjson_lines(path: Path) -> Iterator[tuple[int, str]]:
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            s = line.strip()
            if s:
                yield line_no, s


def _extract_solver_summary_row(
    row: dict[str, Any], *, run_id: str | None
) -> dict[str, Any] | None:
    return _trace_read.extract_solver_summary_from_ndjson_row(row, run_id=run_id)


def _source_kind_key(ss: dict[str, Any]) -> str:
    raw = ss.get("existing_layout_source_kind")
    if isinstance(raw, str) and raw:
        return raw
    return "unknown"


@dataclass
class _AggBucket:
    class_counts: dict[str, int] = field(default_factory=dict)
    reason_counts: dict[str, int] = field(default_factory=dict)
    pqs_samples: list[float] = field(default_factory=list)
    version_hist: dict[str, int] = field(default_factory=dict)
    rows: int = 0

    def ingest(self, ss: dict[str, Any]) -> None:
        self.rows += 1
        _merge_class_counts(self.class_counts, ss.get("pass12_recoverability_class_counts"))
        _merge_class_counts(self.reason_counts, ss.get("pass12_preserve_drop_reason_counts"))
        pqs = _float_pqs(ss.get("preserve_quality_score"))
        if pqs is not None:
            self.pqs_samples.append(pqs)
        ver = ss.get("preserve_quality_score_version")
        if ver is None:
            vkey = "null"
        elif isinstance(ver, bool):
            vkey = str(ver)
        elif isinstance(ver, (int, float)):
            vkey = str(int(ver))
        elif isinstance(ver, str):
            vkey = ver or "null"
        else:
            vkey = str(ver)
        self.version_hist[vkey] = self.version_hist.get(vkey, 0) + 1


def _bucket_summary(bucket: _AggBucket) -> dict[str, Any]:
    sorted_pqs = sorted(bucket.pqs_samples)
    n = len(sorted_pqs)
    avg: float | None = None
    if n:
        avg = round(sum(sorted_pqs) / n, 6)
    pct: dict[str, float | None] = {
        "p50": None if not sorted_pqs else round(_linear_percentile(sorted_pqs, 50.0) or 0.0, 6),
        "p90": None if not sorted_pqs else round(_linear_percentile(sorted_pqs, 90.0) or 0.0, 6),
        "p99": None if not sorted_pqs else round(_linear_percentile(sorted_pqs, 99.0) or 0.0, 6),
    }
    return {
        "solver_summary_rows": bucket.rows,
        "class_counts": dict(sorted(bucket.class_counts.items(), key=lambda kv: kv[0])),
        "reason_counts": dict(sorted(bucket.reason_counts.items(), key=lambda kv: kv[0])),
        "avg_preserve_quality_score": avg,
        "preserve_quality_score_percentiles": pct,
        "preserve_quality_score_version_counts": dict(
            sorted(bucket.version_hist.items(), key=lambda kv: kv[0])
        ),
    }


def scan_ndjson_file_full_metrics(
    path: Path, *, run_id: str | None
) -> tuple[_AggBucket, dict[str, _AggBucket], int]:
    """Return (global bucket, per-source_kind buckets, rows used)."""

    global_b = _AggBucket()
    by_kind: dict[str, _AggBucket] = defaultdict(_AggBucket)
    used = 0
    for line_no, s in _iter_ndjson_lines(path):
        try:
            row = json.loads(s)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: invalid JSON ({e})") from e
        if not isinstance(row, dict):
            continue
        ss = _extract_solver_summary_row(row, run_id=run_id)
        if ss is None:
            continue
        used += 1
        global_b.ingest(ss)
        sk = _source_kind_key(ss)
        by_kind[sk].ingest(ss)
    return global_b, dict(sorted(by_kind.items(), key=lambda kv: kv[0])), used


def scan_ndjson_file_full_metrics_per_trace_run(
    path: Path, *, run_id: str | None
) -> tuple[_AggBucket, dict[str, _AggBucket], int, dict[str, dict[str, int]]]:
    """Global + source_kind + per ndjson run_id class counts."""

    global_b = _AggBucket()
    by_kind: dict[str, _AggBucket] = defaultdict(_AggBucket)
    per_trace_class: dict[str, dict[str, int]] = defaultdict(dict)
    used = 0
    for line_no, s in _iter_ndjson_lines(path):
        try:
            row = json.loads(s)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: invalid JSON ({e})") from e
        if not isinstance(row, dict):
            continue
        ss = _extract_solver_summary_row(row, run_id=run_id)
        if ss is None:
            continue
        used += 1
        global_b.ingest(ss)
        sk = _source_kind_key(ss)
        by_kind[sk].ingest(ss)
        tr = _trace_read.row_trace_run_id(row)
        if tr:
            _merge_class_counts(per_trace_class[tr], ss.get("pass12_recoverability_class_counts"))
    per_sorted = {k: dict(sorted(v.items())) for k, v in sorted(per_trace_class.items())}
    return global_b, dict(sorted(by_kind.items(), key=lambda kv: kv[0])), used, per_sorted


def _list_ndjson_files(root: Path, *, recursive: bool) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        raise ValueError(f"not a file or directory: {root}")
    if recursive:
        paths = sorted(root.rglob("*.ndjson"), key=lambda p: str(p))
    else:
        paths = sorted(root.glob("*.ndjson"), key=lambda p: str(p))
    return [p for p in paths if p.is_file()]


def _merge_agg_bucket(dst: _AggBucket, src: _AggBucket) -> None:
    _merge_class_counts(dst.class_counts, src.class_counts)
    _merge_class_counts(dst.reason_counts, src.reason_counts)
    dst.pqs_samples.extend(src.pqs_samples)
    for k, v in src.version_hist.items():
        dst.version_hist[k] = dst.version_hist.get(k, 0) + v
    dst.rows += src.rows


def _merge_kind_maps(acc: dict[str, _AggBucket], fragment: dict[str, _AggBucket]) -> None:
    for k, b in fragment.items():
        if k not in acc:
            acc[k] = _AggBucket()
        _merge_agg_bucket(acc[k], b)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="NDJSON file or directory of *.ndjson files",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        metavar="ID",
        help="Only aggregate lines with this run_id (top-level or data.run_id)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        metavar="N",
        help="When path is a directory, scan at most N files (sorted by path)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="When path is a directory, include *.ndjson in subdirectories",
    )
    parser.add_argument(
        "--split-by-ndjson-run-id",
        action="store_true",
        dest="split_by_ndjson_run_id",
        help=(
            "Include pass12_recoverability_class_counts_by_ndjson_run_id "
            "(group by run_id: top-level or data.run_id on each trace line)"
        ),
    )
    args = parser.parse_args()
    root = args.path.resolve()

    try:
        files = _list_ndjson_files(root, recursive=args.recursive)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.max_files is not None:
        files = files[: max(0, args.max_files)]

    global_b = _AggBucket()
    kind_map: dict[str, _AggBucket] = {}
    merged_per_run: dict[str, dict[str, int]] = defaultdict(dict)
    rows_used = 0

    for fp in files:
        if args.split_by_ndjson_run_id:
            g, kinds, n, per_file = scan_ndjson_file_full_metrics_per_trace_run(
                fp, run_id=args.run_id
            )
            rows_used += n
            _merge_agg_bucket(global_b, g)
            _merge_kind_maps(kind_map, kinds)
            for tr, hist in per_file.items():
                _merge_class_counts(merged_per_run[tr], hist)
        else:
            g, kinds, n = scan_ndjson_file_full_metrics(fp, run_id=args.run_id)
            rows_used += n
            _merge_agg_bucket(global_b, g)
            _merge_kind_maps(kind_map, kinds)

    global_summary = _bucket_summary(global_b)
    source_breakdown = {
        k: _bucket_summary(v) for k, v in sorted(kind_map.items(), key=lambda kv: kv[0])
    }

    out: dict[str, Any] = {
        "total_runs": rows_used,
        "solver_summary_rows_used": rows_used,
        "pass12_recoverability_class_counts": global_summary["class_counts"],
        "class_counts": global_summary["class_counts"],
        "pass12_preserve_drop_reason_counts": global_summary["reason_counts"],
        "reason_counts": global_summary["reason_counts"],
        "avg_preserve_quality_score": global_summary["avg_preserve_quality_score"],
        "preserve_quality_score_percentiles": global_summary["preserve_quality_score_percentiles"],
        "preserve_quality_score_version_counts": global_summary[
            "preserve_quality_score_version_counts"
        ],
        "source_kind_breakdown": source_breakdown,
        "files_scanned": len(files),
        "paths": [str(p) for p in files],
    }
    if args.split_by_ndjson_run_id:
        out["pass12_recoverability_class_counts_by_ndjson_run_id"] = {
            k: dict(sorted(v.items(), key=lambda kv: kv[0]))
            for k, v in sorted(merged_per_run.items())
        }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(2) from e
