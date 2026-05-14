"""P3-E3 guarded commit DTOs and trace serializers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class P3E3GuardedPrecheckCandidate:
    """Summaries-only candidate for a future guarded atomic commit (P3-E3b).

    Per-stub lex path coordinates and map deltas are deferred until atomic candidate-map build.
    """

    outlet_stub_cells: tuple[Coord, ...]
    lex_internal_transport_count: int
    lex_path_length_sum: int
    greedy_internal_transport_count: int
    greedy_path_length_sum: int
    lex_all_found: bool
    shadow_would_commit_preview: bool
    shadow_rejected_reason: str | None
    lex_success_count: int
    greedy_success_count: int


def p3e3_guarded_precheck_candidate_as_trace_dict(
    candidate: P3E3GuardedPrecheckCandidate,
) -> dict[str, Any]:
    """JSON-friendly dict (stub coords as ``[x, y]`` lists)."""

    d = asdict(candidate)
    d["outlet_stub_cells"] = [[int(x), int(y)] for x, y in candidate.outlet_stub_cells]
    return d


@dataclass(frozen=True)
class P3E3GuardedCommitCandidate:
    """Atomic swap preview for P3-E3b (precheck + optional live swap + post validation)."""

    attempted: bool
    candidate_transport_cells: frozenset[Coord]
    removed_transport_cells: frozenset[Coord]
    added_transport_cells: frozenset[Coord]
    preserved_stub_cells: frozenset[Coord]
    touched_hard_protected_cells: frozenset[Coord]
    touched_soft_protected_cells: frozenset[Coord]
    replacement_route_cells: frozenset[Coord]
    baseline_route_length: int | None
    candidate_route_length: int | None
    route_length_ratio: float | None
    precheck_passed: bool
    rejected_reason: str | None
    hard_protected_corridors: frozenset[Coord]


def p3e3_guarded_commit_candidate_as_trace_dict(
    candidate: P3E3GuardedCommitCandidate,
) -> dict[str, Any]:
    """JSON-friendly frozensets as sorted ``[x, y]`` lists."""

    def fs_cells(fs: frozenset[Coord]) -> list[list[int]]:
        """trace payload용 frozenset Coord를 정렬된 list 좌표로 변환한다 (§11 P3-E3)."""
        return [[int(x), int(y)] for x, y in sorted(fs, key=lambda p: (p[1], p[0]))]

    return {
        "attempted": candidate.attempted,
        "candidate_transport_cells": fs_cells(candidate.candidate_transport_cells),
        "removed_transport_cells": fs_cells(candidate.removed_transport_cells),
        "added_transport_cells": fs_cells(candidate.added_transport_cells),
        "preserved_stub_cells": fs_cells(candidate.preserved_stub_cells),
        "touched_hard_protected_cells": fs_cells(candidate.touched_hard_protected_cells),
        "touched_soft_protected_cells": fs_cells(candidate.touched_soft_protected_cells),
        "replacement_route_cells": fs_cells(candidate.replacement_route_cells),
        "baseline_route_length": candidate.baseline_route_length,
        "candidate_route_length": candidate.candidate_route_length,
        "route_length_ratio": candidate.route_length_ratio,
        "precheck_passed": candidate.precheck_passed,
        "rejected_reason": candidate.rejected_reason,
    }
