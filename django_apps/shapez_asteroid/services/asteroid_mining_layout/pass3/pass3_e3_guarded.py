"""P3-E3 guarded atomic commit façade (submodules: dto, atomic_map, lex, trace, gates)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_VALIDATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

from .pass3_e3_guarded_atomic_map import (
    _p3e3_build_atomic_candidate_map,
    _p3e3_route_length_ratio_allowed,
)
from .pass3_e3_guarded_dto import P3E3GuardedCommitCandidate
from .pass3_e3_guarded_gates import (
    _p3e3_atomic_phase_deferred_by_shadow_alignment,
    _p3e3_rollback_guarded_transport_cells,
    _p3e3_should_commit_guarded_candidate,
    _p3e3_transport_dict_from_candidate_cells,
)
from .pass3_e3_guarded_lex_collect import _p3e3_collect_guarded_lex_replacement
from .pass3_e3_guarded_trace import (
    _p3e3_atomic_trace_from_dto,
    p3e2_pass3_summary_placeholder,
    p3e3_emit_guarded_trace,
    p3e3_pass3_summary_placeholder,
)
from .pass3_e3_guarded_transport_trial import (
    _p3e3_validate_candidate_transport_map,
    _p3e3_validate_post_commit_transport_map,
)

__all__ = (
    "P3E3GuardedCommitCandidate",
    "_p3e3_atomic_phase_deferred_by_shadow_alignment",
    "_p3e3_atomic_trace_from_dto",
    "_p3e3_build_atomic_candidate_map",
    "_p3e3_collect_guarded_lex_replacement",
    "_p3e3_rollback_guarded_transport_cells",
    "_p3e3_route_length_ratio_allowed",
    "_p3e3_run_atomic_candidate_phase",
    "_p3e3_should_commit_guarded_candidate",
    "_p3e3_transport_dict_from_candidate_cells",
    "_p3e3_validate_post_commit_transport_map",
    "p3e2_pass3_summary_placeholder",
    "p3e3_emit_guarded_trace",
    "p3e3_pass3_summary_placeholder",
)


def _p3e3_run_atomic_candidate_phase(
    *,
    mining_map: list[dict[str, Any]],
    cells: dict[Coord, dict[str, Any]],
    transport_cells: dict[Coord, str],
    outlets_order: list[Coord],
    anchor: Coord,
    want_role: str,
    transport_kind: str,
    asteroid_cells: set[Coord],
    mineable_f: frozenset[Coord],
    asteroid_f: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> tuple[P3E3GuardedCommitCandidate, dict[str, Any]]:
    """P3-E3b-1: build + validate candidate; never mutates caller maps."""

    fixed_stubs = frozenset(outlets_order)
    (
        cells_to_remove,
        replacement_route_cells,
        baseline_len,
        candidate_len,
        hard_union,
        soft_union,
        collect_err,
    ) = _p3e3_collect_guarded_lex_replacement(
        mining_map=mining_map,
        cells=cells,
        transport_cells=transport_cells,
        outlets_order=outlets_order,
        anchor=anchor,
        transport_kind=transport_kind,
        asteroid_cells=asteroid_cells,
        mineable_f=mineable_f,
        asteroid_f=asteroid_f,
        is_external=is_external,
    )

    if collect_err is not None:
        dto = P3E3GuardedCommitCandidate(
            attempted=True,
            candidate_transport_cells=frozenset(),
            removed_transport_cells=frozenset(),
            added_transport_cells=frozenset(),
            preserved_stub_cells=fixed_stubs,
            touched_hard_protected_cells=frozenset(),
            touched_soft_protected_cells=frozenset(),
            replacement_route_cells=frozenset(),
            baseline_route_length=None,
            candidate_route_length=None,
            route_length_ratio=None,
            precheck_passed=False,
            rejected_reason=collect_err,
            hard_protected_corridors=frozenset(),
        )
        trace = _p3e3_atomic_trace_from_dto(
            dto,
            atomic_candidate_built=False,
            validation_passed=False,
            would_accept=False,
            atomic_rejected=collect_err,
        )
        return dto, trace

    dto = _p3e3_build_atomic_candidate_map(
        current_transport_cells=frozenset(transport_cells.keys()),
        cells_to_remove=cells_to_remove,
        replacement_route_cells=replacement_route_cells,
        fixed_output_stubs=fixed_stubs,
        hard_protected_corridors=hard_union,
        soft_protected_corridors=soft_union,
        baseline_route_length=baseline_len,
        candidate_route_length=candidate_len,
        attempted=True,
    )

    atomic_rejected: str | None = dto.rejected_reason
    ratio_ok = _p3e3_route_length_ratio_allowed(
        baseline_route_length=baseline_len,
        candidate_route_length=candidate_len,
    )
    if dto.precheck_passed and not ratio_ok:
        dto = replace(
            dto,
            rejected_reason=P3E3_REJECT_ROUTE_LENGTH_RATIO,
        )
        atomic_rejected = P3E3_REJECT_ROUTE_LENGTH_RATIO

    validation_passed = False
    val_reason: str | None = None
    if dto.precheck_passed and ratio_ok:
        validation_passed, val_reason = _p3e3_validate_candidate_transport_map(
            cells_base=cells,
            want_role=want_role,
            candidate_transport_cells=dto.candidate_transport_cells,
            fixed_output_stubs=fixed_stubs,
            hard_protected_corridors=hard_union,
        )
        if not validation_passed:
            atomic_rejected = val_reason or P3E3_REJECT_VALIDATION
            dto = replace(dto, rejected_reason=atomic_rejected)

    would_accept = bool(dto.precheck_passed and ratio_ok and validation_passed)
    trace = _p3e3_atomic_trace_from_dto(
        dto,
        atomic_candidate_built=True,
        validation_passed=validation_passed,
        would_accept=would_accept,
        atomic_rejected=atomic_rejected,
    )
    return dto, trace
