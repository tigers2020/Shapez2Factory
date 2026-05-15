"""
Pass2 bundle packing: choose a non-overlapping subset of ``Pass2BundleCandidate``.

CP-SAT (OR-Tools) when available; otherwise deterministic greedy set packing.
Does not import routing, NDJSON/replay readers, or v1 layout.
"""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)

from .bundle_candidate import Pass2BundleCandidate

try:
    from ortools.sat.python import cp_model as ortools_cp_model
except ImportError:
    ortools_cp_model = None


def pass2_candidate_occupied_cells(candidate: Pass2BundleCandidate) -> frozenset[BlueprintCell]:
    """Geometry aligned with ``PlacementBundle`` / former ``_pass2_try_commit_bundle``."""

    cells: set[BlueprintCell] = {
        candidate.extractor_cell,
        candidate.output_stub_cell,
    }
    for ec, _pc, _orient in candidate.extension_cells:
        cells.add(ec)
    return frozenset(cells)


def _objective_weight(candidate: Pass2BundleCandidate) -> int:
    return int(round(float(candidate.score) * 1000.0))


def _cell_to_candidate_indices(
    candidates: tuple[Pass2BundleCandidate, ...],
) -> dict[BlueprintCell, tuple[int, ...]]:
    out: dict[BlueprintCell, list[int]] = {}
    for i, c in enumerate(candidates):
        for cell in pass2_candidate_occupied_cells(c):
            out.setdefault(cell, []).append(i)
    return {k: tuple(v) for k, v in out.items()}


def select_pass2_bundles_greedy_fallback(
    candidates: tuple[Pass2BundleCandidate, ...],
) -> tuple[Pass2BundleCandidate, ...]:
    """Deterministic greedy set packing: sort by weight desc, then stable tie-breakers."""



    def sort_key(
        item: tuple[int, Pass2BundleCandidate],
    ) -> tuple[int, int, tuple[int, int], tuple[int, int], str, int]:
        i, c = item
        w = _objective_weight(c)
        return (-w, c.scan_index, c.extractor_cell, c.output_direction, c.candidate_id, i)

    sorted_items = sorted(enumerate(candidates), key=sort_key)
    taken: set[BlueprintCell] = set()
    picked: list[Pass2BundleCandidate] = []
    for _i, c in sorted_items:
        occ = pass2_candidate_occupied_cells(c)
        if occ & taken:
            continue
        taken |= occ
        picked.append(c)
    picked.sort(key=lambda c: (c.scan_index, c.extractor_cell, c.output_direction, c.candidate_id))
    return tuple(picked)


def _cp_sat_pack(
    candidates: tuple[Pass2BundleCandidate, ...],
    *,
    time_limit_ms: int,
) -> tuple[tuple[Pass2BundleCandidate, ...], int, str, int] | None:
    """Return (selected_sorted, objective, cp_status_name, conflict_count) or None."""

    if ortools_cp_model is None or not candidates:
        return None

    cp_model = ortools_cp_model
    model = cp_model.CpModel()
    n = len(candidates)
    weights = [_objective_weight(candidates[i]) for i in range(n)]
    cell_map = _cell_to_candidate_indices(candidates)
    x = [model.NewBoolVar(f"x_{i}") for i in range(n)]
    conflict_count = 0
    for _cell, indices in cell_map.items():
        if len(indices) < 2:
            continue
        conflict_count += 1
        model.Add(sum(x[i] for i in indices) <= 1)

    model.Maximize(sum(weights[i] * x[i] for i in range(n)))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(time_limit_ms, 1) / 1000.0
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None

    status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
    selected_list = [candidates[i] for i in range(n) if solver.Value(x[i]) == 1]
    selected_list.sort(
        key=lambda c: (c.scan_index, c.extractor_cell, c.output_direction, c.candidate_id)
    )
    objective = int(round(solver.ObjectiveValue()))
    return (tuple(selected_list), objective, status_name, conflict_count)


