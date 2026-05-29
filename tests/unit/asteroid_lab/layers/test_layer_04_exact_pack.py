"""Layer 04 v2 exact_pack (branch-and-bound MWIS)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.exact_pack import (
    select_max_set_score_independent_set,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    effective_mining_gain,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def _line_graph_three() -> tuple:
    """e0—e1—e2 chain: optimal independent set is e0 + e2."""

    e0 = succeeded_probe_at(
        (0, 0),
        equivalence_key="e0",
        mining=frozenset({(0, 0), (1, 0)}),
        transport=frozenset({(9, 0)}),
    )
    e1 = succeeded_probe_at(
        (2, 0),
        equivalence_key="e1",
        mining=frozenset({(1, 0), (2, 0)}),
        transport=frozenset({(9, 1)}),
    )
    e2 = succeeded_probe_at(
        (4, 0),
        equivalence_key="e2",
        mining=frozenset({(2, 0), (3, 0)}),
        transport=frozenset({(9, 2)}),
    )
    return (e0, e1, e2)


def test_exact_pack_line_graph_picks_endpoints_not_middle() -> None:
    e0, e1, e2 = _line_graph_three()
    selected = select_max_set_score_independent_set((e0, e1, e2))
    keys = {e.candidate.equivalence_key for e in selected}
    assert keys == {"e0", "e2"}
    total = sum(effective_mining_gain(e.candidate) for e in selected)
    assert total == 4


def test_exact_pack_two_conflict_picks_higher_gain() -> None:
    low = succeeded_probe_at(
        (0, 0),
        equivalence_key="low",
        mining=frozenset({(0, 0)}),
        transport=frozenset({(9, 9)}),
    )
    high = succeeded_probe_at(
        (0, 0),
        equivalence_key="high",
        mining=frozenset({(0, 0), (1, 0), (2, 0)}),
        transport=frozenset({(9, 8)}),
    )
    selected = select_max_set_score_independent_set((low, high))
    assert len(selected) == 1
    assert selected[0].candidate.equivalence_key == "high"


def test_exact_pack_prefers_lower_candidate_id_at_full_tie() -> None:
    lower = succeeded_probe_at((0, 0), gene_key="aaa", equivalence_key="aaa")
    higher = succeeded_probe_at((0, 0), gene_key="zzz", equivalence_key="zzz")
    selected = select_max_set_score_independent_set((higher, lower))
    assert len(selected) == 1
    assert selected[0].candidate.equivalence_key == "aaa"
