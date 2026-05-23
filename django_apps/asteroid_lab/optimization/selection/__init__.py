"""RTTP Layer 3 candidate selection."""

from django_apps.asteroid_lab.optimization.selection.equivalence import (
    CandidateEquivalenceKey,
    dedupe_candidates,
    equivalence_key,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    select_genome,
)

__all__ = [
    "CandidateEquivalenceKey",
    "PlacementGenome",
    "SelectionConfig",
    "dedupe_candidates",
    "equivalence_key",
    "select_genome",
]
