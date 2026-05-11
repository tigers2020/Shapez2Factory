#!/usr/bin/env python3
"""Pass12 preserve stub recovery OFF vs ON (same merged-seed / same decoded BP input).

Default: synthetic merged-seed fixture + greenfield striped ``build_solver_timeline`` smoke.

With ``--copy-code-file`` or ``--ndjson``: runs full ``build_solver_timeline(decoded)`` twice
(recovery OFF vs ON) and writes comparison to ``var/pass12_recovery_ab_experiment.json``.

``--ndjson`` accepts (1) a single JSON object with top-level ``BP``, or (2) NDJSON where at
least one line parses to an object containing ``BP`` (e.g. a pasted decoded line). Standard
solver debug NDJSON without a ``BP`` line cannot be replayed; use ``*_decoded.json`` or
``--copy-code-file`` instead.

``--solver-trace PATH`` scans the same way for a ``BP`` object (optional ``--run-id`` filters
lines that carry ``run_id``). If the trace file has no blueprint line, pair with
``--bp-json PATH`` (decoded blueprint) while still attaching trace metadata when possible.

Use ``--full`` to write untruncated ``pass12_preserved_missing_stub_drop_details`` and
``pass12_preserved_recovery_traces`` in the JSON (default caps: see module constants).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.test import override_settings  # noqa: E402

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (  # noqa: E402
    MAX_PASS12_RECOVERY_BFS_HOPS,
    MAX_PASS12_RECOVERY_PROBES_PER_MINER,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import (  # noqa: E402
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (  # noqa: E402
    pass12_bundle_commit,
    pass12_merged_layout_seed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (  # noqa: E402
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (  # noqa: E402
    pass12_ab_metrics,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (  # noqa: E402
    PRESERVE_QUALITY_SCORE_VERSION,
    preserve_quality_bundle_from_pass12,
)
from django_apps.shapez_core.services.shapez_copy_decode import (  # noqa: E402
    ShapezCopyDecodeError,
    decode_shapez2_copy_trace,
)

Pass12LayoutScratch = pass12_bundle_commit.Pass12LayoutScratch
seed_pass12 = pass12_merged_layout_seed.seed_pass12_scratch_from_merged_existing

# Greenfield miners + belts (mirrors replay_v3 step4 transaction unit test).
_STRIPED_BP: dict[str, object] = {
    "BP": {
        "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
        + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
    }
}

_OUT_PATH = ROOT / "var" / "pass12_recovery_ab_experiment.json"
_TRACE_LIST_LIMIT = 32
_DROP_DETAILS_LIMIT = 32


def _has_bp(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    bp = obj.get("BP")
    return isinstance(bp, dict) and "Entries" in bp


def _iter_ndjson_objects(path: Path, *, run_id: str | None) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"empty file: {path}")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: invalid JSON ({e})") from e
        if not isinstance(row, dict):
            continue
        if run_id is not None and row.get("run_id") != run_id:
            continue
        rows.append(row)
    return rows


def load_decoded_from_ndjson_or_json(path: Path) -> dict[str, Any]:
    """Load decoded blueprint: whole-file JSON, or last NDJSON line whose root has ``BP``."""

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"empty file: {path}")
    try:
        one = json.loads(raw)
    except json.JSONDecodeError:
        one = None
    if isinstance(one, dict) and _has_bp(one):
        return one

    last_bp: dict[str, Any] | None = None
    for line_no, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_no}: invalid JSON ({e})") from e
        if _has_bp(row):
            last_bp = row
    if last_bp is None:
        raise ValueError(
            f"no object with top-level 'BP'.Entries in {path}. "
            "Solver trace NDJSON often has no blueprint; use copy-preview *_decoded.json "
            "or --copy-code-file with SHAPEZ2-4-... copy text."
        )
    return last_bp


def load_decoded_from_copy_code_file(path: Path) -> dict[str, Any]:
    code = path.read_text(encoding="utf-8")
    trace = decode_shapez2_copy_trace(code)
    if not trace.success or trace.data is None:
        raise ShapezCopyDecodeError(trace.error or "decode failed")
    if not _has_bp(trace.data):
        raise ShapezCopyDecodeError("decoded JSON has no BP.Entries")
    return trace.data


def load_decoded_from_solver_trace_ndjson(
    path: Path,
    *,
    run_id: str | None = None,
    bp_json: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load blueprint for A/B: from ``bp_json``, or first matching ``BP`` line in trace NDJSON.

    Returns ``(decoded, trace_meta)``. ``trace_meta`` may include a ``solver_summary`` excerpt.
    """

    trace_meta: dict[str, Any] = {"trace_path": str(path.resolve()), "run_id_filter": run_id}
    rows = _iter_ndjson_objects(path, run_id=run_id)
    last_bp: dict[str, Any] | None = None
    solver_summary: dict[str, Any] | None = None
    trace_run_id: str | None = None
    for row in rows:
        if _has_bp(row):
            last_bp = row
        if row.get("kind") == "trace" and row.get("message") == "solver_summary":
            data = row.get("data")
            if isinstance(data, dict):
                ss = data.get("solver_summary")
                if isinstance(ss, dict):
                    solver_summary = ss
                    rid = row.get("run_id")
                    if isinstance(rid, str) and rid:
                        trace_run_id = rid
                    inner = ss.get("run_id")
                    if isinstance(inner, str) and inner:
                        trace_run_id = inner
    if bp_json is not None:
        decoded = load_decoded_from_ndjson_or_json(bp_json.resolve())
        trace_meta["bp_source"] = str(bp_json.resolve())
    elif last_bp is not None:
        decoded = last_bp
        trace_meta["bp_source"] = "embedded_in_trace"
    else:
        raise ValueError(
            f"No BP.Entries in {path} after optional run_id filter. "
            "Pass --bp-json with a *_decoded.json (or --ndjson / --copy-code-file)."
        )
    if trace_run_id is not None:
        trace_meta["trace_run_id"] = trace_run_id
    if solver_summary is not None:
        trace_meta["solver_summary_excerpt"] = {
            "pass12_preserved_missing_stub_drop_extractor_count": solver_summary.get(
                "pass12_preserved_missing_stub_drop_extractor_count"
            ),
            "pass12_preserve_drop_reason_counts": dict(
                solver_summary.get("pass12_preserve_drop_reason_counts") or {}
            ),
            "pass12_recoverability_class_counts": dict(
                solver_summary.get("pass12_recoverability_class_counts") or {}
            ),
            "preserve_quality_score": solver_summary.get("preserve_quality_score"),
            "preserve_quality_score_version": solver_summary.get(
                "preserve_quality_score_version", PRESERVE_QUALITY_SCORE_VERSION
            ),
            "step4_routing_failure_count": solver_summary.get("step4_routing_failure_count"),
            "missing_stub_count": solver_summary.get("missing_stub_count"),
        }
    return decoded, trace_meta


