"""Deterministic solver state hashing (mining_map + optional routing subset)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    ROUTING_STATE_KEYS_STEP4_HASH,
    mining_map_state_hash,
    normalized_solver_state_payload,
    solver_state_sha256_hex,
)


def test_mining_map_hash_deterministic_same_map_twice() -> None:
    rows = [
        {"x": 2, "y": 1, "role": "belt"},
        {"x": 1, "y": 1, "role": "occupied"},
    ]
    a = mining_map_state_hash(rows)
    b = mining_map_state_hash(list(reversed(rows)))
    assert a == b
    assert len(a) == 64


def test_mining_map_hash_order_independent_of_row_insertion() -> None:
    m1 = [{"x": 5, "y": 3, "role": "pipe"}, {"x": 4, "y": 3, "role": "belt"}]
    m2 = [m1[1], m1[0]]
    assert mining_map_state_hash(m1) == mining_map_state_hash(m2)


def test_routing_subset_changes_hash() -> None:
    m = [{"x": 1, "y": 1, "role": "belt"}]
    rs_a = {"hard_protected_corridors": [[1, 1]], "soft_protected_corridors": []}
    rs_b = {"hard_protected_corridors": [], "soft_protected_corridors": [[2, 2]]}
    ha = solver_state_sha256_hex(
        m,
        routing_state=rs_a,
        routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
    )
    hb = solver_state_sha256_hex(
        m,
        routing_state=rs_b,
        routing_state_keys=ROUTING_STATE_KEYS_STEP4_HASH,
    )
    assert ha != hb


def test_map_only_omits_routing_in_payload() -> None:
    p = normalized_solver_state_payload(
        [{"x": 1, "y": 1, "role": "belt"}],
        routing_state={"hard_protected_corridors": [[9, 9]]},
        routing_state_keys=None,
    )
    assert "routing_state" not in p
