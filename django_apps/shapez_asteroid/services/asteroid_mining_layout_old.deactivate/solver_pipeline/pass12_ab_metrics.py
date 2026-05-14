"""Pass12 preserve recovery A/B: OFF drop vs ON recovery join (no Django runtime deps)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Any


def _int_counts(raw: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        try:
            out[k] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def _miner_cell_tuple(cell: Any) -> tuple[int, int] | None:
    if not isinstance(cell, list) or len(cell) != 2:
        return None
    try:
        return (int(cell[0]), int(cell[1]))
    except (TypeError, ValueError):
        return None


def recoverability_ab_outcome_bundle(
    b_off: Mapping[str, Any],
    b_on: Mapping[str, Any],
) -> dict[str, Any]:
    """Join OFF drop_details (recoverability_class) to ON recovery_traces (miner_cell).

    ``b_off`` / ``b_on`` need full drop detail and trace lists for correct joins.
    """

    dropped_off = _int_counts(b_off.get("pass12_recoverability_class_counts"))
    miner_to_class: dict[tuple[int, int], str] = {}
    drops = b_off.get("pass12_preserved_missing_stub_drop_details") or []
    if isinstance(drops, list):
        for row in drops:
            if not isinstance(row, dict):
                continue
            kt = _miner_cell_tuple(row.get("miner_cell"))
            cls = row.get("recoverability_class")
            if kt is not None and isinstance(cls, str) and cls:
                miner_to_class[kt] = cls

    recovered_by_class: dict[str, int] = defaultdict(int)
    orphan_on_recovery_trace_count = 0
    traces = b_on.get("pass12_preserved_recovery_traces") or []
    if isinstance(traces, list):
        for tr in traces:
            if not isinstance(tr, dict):
                continue
            kt = _miner_cell_tuple(tr.get("miner_cell"))
            if kt is None:
                orphan_on_recovery_trace_count += 1
                continue
            cls = miner_to_class.get(kt)
            if cls is None:
                orphan_on_recovery_trace_count += 1
                continue
            recovered_by_class[cls] += 1

    recovered_sorted = dict(sorted(recovered_by_class.items(), key=lambda kv: kv[0]))
    rate: dict[str, float] = {}
    for cls, dcnt in dropped_off.items():
        if dcnt <= 0:
            continue
        rcnt = recovered_sorted.get(cls, 0)
        rate[cls] = round(float(rcnt) / float(dcnt), 6)

    outcome_by_class: dict[str, dict[str, Any]] = {}
    for cls, dcnt in sorted(dropped_off.items(), key=lambda kv: kv[0]):
        if dcnt <= 0:
            continue
        rcnt = recovered_sorted.get(cls, 0)
        outcome_by_class[cls] = {
            "dropped": dcnt,
            "recovered": rcnt,
            "recovery_rate": round(float(rcnt) / float(dcnt), 6),
        }

    drop_row = int(b_off.get("pass12_preserved_missing_stub_drop_extractor_count") or 0)
    hist_total = sum(dropped_off.values())
    denom = drop_row if drop_row > 0 else hist_total
    unrec = int(dropped_off.get("UNRECOVERABLE", 0) or 0)
    recovery_candidate_fraction: float | None = None
    recovery_candidate_count: int | None = None
    if denom > 0:
        recovery_candidate_count = max(0, denom - min(unrec, denom))
        recovery_candidate_fraction = round(float(recovery_candidate_count) / float(denom), 6)

    return {
        "recoverability_outcome_counts": {
            "dropped_off": dict(sorted(dropped_off.items(), key=lambda kv: kv[0])),
            "recovered_by_class": recovered_sorted,
            "orphan_on_recovery_trace_count": orphan_on_recovery_trace_count,
        },
        "recoverability_outcome_by_class": outcome_by_class,
        "recovery_rate_by_class": rate,
        "recovery_candidate_fraction": recovery_candidate_fraction,
        "recovery_candidate_count": recovery_candidate_count,
        "recovery_candidate_denominator": denom if denom > 0 else None,
    }
