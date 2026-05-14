"""Copy-on-write style mining-map transaction boundary (P4 reclaim entry, MVP).

See ``documents/Algorithm/solver_mutation_transaction_plan_2026-05-10.md``.
"""

from __future__ import annotations

import copy
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)


def copy_mining_map_rows(mining_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deep copy of layout rows (nested values preserved)."""

    return copy.deepcopy(mining_map)


def diff_mining_maps(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    *,
    role_key: str = "role",
) -> dict[str, Any]:
    """Summarize cell-level differences between two maps (deterministic counts only)."""

    b = cells_dict_from_mining_map(before)
    a = cells_dict_from_mining_map(after)
    keys_b = frozenset(b)
    keys_a = frozenset(a)
    added = keys_a - keys_b
    removed = keys_b - keys_a
    common = keys_a & keys_b
    role_changes = 0
    for c in common:
        rb = b[c].get(role_key)
        ra = a[c].get(role_key)
        if rb != ra:
            role_changes += 1
    return {
        "cell_count_before": len(b),
        "cell_count_after": len(a),
        "coords_added": len(added),
        "coords_removed": len(removed),
        "role_changes": role_changes,
    }


class SolverMutationTransaction:
    """Minimal single-level transaction: baseline snapshot + mutable working map.

    Nested ``begin()`` is not supported. ``rollback()`` returns a fresh copy of the baseline
    suitable for re-assigning the pipeline ``map_final`` and resets ``working_map`` to match.
    """

    def __init__(self, mining_map: list[dict[str, Any]]) -> None:
        self._baseline: list[dict[str, Any]] = copy_mining_map_rows(mining_map)
        self._working: list[dict[str, Any]] = copy_mining_map_rows(mining_map)
        self._open = False

    @property
    def working_map(self) -> list[dict[str, Any]]:
        """Mutable map passed into reclaim / probe callees."""

        return self._working

    def begin(self) -> None:
        if self._open:
            msg = "SolverMutationTransaction.begin: nested transactions are not supported"
            raise RuntimeError(msg)
        self._open = True

    def commit(self) -> None:
        if not self._open:
            msg = "SolverMutationTransaction.commit: not in an open transaction"
            raise RuntimeError(msg)
        self._open = False

    def rollback(self) -> list[dict[str, Any]]:
        """Restore working from baseline; return a new deep copy for the caller."""

        if not self._open:
            msg = "SolverMutationTransaction.rollback: not in an open transaction"
            raise RuntimeError(msg)
        self._working = copy_mining_map_rows(self._baseline)
        self._open = False
        return copy_mining_map_rows(self._baseline)

    def snapshot(self) -> list[dict[str, Any]]:
        """Deep copy of the current working map."""

        return copy_mining_map_rows(self._working)
