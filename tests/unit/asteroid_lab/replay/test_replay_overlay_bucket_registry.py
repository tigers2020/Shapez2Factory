"""Overlay bucket registry — semantic lookup vs paint target roles."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_overlay_bucket_registry import (
    OverlayBucketRole,
    collect_overlay_cells_for_paint_target,
    collect_overlay_cells_for_semantic_lookup,
    overlay_bucket_keys_for_role,
)


def test_semantic_lookup_includes_solver_overlay_buckets() -> None:
    keys = overlay_bucket_keys_for_role(OverlayBucketRole.SEMANTIC_LOOKUP)
    assert "components" in keys
    assert "main_component_candidate" in keys
    assert "cleanup_candidate_cells" in keys
    assert "equipment_bundles" not in keys


def test_paint_target_includes_equipment_bundles_not_solver_only_buckets() -> None:
    keys = overlay_bucket_keys_for_role(OverlayBucketRole.PAINT_TARGET)
    assert "equipment_bundles" in keys
    assert "components" not in keys
    assert "cells" in keys


def test_semantic_harvest_includes_dynamic_dict_cells_json() -> None:
    overlay = {
        "cells": [{"x": 1, "y": 0, "cell_kind": "space_belt"}],
        "custom_bundle": {"cells_json": [{"x": 2, "y": 0, "cell_kind": "space_pipe"}]},
    }
    harvested = collect_overlay_cells_for_semantic_lookup(overlay)
    kinds = {str(c.get("cell_kind") or c.get("kind") or "") for c in harvested}
    assert kinds == {"space_belt", "space_pipe"}


def test_paint_harvest_uses_equipment_bundles_only_for_paint_role() -> None:
    overlay = {
        "equipment_bundles": [{"cells_json": [{"x": 3, "y": 0, "cell_kind": "fluid_miner"}]}],
        "components": [{"cells": [{"x": 4, "y": 0, "cell_kind": "candidate_miner"}]}],
    }
    paint = collect_overlay_cells_for_paint_target(overlay)
    semantic = collect_overlay_cells_for_semantic_lookup(overlay)
    paint_kinds = {str(c.get("cell_kind") or c.get("kind") or "") for c in paint}
    semantic_kinds = {str(c.get("cell_kind") or c.get("kind") or "") for c in semantic}
    assert paint_kinds == {"fluid_miner"}
    assert semantic_kinds == {"candidate_miner"}
