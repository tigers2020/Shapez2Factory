"""P3-E3 guarded commit gates and transport snapshot helpers."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
)


def _p3e3_rollback_guarded_transport_cells(
    *,
    known_good_transport_snapshot: dict[Coord, str],
) -> dict[Coord, str]:
    """Restore transport role map from greedy Pass3 snapshot (including per-cell role strings)."""

    return dict(known_good_transport_snapshot)


def _p3e3_transport_dict_from_candidate_cells(
    candidate_transport_cells: frozenset[Coord],
    *,
    want_role: str,
) -> dict[Coord, str]:
    """Atomic assignment: one role string per candidate coordinate."""

    return {c: want_role for c in candidate_transport_cells}


def _p3e3_should_commit_guarded_candidate(
    *,
    guarded_enabled: bool,
    candidate: P3E3GuardedCommitCandidate | None,
    candidate_validation_passed: bool | None,
    would_accept: bool | None,
) -> bool:
    """Single gate for P3-E3b-2a live swap (E3b-1 candidate must already pass all checks)."""

    return bool(
        guarded_enabled
        and candidate is not None
        and candidate.precheck_passed
        and candidate_validation_passed is True
        and would_accept is True
    )


def _p3e3_atomic_phase_deferred_by_shadow_alignment(shadow_trace: dict[str, Any]) -> bool:
    """When shadow ran and lex did not complete for all greedy-ready outlets, skip E3b atomic.

    Mirrors greedy-only / skip policy: running :func:`_p3e3_collect_guarded_lex_replacement` again
    would reject with the same class of outcome while doubling lex work.
    """

    if not shadow_trace.get("p3e2_shadow_enabled"):
        return False
    return not bool(shadow_trace.get("p3e2_lex_found"))
