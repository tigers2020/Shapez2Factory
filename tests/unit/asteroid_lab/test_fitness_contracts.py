"""Phase 5 / 10B fitness and survivability contract tests."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.enums import PenaltyMode
from django_apps.asteroid_lab.optimization.fitness_contracts import (
    compute_conservative_fragility_penalties,
    evolution_distant_mutation_slot_index,
)


def test_conservative_penalties_off_returns_zero() -> None:
    fragility, corridor = compute_conservative_fragility_penalties(
        penalty_mode=PenaltyMode.OFF,
        path_cells=frozenset({(1, 0), (2, 0)}),
        other_candidate_path_cells=frozenset({(2, 0), (3, 0)}),
        narrow_segment_count=3,
    )
    assert fragility == 0.0
    assert corridor == 0.0


def test_conservative_penalties_conservative_nonzero_on_overlap() -> None:
    fragility, corridor = compute_conservative_fragility_penalties(
        penalty_mode=PenaltyMode.CONSERVATIVE,
        path_cells=frozenset({(1, 0), (2, 0)}),
        other_candidate_path_cells=frozenset({(2, 0)}),
        narrow_segment_count=2,
        alpha=2.0,
        beta=1.5,
    )
    assert corridor == 2.0
    assert fragility == 3.0


def test_evolution_distant_mutation_slot_deterministic() -> None:
    a = evolution_distant_mutation_slot_index(
        seed=42, generation=3, genome_id="g-1", population_size=8
    )
    b = evolution_distant_mutation_slot_index(
        seed=42, generation=3, genome_id="g-1", population_size=8
    )
    assert a == b
    assert 0 <= a < 8


@pytest.mark.skip(reason="FitnessEvaluator not wired; contract: mismatch domain => penalty >= 0")
def test_fitness_penalty_positive_when_probe_domain_differs_from_commit_domain() -> None:
    """Documented contract — enable when FitnessEvaluator lands."""
    raise NotImplementedError
