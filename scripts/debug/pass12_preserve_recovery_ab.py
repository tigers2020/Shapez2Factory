#!/usr/bin/env python3
"""Pass12 preserve stub recovery OFF vs ON (same merged-seed / same decoded BP input).

Default: synthetic merged-seed fixture + greenfield striped ``build_solver_timeline`` smoke.

With ``--copy-code-file`` or ``--ndjson``: runs full ``build_solver_timeline(decoded)`` twice
(recovery OFF vs ON) and writes comparison to ``var/pass12_recovery_ab_experiment.json``.

With ``--stub-route-recovery-ab``: same inputs, but compares
``SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=False`` vs ``True`` while holding
``SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True`` (isolates stub-route recovery). Writes
``var/pass12_stub_route_recovery_ab_experiment.json``.

With ``--stub-route-cap-ab``: runs the same decoded input with
``MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS`` variants (default: 6,8,10). Writes
``var/pass12_stub_route_recovery_cap_ab_experiment.json``.

``--ndjson`` accepts (1) a single JSON object with top-level ``BP``, or (2) NDJSON where at
least one line parses to an object containing ``BP`` (e.g. a pasted decoded line). Standard
solver debug NDJSON without a ``BP`` line cannot be replayed; use ``*_decoded.json`` or
``--copy-code-file`` instead.

``--solver-trace PATH`` scans the same way for a ``BP`` object (optional ``--run-id``
filters lines whose top-level ``run_id`` or ``data.run_id`` matches). If the trace file has no
blueprint line, pair with
``--bp-json PATH`` (decoded blueprint) while still attaching trace metadata when possible.
``--bp-json`` alone loads a single decoded JSON object (same shape as ``*_decoded.json``).

Use ``--full`` to write untruncated ``pass12_preserved_missing_stub_drop_details`` and
``pass12_preserved_recovery_traces`` in the JSON (default caps: see module constants).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
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
    pass12_preserve_stub_route_recovery,
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

_SCRIPT_DEBUG = Path(__file__).resolve().parent
if str(_SCRIPT_DEBUG) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DEBUG))

import solver_trace_ndjson_read as _trace_read  # noqa: E402

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
_OUT_PATH_STUB_ROUTE_AB = ROOT / "var" / "pass12_stub_route_recovery_ab_experiment.json"
_OUT_PATH_STUB_ROUTE_CAP_AB = ROOT / "var" / "pass12_stub_route_recovery_cap_ab_experiment.json"
_TRACE_LIST_LIMIT = 32
_DROP_DETAILS_LIMIT = 32

_STUB_ROUTE_AB_SUMMARY_KEYS = (
    "pass12_preserved_missing_stub_route_recovery_attempted_count",
    "pass12_preserved_missing_stub_route_recovery_success_count",
    "pass12_preserved_missing_stub_route_recovery_queue_rounds",
    "pass12_preserved_missing_stub_drop_extractor_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_visit_cap_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_route_len_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count",
    "pass12_preserved_missing_stub_route_recovery_rejected_by_extension_carve_disabled_count",
    "pass12_preserved_rotation_recovery_count",
    "geometry_valid",
    "connectivity_valid",
    "missing_stub_count",
    "orphan_transport_count",
    "transport_connected",
    "preserve_quality_score_version",
    "preserve_quality_score",
    "extractor_count",
    "pass12_preserved_recovery_success_count",
)


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
        if run_id is not None and not _trace_read.run_id_matches_row(row, run_id):
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
        ss = _trace_read.extract_solver_summary_from_ndjson_row(row, run_id=None)
        if ss is not None:
            solver_summary = ss
            tid = _trace_read.row_trace_run_id(row)
            if isinstance(tid, str) and tid:
                trace_run_id = tid
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
            "pass12_preserved_missing_stub_route_recovery_attempted_count": solver_summary.get(
                "pass12_preserved_missing_stub_route_recovery_attempted_count"
            ),
            "pass12_preserved_missing_stub_route_recovery_success_count": solver_summary.get(
                "pass12_preserved_missing_stub_route_recovery_success_count"
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


def _metrics(stats: dict[str, object]) -> dict[str, Any]:
    s = cast(dict[str, Any], stats)
    drop = int(s.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    rec = int(s.get("pass12_preserved_recovery_success_count") or 0)
    pq, pqs = preserve_quality_bundle_from_pass12(s)
    return {
        "pass12_preserved_missing_stub_drop_extractor_count": drop,
        "pass12_preserve_drop_reason_counts": dict(
            s.get("pass12_preserve_drop_reason_counts") or {}
        ),
        "pass12_preserved_recovery_success_count": rec,
        "pass12_preserved_recovery_traces": list(s.get("pass12_preserved_recovery_traces") or []),
        "preserve_quality": pq,
        "preserve_quality_score": pqs,
    }


def _run_merged_seed_synthetic(recovery_flag: bool) -> dict[str, Any]:
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


def _stub_route_ab_timeline_row(decoded: dict[str, Any], *, route_flag: bool) -> dict[str, Any]:
    """Timeline row with relaxed stub recovery ON; toggles stub-route recovery only."""

    with override_settings(
        SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True,
        SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=route_flag,
    ):
        out = build_solver_timeline(decoded)
    s = out["solver_summary"]
    drops = s.get("pass12_preserved_missing_stub_drop_details") or []
    traces = s.get("pass12_preserved_recovery_traces") or []
    row: dict[str, Any] = {
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
        "extractor_count": s.get("extractor_count"),
        "original_extractor_count": s.get("original_extractor_count"),
        "final_extractor_count": s.get("final_extractor_count"),
        "extractor_drop_count": s.get("extractor_drop_count"),
        "transport_cell_count": s.get("transport_cell_count"),
        "optimization_final_internal_transport_count": s.get(
            "optimization_final_internal_transport_count"
        ),
        "internal_transport_delta_vs_baseline": s.get("internal_transport_delta_vs_baseline"),
        "solver_quality_tier": s.get("solver_quality_tier"),
        "orphan_transport_count": s.get("orphan_transport_count"),
        "transport_connected": s.get("transport_connected"),
    }
    for k in _STUB_ROUTE_AB_SUMMARY_KEYS:
        if k not in row and k in s:
            row[k] = s.get(k)
    pq = s.get("preserve_quality")
    if isinstance(pq, dict):
        row["preserve_quality_stub_route_recovery_success_count"] = pq.get(
            "stub_route_recovery_success_count"
        )
    return row


def _diff_stub_route_ab(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "return_reason",
        "geometry_valid",
        "connectivity_valid",
        "missing_stub_count",
        "orphan_transport_count",
        "transport_connected",
        "step4_routing_failure_count",
        "step4_committed",
        "preserve_quality_score",
        "preserve_quality_score_version",
        "pass12_preserved_missing_stub_drop_extractor_count",
        "pass12_preserved_recovery_success_count",
        "pass12_preserved_missing_stub_route_recovery_attempted_count",
        "pass12_preserved_missing_stub_route_recovery_success_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_visit_cap_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_route_len_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count",
        "pass12_preserved_missing_stub_route_recovery_rejected_by_extension_carve_disabled_count",
        "extractor_count",
        "preserve_quality_stub_route_recovery_success_count",
    )
    out: dict[str, Any] = {}
    for k in keys:
        if a.get(k) != b.get(k):
            out[k] = {"route_off": a.get(k), "route_on": b.get(k)}
    return out


def _stub_route_ab_decision_hint(b_off: dict[str, Any], b_on: dict[str, Any]) -> str:
    att = int(b_on.get("pass12_preserved_missing_stub_route_recovery_attempted_count") or 0)
    ok = int(b_on.get("pass12_preserved_missing_stub_route_recovery_success_count") or 0)
    geo = b_on.get("geometry_valid") is True
    conn = b_on.get("connectivity_valid") is True
    ms = int(b_on.get("missing_stub_count") or 0)
    ot = int(b_on.get("orphan_transport_count") or 0)
    tc = b_on.get("transport_connected")
    tc_ok = tc is True or tc is None
    if att == 0:
        return "no_route_recovery_attempts_on_input_check_eligibility"
    if ok == 0:
        return "attempted_but_no_success_review_rejection_histogram"
    if not (geo and conn and ms == 0 and ot == 0 and tc_ok):
        return "success_but_invariant_failed_revisit_commit_gate"
    return "success_and_invariants_ok_consider_shrunk_fixture"


def _stub_route_trace_spotcheck(b_on: dict[str, Any]) -> dict[str, Any]:
    traces = b_on.get("pass12_preserved_recovery_traces") or []
    samples: list[dict[str, Any]] = []
    if not isinstance(traces, list):
        return {"stub_route_trace_samples": [], "note": "no_traces_list"}
    for tr in traces:
        if not isinstance(tr, dict):
            continue
        rm = tr.get("recovery_mode")
        modes = rm if isinstance(rm, list) else []
        if "stub_route_to_trunk" in modes:
            samples.append(
                {
                    "miner_cell": tr.get("miner_cell"),
                    "path_cells": tr.get("path_cells"),
                    "new_transport_cell_count": tr.get("new_transport_cell_count"),
                    "selected_stub_cell": tr.get("selected_stub_cell"),
                }
            )
        if len(samples) >= 16:
            break
    return {
        "stub_route_trace_samples": samples,
        "note": "Compare path_cells roles to mining_map offline if needed.",
    }


def _write_stub_route_ab(
    payload: dict[str, Any], diff: dict[str, Any], summary_diff: dict[str, Any]
) -> int:
    out_dir = ROOT / "var"
    out_dir.mkdir(parents=True, exist_ok=True)
    _OUT_PATH_STUB_ROUTE_AB.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"written": str(_OUT_PATH_STUB_ROUTE_AB), "diff": diff, "summary": summary_diff},
            indent=2,
        )
    )
    return 0


def _main_stub_route_recovery_ab(
    decoded: dict[str, Any], source: dict[str, Any], *, full: bool = False
) -> int:
    decoded_off = copy.deepcopy(decoded)
    decoded_on = copy.deepcopy(decoded)
    b_off = _stub_route_ab_timeline_row(decoded_off, route_flag=False)
    b_on = _stub_route_ab_timeline_row(decoded_on, route_flag=True)
    diff = _diff_stub_route_ab(b_off, b_on)
    drop_off = int(b_off.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    drop_on = int(b_on.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    rr_ok_off = int(b_off.get("pass12_preserved_missing_stub_route_recovery_success_count") or 0)
    rr_ok_on = int(b_on.get("pass12_preserved_missing_stub_route_recovery_success_count") or 0)
    ext_off = b_off.get("extractor_count")
    ext_on = b_on.get("extractor_count")
    summary_diff = {
        "stub_route_drop_delta": drop_on - drop_off,
        "stub_route_recovery_success_delta": rr_ok_on - rr_ok_off,
        "extractor_count_off": ext_off,
        "extractor_count_on": ext_on,
        "decision_hint": _stub_route_ab_decision_hint(b_off, b_on),
    }
    spot = _stub_route_trace_spotcheck(b_on)
    payload = {
        "ab_mode": "stub_route_recovery",
        "settings_note": (
            "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True for both runs; "
            "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY toggled False/True."
        ),
        "input_source": source,
        "baseline_route_recovery_off": _trim_timeline_heavy(b_off, full=full),
        "route_recovery_on": _trim_timeline_heavy(b_on, full=full),
        "diff_route_off_vs_on": diff,
        "summary_diff": summary_diff,
        "spotcheck": spot,
    }
    return _write_stub_route_ab(payload, diff, summary_diff)


def _parse_cap_values(raw: str) -> tuple[int, ...]:
    values: list[int] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        try:
            cap = int(item)
        except ValueError as e:
            raise ValueError(f"invalid cap value: {item!r}") from e
        if cap < 1:
            raise ValueError(f"cap must be positive: {cap}")
        if cap not in values:
            values.append(cap)
    if not values:
        raise ValueError("at least one cap value is required")
    return tuple(values)


def _run_stub_route_cap_row(decoded: dict[str, Any], *, cap: int) -> dict[str, Any]:
    """같은 입력을 특정 nearest-hop cap으로 실행하고 핵심 품질 지표를 모은다."""

    started = time.perf_counter()
    with (
        patch.object(
            pass12_merged_layout_seed,
            "MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS",
            cap,
        ),
        patch.object(
            pass12_preserve_stub_route_recovery,
            "MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS",
            cap,
        ),
        override_settings(
            SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True,
            SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True,
        ),
    ):
        row = _stub_route_ab_timeline_row(copy.deepcopy(decoded), route_flag=True)
    row["cap"] = cap
    row["runtime_s"] = round(time.perf_counter() - started, 6)
    return row


def _cap_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cap": row.get("cap"),
        "runtime_s": row.get("runtime_s"),
        "original_extractor_count": row.get("original_extractor_count"),
        "final_extractor_count": row.get("final_extractor_count") or row.get("extractor_count"),
        "preserve_missing_stub_drop_count": row.get(
            "pass12_preserved_missing_stub_drop_extractor_count"
        ),
        "stub_route_recovery_attempted_count": row.get(
            "pass12_preserved_missing_stub_route_recovery_attempted_count"
        ),
        "stub_route_recovery_success_count": row.get(
            "pass12_preserved_missing_stub_route_recovery_success_count"
        ),
        "rejected_by_nearest_hops_count": row.get(
            "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count"
        ),
        "rejected_by_no_same_kind_route_count": row.get(
            "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count"
        ),
        "rejected_by_visit_cap_count": row.get(
            "pass12_preserved_missing_stub_route_recovery_rejected_by_visit_cap_count"
        ),
        "transport_cell_count": row.get("transport_cell_count"),
        "optimization_final_internal_transport_count": row.get(
            "optimization_final_internal_transport_count"
        ),
        "internal_transport_delta_vs_baseline": row.get("internal_transport_delta_vs_baseline"),
        "geometry_valid": row.get("geometry_valid"),
        "connectivity_valid": row.get("connectivity_valid"),
        "missing_stub_count": row.get("missing_stub_count"),
        "orphan_transport_count": row.get("orphan_transport_count"),
        "transport_connected": row.get("transport_connected"),
        "solver_quality_tier": row.get("solver_quality_tier"),
    }


def _main_stub_route_cap_ab(
    decoded: dict[str, Any],
    source: dict[str, Any],
    *,
    cap_values: tuple[int, ...],
    full: bool = False,
) -> int:
    rows = [_run_stub_route_cap_row(decoded, cap=cap) for cap in cap_values]
    summaries = [_cap_row_summary(row) for row in rows]
    baseline = summaries[0] if summaries else {}
    comparisons: list[dict[str, Any]] = []
    base_final = baseline.get("final_extractor_count")
    base_drop = baseline.get("preserve_missing_stub_drop_count")
    base_transport = baseline.get("transport_cell_count")
    base_delta = baseline.get("internal_transport_delta_vs_baseline")
    for row in summaries:
        comparisons.append(
            {
                "cap": row.get("cap"),
                "final_extractor_delta_vs_first_cap": (
                    None
                    if not isinstance(row.get("final_extractor_count"), int)
                    or not isinstance(base_final, int)
                    else row["final_extractor_count"] - base_final
                ),
                "preserve_drop_delta_vs_first_cap": (
                    None
                    if not isinstance(row.get("preserve_missing_stub_drop_count"), int)
                    or not isinstance(base_drop, int)
                    else row["preserve_missing_stub_drop_count"] - base_drop
                ),
                "transport_cell_delta_vs_first_cap": (
                    None
                    if not isinstance(row.get("transport_cell_count"), int)
                    or not isinstance(base_transport, int)
                    else row["transport_cell_count"] - base_transport
                ),
                "internal_transport_delta_shift_vs_first_cap": (
                    None
                    if not isinstance(row.get("internal_transport_delta_vs_baseline"), int)
                    or not isinstance(base_delta, int)
                    else row["internal_transport_delta_vs_baseline"] - base_delta
                ),
            }
        )
    payload = {
        "ab_mode": "stub_route_cap_ab",
        "settings_note": (
            "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True and "
            "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True for every variant."
        ),
        "input_source": source,
        "cap_values": list(cap_values),
        "summary_rows": summaries,
        "comparisons_vs_first_cap": comparisons,
        "variant_rows": [_trim_timeline_heavy(row, full=full) for row in rows],
    }
    out_dir = ROOT / "var"
    out_dir.mkdir(parents=True, exist_ok=True)
    _OUT_PATH_STUB_ROUTE_CAP_AB.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "written": str(_OUT_PATH_STUB_ROUTE_CAP_AB),
                "summary_rows": summaries,
                "comparisons_vs_first_cap": comparisons,
            },
            indent=2,
        )
    )
    return 0


def _probe_replay_input(path: Path) -> dict[str, Any]:
    """Return whether ``path`` can supply a decoded blueprint (BP.Entries) without running solve."""

    p = path.resolve()
    try:
        load_decoded_from_ndjson_or_json(p)
        return {"path": str(p), "replayable": True, "reason": "found_top_level_BP"}
    except (OSError, ValueError) as e:
        return {"path": str(p), "replayable": False, "reason": str(e)}


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
    drop_on = int(recovery_on.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    drop_off = int(baseline.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    rec_on = int(recovery_on.get("pass12_preserved_recovery_success_count") or 0)
    rec_off = int(baseline.get("pass12_preserved_recovery_success_count") or 0)
    diff = {
        "drop_delta": drop_on - drop_off,
        "recovery_success_delta": rec_on - rec_off,
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
    src_group = parser.add_mutually_exclusive_group()
    src_group.add_argument(
        "--copy-code-file",
        type=Path,
        metavar="PATH",
        help="Text file with SHAPEZ2-4-... copy string (whitespace allowed).",
    )
    src_group.add_argument(
        "--ndjson",
        type=Path,
        metavar="PATH",
        help="Single JSON with BP, or NDJSON containing a line with BP (e.g. *_decoded.json).",
    )
    src_group.add_argument(
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
        help=(
            "Decoded blueprint JSON (single object with BP.Entries), alone or with "
            "--solver-trace when the trace has no embedded BP line."
        ),
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include full pass12 drop_details and recovery_traces in JSON (default: truncated).",
    )
    parser.add_argument(
        "--stub-route-recovery-ab",
        action="store_true",
        help=(
            "Compare SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY False vs True "
            "(SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True). Writes "
            "var/pass12_stub_route_recovery_ab_experiment.json. Use with --ndjson / "
            "--copy-code-file / --solver-trace, or alone for striped BP smoke."
        ),
    )
    parser.add_argument(
        "--stub-route-cap-ab",
        action="store_true",
        help=(
            "Run stub-route recovery with nearest-hop cap variants. Writes "
            "var/pass12_stub_route_recovery_cap_ab_experiment.json."
        ),
    )
    parser.add_argument(
        "--stub-route-cap-values",
        type=str,
        default="6,8,10",
        metavar="CSV",
        help="Comma-separated nearest-hop cap values for --stub-route-cap-ab (default: 6,8,10).",
    )
    parser.add_argument(
        "--probe-replay-input",
        type=Path,
        default=None,
        metavar="PATH",
        help="Exit after checking whether PATH contains a replayable top-level BP (no solve).",
    )
    args = parser.parse_args()

    if args.probe_replay_input is not None:
        probe = _probe_replay_input(args.probe_replay_input.resolve())
        print(json.dumps(probe, indent=2))
        return 0 if probe.get("replayable") else 3

    has_input = bool(args.solver_trace or args.copy_code_file or args.ndjson or args.bp_json)
    cap_values = _parse_cap_values(args.stub_route_cap_values)

    try:
        if args.stub_route_cap_ab and not has_input:
            return _main_stub_route_cap_ab(
                copy.deepcopy(_STRIPED_BP),
                {"kind": "synthetic_striped_bp_stub_route_cap_ab"},
                cap_values=cap_values,
                full=args.full,
            )
        if args.stub_route_recovery_ab and not has_input:
            return _main_stub_route_recovery_ab(
                copy.deepcopy(_STRIPED_BP),
                {"kind": "synthetic_striped_bp_stub_route_ab"},
                full=args.full,
            )
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
            if args.stub_route_cap_ab:
                return _main_stub_route_cap_ab(
                    decoded, src_meta, cap_values=cap_values, full=args.full
                )
            if args.stub_route_recovery_ab:
                return _main_stub_route_recovery_ab(decoded, src_meta, full=args.full)
            return _main_decoded(decoded, src_meta, full=args.full)
        if args.copy_code_file:
            decoded = load_decoded_from_copy_code_file(args.copy_code_file.resolve())
            input_src: dict[str, Any] = {
                "kind": "copy_code_file",
                "path": str(args.copy_code_file.resolve()),
            }
            if args.stub_route_cap_ab:
                return _main_stub_route_cap_ab(
                    decoded, input_src, cap_values=cap_values, full=args.full
                )
            if args.stub_route_recovery_ab:
                return _main_stub_route_recovery_ab(decoded, input_src, full=args.full)
            return _main_decoded(decoded, input_src, full=args.full)
        if args.ndjson:
            decoded = load_decoded_from_ndjson_or_json(args.ndjson.resolve())
            input_src = {
                "kind": "ndjson_or_json",
                "path": str(args.ndjson.resolve()),
            }
            if args.stub_route_cap_ab:
                return _main_stub_route_cap_ab(
                    decoded, input_src, cap_values=cap_values, full=args.full
                )
            if args.stub_route_recovery_ab:
                return _main_stub_route_recovery_ab(decoded, input_src, full=args.full)
            return _main_decoded(decoded, input_src, full=args.full)
        if args.bp_json:
            decoded = load_decoded_from_ndjson_or_json(args.bp_json.resolve())
            input_src = {"kind": "bp_json", "path": str(args.bp_json.resolve())}
            if args.stub_route_cap_ab:
                return _main_stub_route_cap_ab(
                    decoded, input_src, cap_values=cap_values, full=args.full
                )
            if args.stub_route_recovery_ab:
                return _main_stub_route_recovery_ab(decoded, input_src, full=args.full)
            return _main_decoded(decoded, input_src, full=args.full)
    except (OSError, ValueError, ShapezCopyDecodeError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return _main_default(full=args.full)


if __name__ == "__main__":
    raise SystemExit(main())
