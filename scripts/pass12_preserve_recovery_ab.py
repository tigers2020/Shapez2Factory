#!/usr/bin/env python3
"""Pass12 preserve stub recovery OFF vs ON (same merged-seed / same decoded BP input).

Default: synthetic merged-seed fixture + greenfield striped ``build_solver_timeline`` smoke.

With ``--copy-code-file`` or ``--ndjson``: runs full ``build_solver_timeline(decoded)`` twice
(recovery OFF vs ON) and writes comparison to ``var/pass12_recovery_ab_experiment.json``.

``--ndjson`` accepts (1) a single JSON object with top-level ``BP``, or (2) NDJSON where at
least one line parses to an object containing ``BP`` (e.g. a pasted decoded line). Standard
solver debug NDJSON without a ``BP`` line cannot be replayed; use ``*_decoded.json`` or
``--copy-code-file`` instead.
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (  # noqa: E402
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
        "pass12_preserved_missing_stub_drop_extractor_count": s.get(
            "pass12_preserved_missing_stub_drop_extractor_count"
        ),
        "pass12_preserve_drop_reason_counts": dict(
            s.get("pass12_preserve_drop_reason_counts") or {}
        ),
        "pass12_preserved_recovery_success_count": s.get(
            "pass12_preserved_recovery_success_count"
        ),
        "pass12_preserved_recovery_traces": list(traces)[:_TRACE_LIST_LIMIT],
        "pass12_preserved_missing_stub_drop_details": list(drops)[:_DROP_DETAILS_LIMIT],
    }


def _default_on_gates(b_off: dict[str, Any], b_on: dict[str, Any]) -> dict[str, Any]:
    """Heuristic checklist: ON vs OFF (relative improvement + absolute safety on ON)."""

    drop_off = int(b_off.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    drop_on = int(b_on.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    score_off = b_off.get("preserve_quality_score")
    score_on = b_on.get("preserve_quality_score")
    try:
        score_delta = float(score_on) - float(score_off) if score_off is not None else None
    except (TypeError, ValueError):
        score_delta = None

    def _num(x: Any) -> int | None:
        if x is None:
            return None
        try:
            return int(x)
        except (TypeError, ValueError):
            return None

    ms_on = _num(b_on.get("missing_stub_count"))
    rf_on = _num(b_on.get("step4_routing_failure_count"))

    return {
        "drop_decreased": drop_on < drop_off,
        "preserve_quality_score_increased": bool(score_delta is not None and score_delta > 0),
        "preserve_quality_score_delta": score_delta,
        "geometry_valid_unchanged_and_true": (
            b_off.get("geometry_valid") is True and b_on.get("geometry_valid") is True
        ),
        "connectivity_valid_unchanged_and_true": (
            b_off.get("connectivity_valid") is True and b_on.get("connectivity_valid") is True
        ),
        "step4_routing_failure_stays_zero": rf_on == 0,
        "missing_stub_stays_zero": ms_on == 0,
        "step4_committed_stays_true": b_on.get("step4_committed") is True,
        "all_default_on_candidate_gates": bool(
            drop_on < drop_off
            and (score_delta is not None and score_delta > 0)
            and b_off.get("geometry_valid") is True
            and b_on.get("geometry_valid") is True
            and b_off.get("connectivity_valid") is True
            and b_on.get("connectivity_valid") is True
            and rf_on == 0
            and ms_on == 0
            and b_on.get("step4_committed") is True
        ),
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


def _main_default() -> int:
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

    payload = {
        "input_source": {"kind": "synthetic_default"},
        "fixture": "relaxed_stub_recovery_synthetic",
        "baseline_recovery_off": baseline,
        "recovery_on": recovery_on,
        "diff": diff,
        "trace_spotcheck": spotcheck_note,
        "full_pipeline_smoke_striped_bp": {
            "note": (
                "Greenfield blueprint; pass12 recovery flag should not change geometry/step4 "
                "regression gates vs itself."
            ),
            "baseline_recovery_off": tl_off,
            "recovery_on": tl_on,
            "field_changed_recovery_on_vs_off": {k: v for k, v in tl_diff.items() if v},
        },
    }
    return _write_and_print(payload, diff)


def _main_decoded(decoded: dict[str, Any], source: dict[str, Any]) -> int:
    b_off = _timeline_guard_fields(decoded, False)
    b_on = _timeline_guard_fields(decoded, True)
    diff = _diff_timeline(b_off, b_on)
    gates = _default_on_gates(b_off, b_on)
    payload = {
        "input_source": source,
        "baseline_recovery_off": b_off,
        "recovery_on": b_on,
        "diff_timeline_off_vs_on": diff,
        "default_on_candidate_gates": gates,
    }
    summary_diff = {
        "drop_delta": int(b_on["pass12_preserved_missing_stub_drop_extractor_count"] or 0)
        - int(b_off["pass12_preserved_missing_stub_drop_extractor_count"] or 0),
        "recovery_success_delta": int(b_on["pass12_preserved_recovery_success_count"] or 0)
        - int(b_off["pass12_preserved_recovery_success_count"] or 0),
        "preserve_quality_score_baseline": b_off.get("preserve_quality_score"),
        "preserve_quality_score_recovery_on": b_on.get("preserve_quality_score"),
        "default_on_all_gates": gates.get("all_default_on_candidate_gates"),
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
    args = parser.parse_args()

    try:
        if args.copy_code_file:
            decoded = load_decoded_from_copy_code_file(args.copy_code_file.resolve())
            return _main_decoded(
                decoded,
                {"kind": "copy_code_file", "path": str(args.copy_code_file.resolve())},
            )
        if args.ndjson:
            decoded = load_decoded_from_ndjson_or_json(args.ndjson.resolve())
            return _main_decoded(
                decoded,
                {"kind": "ndjson_or_json", "path": str(args.ndjson.resolve())},
            )
    except (OSError, ValueError, ShapezCopyDecodeError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return _main_default()


if __name__ == "__main__":
    raise SystemExit(main())
