import time

import pytest

from django_apps.shapez_solver.services.inventory_search_solver import (
    InventorySearchError,
    InventorySearchRequest,
    InventorySearchSolver,
)


def test_inventory_search_solver_returns_zero_operation_plan_for_existing_target() -> None:
    plan = InventorySearchSolver().solve(
        InventorySearchRequest(
            target_code="RcRcRcRc",
            target_count=1,
            source_counts={"RcRcRcRc": 1},
        )
    )

    assert plan.steps == ()
    assert plan.final_inventory["RcRcRcRc"] == 1
    assert plan.cost.as_tuple() == (0, 0, 0, 0)
    assert plan.used_macro_kinds == ()


def test_inventory_search_solver_finds_basic_swapper_plan() -> None:
    plan = InventorySearchSolver().solve(
        InventorySearchRequest(
            target_code="RcRcCuCu",
            target_count=1,
            source_counts={"RcRcRcRc": 1, "CuCuCuCu": 1},
            max_states=200,
            max_steps=4,
        )
    )

    assert [step.operation.value for step in plan.steps] == ["swapper"]
    assert plan.final_inventory["RcRcCuCu"] == 1
    assert plan.final_inventory["CuCuRcRc"] == 1
    assert plan.used_macro_kinds == ()


def test_inventory_search_solver_deadline_raises() -> None:
    with pytest.raises(InventorySearchError, match="deadline exceeded"):
        InventorySearchSolver().solve(
            InventorySearchRequest(
                target_code="RuCuRuCu",
                target_count=2,
                source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1},
                max_states=500_000,
                max_steps=40,
                deadline_monotonic=time.monotonic() - 1.0,
            )
        )


def test_inventory_search_solver_abcc_batch_macro_shortcut() -> None:
    plan = InventorySearchSolver().solve(
        InventorySearchRequest(
            target_code="CuRuSuSu",
            target_count=4,
            source_counts={"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2},
            max_states=100,
            max_steps=28,
        )
    )

    assert plan.final_inventory.get("CuRuSuSu") == 4
    assert "ABCC_BATCH" in plan.used_macro_kinds
    assert "ABCC_BATCH:builtin" in plan.used_macro_sources
    assert len(plan.steps) >= 1
