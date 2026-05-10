"""Tests for ``SolverMutationTransaction`` and mining map diff helpers."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_mutation_transaction as mut_txn,
)


def test_copy_mining_map_rows_is_deep() -> None:
    src = [{"x": 1, "y": 2, "role": "occupied", "meta": {"k": 1}}]
    cpy = mut_txn.copy_mining_map_rows(src)
    assert cpy == src
    cpy[0]["meta"]["k"] = 99
    assert src[0]["meta"]["k"] == 1


def test_diff_mining_maps_counts_roles() -> None:
    before = [{"x": 1, "y": 1, "role": "empty"}]
    after = [
        {"x": 1, "y": 1, "role": "occupied"},
        {"x": 2, "y": 1, "role": "empty"},
    ]
    d = mut_txn.diff_mining_maps(before, after)
    assert d["coords_added"] == 1
    assert d["coords_removed"] == 0
    assert d["role_changes"] == 1


def test_transaction_rollback_restores_baseline() -> None:
    base = [{"x": 1, "y": 1, "role": "empty"}]
    txn = mut_txn.SolverMutationTransaction(base)
    txn.begin()
    wm = txn.working_map
    wm[0] = {"x": 1, "y": 1, "role": "occupied"}
    restored = txn.rollback()
    assert restored == base
    assert txn.working_map == base


def test_transaction_commit_requires_open() -> None:
    txn = mut_txn.SolverMutationTransaction([{"x": 1, "y": 1, "role": "empty"}])
    try:
        txn.commit()
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")
