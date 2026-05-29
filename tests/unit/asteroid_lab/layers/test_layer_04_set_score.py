"""Layer 04 v2 set_score helpers."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.set_score import (
    compare_set_scores,
    set_score_tuple,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    effective_mining_gain,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_set_score_prefers_higher_count_at_equal_gain() -> None:
    two_cell = frozenset({(0, 0), (1, 0)})
    three_cell = frozenset({(0, 0), (1, 0), (2, 0)})
    a = succeeded_probe_at(
        (0, 0),
        equivalence_key="a",
        mining=three_cell,
        transport=frozenset({(9, 0)}),
    )
    b = succeeded_probe_at(
        (5, 0),
        equivalence_key="b",
        mining=three_cell,
        transport=frozenset({(9, 1)}),
    )
    p = succeeded_probe_at(
        (10, 0),
        equivalence_key="p",
        mining=two_cell,
        transport=frozenset({(9, 2)}),
    )
    q = succeeded_probe_at(
        (15, 0),
        equivalence_key="q",
        mining=two_cell,
        transport=frozenset({(9, 3)}),
    )
    r = succeeded_probe_at(
        (20, 0),
        equivalence_key="r",
        mining=two_cell,
        transport=frozenset({(9, 4)}),
    )
    score_pair = set_score_tuple(entries=(a, b))
    score_triple = set_score_tuple(entries=(p, q, r))
    assert score_pair[0] == score_triple[0] == 6
    assert score_pair[1] == 2
    assert score_triple[1] == 3
    assert compare_set_scores(score_triple, score_pair) > 0


def test_set_score_prefers_lower_route_cost_at_equal_gain_and_count() -> None:
    cheap_a = succeeded_probe_at((0, 0), equivalence_key="cheap_a", route_cost=1)
    cheap_b = succeeded_probe_at((10, 0), equivalence_key="cheap_b", route_cost=1)
    costly_a = succeeded_probe_at((0, 5), equivalence_key="costly_a", route_cost=50)
    costly_b = succeeded_probe_at((10, 5), equivalence_key="costly_b", route_cost=50)
    assert effective_mining_gain(cheap_a.candidate) == effective_mining_gain(costly_a.candidate)
    assert effective_mining_gain(cheap_b.candidate) == effective_mining_gain(costly_b.candidate)
    cheap_score = set_score_tuple(entries=(cheap_a, cheap_b))
    costly_score = set_score_tuple(entries=(costly_a, costly_b))
    assert cheap_score[0] == costly_score[0]
    assert cheap_score[1] == costly_score[1]
    assert compare_set_scores(cheap_score, costly_score) > 0


def test_set_score_prefers_lower_candidate_ids_at_full_tie() -> None:
    lower = succeeded_probe_at((0, 0), gene_key="aaa", equivalence_key="aaa")
    higher = succeeded_probe_at((0, 0), gene_key="zzz", equivalence_key="zzz")
    lower_score = set_score_tuple(entries=(lower,))
    higher_score = set_score_tuple(entries=(higher,))
    assert lower_score[:4] == higher_score[:4]
    assert lower_score[4] < higher_score[4]
    assert compare_set_scores(lower_score, higher_score) > 0