def _relaxed_recovery_fixture() -> tuple[frozenset[Coord], list[dict[str, object]]]:
    """One miner recoverable via relaxed stub + rotation when recovery flag is ON."""

    mineable: frozenset[Coord] = frozenset({(1, 0), (1, 1), (2, 1), (5, 1)})
    rows: list[dict[str, object]] = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 2,
            "surface": "fluid",
        },
        {"x": 2, "y": 1, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {
            "x": 1,
            "y": 0,
            "role": "occupied",
            "layout_kind": "fluid_pipe",
            "surface": "fluid",
        },
        {
            "x": 5,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
    ]
    return mineable, rows


def _metrics(stats: dict[str, object]) -> dict[str, object]:
    drop = int(stats.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    rec = int(stats.get("pass12_preserved_recovery_success_count") or 0)
    pq, pqs = preserve_quality_bundle_from_pass12(stats)
    return {
        "pass12_preserved_missing_stub_drop_extractor_count": drop,
        "pass12_preserve_drop_reason_counts": dict(
            stats.get("pass12_preserve_drop_reason_counts") or {}
        ),
        "pass12_preserved_recovery_success_count": rec,
        "pass12_preserved_recovery_traces": list(
            stats.get("pass12_preserved_recovery_traces") or []
        ),
        "preserve_quality": pq,
        "preserve_quality_score": pqs,
    }


def _run_merged_seed_synthetic(recovery_flag: bool) -> dict[str, object]:
    mineable, rows = _relaxed_recovery_fixture()
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    with override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=recovery_flag):
        stats = seed_pass12(
            rows,
            mineable=mineable,
            scratch=scratch,
            existing_layout_source_kind="existing_fluid_layout",
        )
    return _metrics(stats)


def _timeline_guard_fields(decoded: dict[str, Any], recovery_flag: bool) -> dict[str, Any]:
    """Full drop_details and recovery_traces for join; trim with ``_trim_timeline_heavy``."""

    with override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=recovery_flag):
        out = build_solver_timeline(decoded)
    s = out["solver_summary"]
    drops = s.get("pass12_preserved_missing_stub_drop_details") or []
    traces = s.get("pass12_preserved_recovery_traces") or []
    return {
        "return_reason": s.get("return_reason"),
        "solver_termination": s.get("solver_termination"),
        "geometry_valid": s.get("geometry_valid"),
        "connectivity_valid": s.get("connectivity_valid"),
        "missing_stub_count": s.get("missing_stub_count"),
        "step4_routing_failure_count": s.get("step4_routing_failure_count"),
        "step4_committed": s.get("step4_committed"),
        "preserve_quality_score": s.get("preserve_quality_score"),
        "preserve_quality": s.get("preserve_quality"),
        "preserve_quality_score_version": s.get(
            "preserve_quality_score_version", PRESERVE_QUALITY_SCORE_VERSION
        ),
        "pass12_preserved_missing_stub_drop_extractor_count": s.get(
            "pass12_preserved_missing_stub_drop_extractor_count"
        ),
        "pass12_preserve_drop_reason_counts": dict(
            s.get("pass12_preserve_drop_reason_counts") or {}
        ),
        "pass12_recoverability_class_counts": dict(
            s.get("pass12_recoverability_class_counts") or {}
        ),
        "pass12_preserved_recovery_success_count": s.get("pass12_preserved_recovery_success_count"),
        "pass12_preserved_recovery_traces": list(traces),
        "pass12_preserved_missing_stub_drop_details": list(drops),
    }