def _truncate_candidates(
    candidates: tuple[Pass2BundleCandidate, ...],
    max_candidates: int,
) -> tuple[tuple[Pass2BundleCandidate, ...], bool]:
    if len(candidates) <= max_candidates:
        return candidates, False
    sorted_c = sorted(
        candidates,
        key=lambda c: (c.scan_index, c.extractor_cell, c.output_direction, c.candidate_id),
    )
    return tuple(sorted_c[:max_candidates]), True


@dataclass(frozen=True, slots=True)
class Pass2PackingInput:
    """Inputs for Pass2 set packing (subset of feasible candidates)."""

    candidates: tuple[Pass2BundleCandidate, ...]
    blocked_cells: frozenset[BlueprintCell]
    max_candidates: int = 5000
    time_limit_ms: int = 250
    use_cp_sat: bool = True
    fallback_to_greedy: bool = True


@dataclass(frozen=True, slots=True)
class Pass2PackingResult:
    """Optimizer output + metadata for beam / tests."""

    selected: tuple[Pass2BundleCandidate, ...]
    rejected: tuple[dict[str, object], ...]
    optimizer_status: str
    objective_value: int
    candidate_count: int
    selected_count: int
    conflict_constraint_count: int
    fallback_used: bool
    cp_sat_status: str | None
    optimizer_name: str


def optimize_pass2_bundle_packing(inp: Pass2PackingInput) -> Pass2PackingResult:
    """Maximize sum of integer-scaled scores under pairwise cell disjointness."""

    feasible = tuple(c for c in inp.candidates if c.reject_reason is None)
    pool, truncated = _truncate_candidates(feasible, inp.max_candidates)
    meta_rejects: list[dict[str, object]] = []
    if truncated:
        meta_rejects.append(
            {
                "placement_pass": "pass2",
                "event_type": "pass2_optimizer_truncation",
                "truncated": True,
                "max_candidates": inp.max_candidates,
                "feasible_before": len(feasible),
                "feasible_after": len(pool),
            }
        )

    if not pool:
        return Pass2PackingResult(
            selected=(),
            rejected=tuple(meta_rejects),
            optimizer_status="EMPTY",
            objective_value=0,
            candidate_count=0,
            selected_count=0,
            conflict_constraint_count=0,
            fallback_used=False,
            cp_sat_status=None,
            optimizer_name="none",
        )

    cell_map = _cell_to_candidate_indices(pool)
    conflict_constraint_count = sum(1 for idx in cell_map.values() if len(idx) >= 2)

    selected: tuple[Pass2BundleCandidate, ...] = ()
    objective_value = 0
    optimizer_status = "GREEDY_FALLBACK"
    optimizer_name = "greedy_fallback"
    cp_sat_status: str | None = None
    cp_failed = False

    if inp.use_cp_sat and ortools_cp_model is not None:
        cp_out = _cp_sat_pack(pool, time_limit_ms=inp.time_limit_ms)
        if cp_out is not None:
            selected, objective_value, cp_sat_status, conflict_constraint_count = cp_out
            optimizer_name = "cp_sat"
            optimizer_status = cp_sat_status
        else:
            cp_failed = True

    if not selected:
        selected = select_pass2_bundles_greedy_fallback(pool)
        objective_value = sum(_objective_weight(c) for c in selected)
        optimizer_name = "greedy_fallback"
        optimizer_status = "GREEDY_FALLBACK"
        cp_sat_status = None

    fallback_used = bool(
        optimizer_name == "greedy_fallback"
        and inp.use_cp_sat
        and (ortools_cp_model is None or cp_failed)
    )

    return Pass2PackingResult(
        selected=selected,
        rejected=tuple(meta_rejects),
        optimizer_status=optimizer_status,
        objective_value=objective_value,
        candidate_count=len(pool),
        selected_count=len(selected),
        conflict_constraint_count=conflict_constraint_count,
        fallback_used=fallback_used,
        cp_sat_status=cp_sat_status,
        optimizer_name=optimizer_name,
    )


__all__ = [
    "Pass2PackingInput",
    "Pass2PackingResult",
    "optimize_pass2_bundle_packing",
    "pass2_candidate_occupied_cells",
    "select_pass2_bundles_greedy_fallback",
]
