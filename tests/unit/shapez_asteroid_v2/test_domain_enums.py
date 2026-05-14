from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    SolverTermination,
    SourceKind,
    TransportKind,
)


def test_transport_kind_values() -> None:
    assert TransportKind.SHAPE_BELT.value == "shape_belt"
    assert TransportKind.FLUID_PIPE.value == "fluid_pipe"


def test_placement_commit_states_distinct() -> None:
    states = frozenset(PlacementCommitState)
    assert len(states) == 4


def test_source_kind_unknown_exists() -> None:
    assert SourceKind.UNKNOWN.value == "unknown"


def test_solver_termination_values() -> None:
    assert SolverTermination.SUCCESS.value == "success"