def _trim_timeline_heavy(row: dict[str, Any], *, full: bool) -> dict[str, Any]:
    if full:
        return dict(row)
    out = dict(row)
    drops = list(out.get("pass12_preserved_missing_stub_drop_details") or [])
    traces = list(out.get("pass12_preserved_recovery_traces") or [])
    out["pass12_preserved_missing_stub_drop_details"] = drops[:_DROP_DETAILS_LIMIT]
    out["pass12_preserved_recovery_traces"] = traces[:_TRACE_LIST_LIMIT]
    return out


def _build_ab_digest(
    source: dict[str, Any],
    gates: dict[str, Any],
    diff_timeline: dict[str, Any],
    outcome: dict[str, Any],
    b_off: dict[str, Any],
    b_on: dict[str, Any],
) -> dict[str, Any]:
    s4_off = b_off.get("step4_routing_failure_count")
    s4_on = b_on.get("step4_routing_failure_count")
    s4_delta: int | None = None
    if isinstance(s4_off, int) and isinstance(s4_on, int):
        s4_delta = s4_on - s4_off
    pq_ver = b_off.get("preserve_quality_score_version", PRESERVE_QUALITY_SCORE_VERSION)
    return {
        "run_id_filter": source.get("run_id_filter"),
        "trace_run_id": source.get("trace_run_id"),
        "input_source_kind": source.get("kind"),
        "input_path": source.get("path") or source.get("trace_path"),
        "recovery_default_on_candidate": gates.get("recovery_default_on_candidate"),
        "recovery_safe_gate": gates.get("recovery_safe_gate"),
        "preserve_quality_score_delta": gates.get("preserve_quality_score_delta"),
        "stub_drop_delta": gates.get("stub_drop_delta"),
        "step4_routing_failure_delta": s4_delta,
        "diff_timeline_keys": sorted(diff_timeline.keys()),
        "recoverability_outcome_counts": outcome.get("recoverability_outcome_counts"),
        "recoverability_outcome_by_class": outcome.get("recoverability_outcome_by_class"),
        "recovery_rate_by_class": outcome.get("recovery_rate_by_class"),
        "recovery_candidate_fraction": outcome.get("recovery_candidate_fraction"),
        "recovery_candidate_count": outcome.get("recovery_candidate_count"),
        "recovery_candidate_denominator": outcome.get("recovery_candidate_denominator"),
        "preserve_quality_score_version": pq_ver,
    }


def _recovery_ab_histograms(b: dict[str, Any]) -> dict[str, Any]:
    return {
        "pass12_preserve_drop_reason_counts": dict(
            b.get("pass12_preserve_drop_reason_counts") or {}
        ),
        "pass12_recoverability_class_counts": dict(
            b.get("pass12_recoverability_class_counts") or {}
        ),
    }


def _recovery_safe_gate_bundle(b_off: dict[str, Any], b_on: dict[str, Any]) -> dict[str, Any]:
    """Conservative default-ON candidate: unchanged geometry/connectivity/failures + PQS up."""

    def _eq(key: str) -> bool:
        return b_off.get(key) == b_on.get(key)

    ms_off = int(b_off.get("missing_stub_count") or 0)
    ms_on = int(b_on.get("missing_stub_count") or 0)
    missing_stub_unchanged_or_zero = (ms_off == ms_on) and (ms_on == 0)

    score_off = b_off.get("preserve_quality_score")
    score_on = b_on.get("preserve_quality_score")
    try:
        score_delta = (
            float(score_on) - float(score_off)
            if score_off is not None and score_on is not None
            else None
        )
    except (TypeError, ValueError):
        score_delta = None
    preserve_quality_improved = bool(score_delta is not None and score_delta > 0)

    gate = {
        "geometry_unchanged": _eq("geometry_valid"),
        "connectivity_unchanged": _eq("connectivity_valid"),
        "step4_failures_unchanged": _eq("step4_routing_failure_count"),
        "missing_stub_unchanged_or_zero": missing_stub_unchanged_or_zero,
        "preserve_quality_improved": preserve_quality_improved,
    }
    candidate = all(gate.values())
    drop_off = int(b_off.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    drop_on = int(b_on.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    return {
        "recovery_safe_gate": gate,
        "recovery_default_on_candidate": candidate,
        "preserve_quality_score_delta": score_delta,
        "stub_drop_delta": drop_on - drop_off,
    }


def _diff_timeline(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "return_reason",
        "geometry_valid",
        "connectivity_valid",
        "missing_stub_count",
        "step4_routing_failure_count",
        "step4_committed",
        "preserve_quality_score",
        "preserve_quality_score_version",
        "pass12_preserved_missing_stub_drop_extractor_count",
        "pass12_preserved_recovery_success_count",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if a.get(k) != b.get(k):
            out[k] = {"off": a.get(k), "on": b.get(k)}
    return out


def _write_and_print(payload: dict[str, Any], diff: dict[str, Any]) -> int:
    out_dir = ROOT / "var"
    out_dir.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(_OUT_PATH), "diff": diff}, indent=2))
    return 0


def _main_default(*, full: bool = False) -> int:
    baseline = _run_merged_seed_synthetic(False)
    recovery_on = _run_merged_seed_synthetic(True)
    diff = {
        "drop_delta": int(recovery_on["pass12_preserved_missing_stub_drop_extractor_count"])
        - int(baseline["pass12_preserved_missing_stub_drop_extractor_count"]),
        "recovery_success_delta": int(recovery_on["pass12_preserved_recovery_success_count"])
        - int(baseline["pass12_preserved_recovery_success_count"]),
        "preserve_quality_score_baseline": baseline["preserve_quality_score"],
        "preserve_quality_score_recovery_on": recovery_on["preserve_quality_score"],
    }
    spotcheck_note = (
        "recovery_traces_on lists provenance per recovered miner (relaxed_stub_coords, "
        "recovered_rotation)."
    )
    if diff["recovery_success_delta"] == 0 and diff["drop_delta"] == 0:
        spotcheck_note += (
            f" No delta for this fixture: check MAX_PASS12_RECOVERY_BFS_HOPS="
            f"{MAX_PASS12_RECOVERY_BFS_HOPS}, MAX_PASS12_RECOVERY_PROBES_PER_MINER="
            f"{MAX_PASS12_RECOVERY_PROBES_PER_MINER} in foundation/constants.py."
        )
    tl_off = _timeline_guard_fields(_STRIPED_BP, False)
    tl_on = _timeline_guard_fields(_STRIPED_BP, True)
    tl_diff = {k: (tl_on[k] != tl_off[k]) for k in tl_off if k in tl_on}
    gates_tl = _recovery_safe_gate_bundle(tl_off, tl_on)
    outcome_tl = pass12_ab_metrics.recoverability_ab_outcome_bundle(tl_off, tl_on)
    digest_tl = _build_ab_digest(
        {"kind": "synthetic_default", "run_id_filter": None},
        gates_tl,
        {},
        outcome_tl,
        tl_off,
        tl_on,
    )

    payload = {
        "ab_digest": digest_tl,
        "recoverability_outcome_counts": outcome_tl["recoverability_outcome_counts"],
        "recoverability_outcome_by_class": outcome_tl.get("recoverability_outcome_by_class"),
        "recovery_rate_by_class": outcome_tl["recovery_rate_by_class"],
        "input_source": {"kind": "synthetic_default"},
        "fixture": "relaxed_stub_recovery_synthetic",
        "baseline_recovery_off": baseline,
        "recovery_on": recovery_on,
        "diff": diff,
        "trace_spotcheck": spotcheck_note,
        **gates_tl,
        "full_pipeline_smoke_striped_bp": {
            "note": (
                "Greenfield blueprint; pass12 recovery flag should not change geometry/step4 "
                "regression gates vs itself."
            ),
            "baseline_recovery_off": _trim_timeline_heavy(tl_off, full=full),
            "recovery_on": _trim_timeline_heavy(tl_on, full=full),
            "field_changed_recovery_on_vs_off": {k: v for k, v in tl_diff.items() if v},
        },
    }
    return _write_and_print(payload, diff)


def _main_decoded(decoded: dict[str, Any], source: dict[str, Any], *, full: bool = False) -> int:
    b_off = _timeline_guard_fields(decoded, False)
    b_on = _timeline_guard_fields(decoded, True)
    diff = _diff_timeline(b_off, b_on)
    gates = _recovery_safe_gate_bundle(b_off, b_on)
    outcome = pass12_ab_metrics.recoverability_ab_outcome_bundle(b_off, b_on)
    digest = _build_ab_digest(source, gates, diff, outcome, b_off, b_on)
    payload = {
        "ab_digest": digest,
        "recoverability_outcome_counts": outcome["recoverability_outcome_counts"],
        "recoverability_outcome_by_class": outcome.get("recoverability_outcome_by_class"),
        "recovery_rate_by_class": outcome["recovery_rate_by_class"],
        "input_source": source,
        "baseline_recovery_off": _trim_timeline_heavy(b_off, full=full),
        "recovery_on": _trim_timeline_heavy(b_on, full=full),
        "diff_timeline_off_vs_on": diff,
        **gates,
        "histograms": {
            "baseline_recovery_off": _recovery_ab_histograms(b_off),
            "recovery_on": _recovery_ab_histograms(b_on),
        },
    }
    s4_off = b_off.get("step4_routing_failure_count")
    s4_on = b_on.get("step4_routing_failure_count")
    s4_delta = None
    if isinstance(s4_off, int) and isinstance(s4_on, int):
        s4_delta = s4_on - s4_off
    summary_diff = {
        "drop_delta": int(b_on["pass12_preserved_missing_stub_drop_extractor_count"] or 0)
        - int(b_off["pass12_preserved_missing_stub_drop_extractor_count"] or 0),
        "recovery_success_delta": int(b_on["pass12_preserved_recovery_success_count"] or 0)
        - int(b_off["pass12_preserved_recovery_success_count"] or 0),
        "preserve_quality_score_baseline": b_off.get("preserve_quality_score"),
        "preserve_quality_score_recovery_on": b_on.get("preserve_quality_score"),
        "preserve_quality_score_delta": gates.get("preserve_quality_score_delta"),
        "step4_routing_failure_delta": s4_delta,
        "recovery_default_on_candidate": gates.get("recovery_default_on_candidate"),
        "recovery_safe_gate": gates.get("recovery_safe_gate"),
    }
    return _write_and_print(payload, summary_diff)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--copy-code-file",
        type=Path,
        metavar="PATH",
        help="Text file with SHAPEZ2-4-... copy string (whitespace allowed).",
    )
    src.add_argument(
        "--ndjson",
        type=Path,
        metavar="PATH",
        help="Single JSON with BP, or NDJSON containing a line with BP (e.g. *_decoded.json).",
    )
    src.add_argument(
        "--solver-trace",
        type=Path,
        metavar="PATH",
        help="Solver debug NDJSON; use with BP in file or with --bp-json.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        metavar="ID",
        help="Only NDJSON lines with this run_id (optional; --solver-trace / strict trace scan).",
    )
    parser.add_argument(
        "--bp-json",
        type=Path,
        default=None,
        metavar="PATH",
        help="Decoded blueprint JSON when --solver-trace has no embedded BP line.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include full pass12 drop_details and recovery_traces in JSON (default: truncated).",
    )
    args = parser.parse_args()

    try:
        if args.solver_trace:
            decoded, trace_meta = load_decoded_from_solver_trace_ndjson(
                args.solver_trace.resolve(),
                run_id=args.run_id,
                bp_json=args.bp_json.resolve() if args.bp_json else None,
            )
            src_meta: dict[str, Any] = {
                "kind": "solver_trace_ndjson",
                "path": str(args.solver_trace.resolve()),
            }
            src_meta.update(trace_meta)
            return _main_decoded(decoded, src_meta, full=args.full)
        if args.copy_code_file:
            decoded = load_decoded_from_copy_code_file(args.copy_code_file.resolve())
            return _main_decoded(
                decoded,
                {"kind": "copy_code_file", "path": str(args.copy_code_file.resolve())},
                full=args.full,
            )
        if args.ndjson:
            decoded = load_decoded_from_ndjson_or_json(args.ndjson.resolve())
            return _main_decoded(
                decoded,
                {"kind": "ndjson_or_json", "path": str(args.ndjson.resolve())},
                full=args.full,
            )
    except (OSError, ValueError, ShapezCopyDecodeError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return _main_default(full=args.full)


if __name__ == "__main__":
    raise SystemExit(main())
