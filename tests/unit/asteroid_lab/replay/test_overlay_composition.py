"""Tests for replay overlay layer composition."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.overlay_composition import compose_replay_overlay_cells


def _conn(x: int, y: int, connector_id: str = "ext_00") -> dict[str, object]:
    return {
        "x": x,
        "y": y,
        "overlay_role": "planned_exterior_connector",
        "connector_id": connector_id,
        "connector_role": "required",
        "tile_type": "SpaceBelt_Forward",
        "rotation": 0,
    }


def _cand(x: int, y: int, kind: str = "candidate_miner") -> dict[str, object]:
    return {"x": x, "y": y, "kind": kind, "transport": "shape_belt"}


def test_compose_preserves_connector_and_candidate_at_same_coord() -> None:
    out = compose_replay_overlay_cells(
        structural_overlay_cells=[],
        persistent_overlay_cells=[_conn(5, -6)],
        transient_overlay_cells=[_cand(5, -6)],
    )
    roles = {str(c.get("overlay_role") or c.get("kind")) for c in out}
    assert "planned_exterior_connector" in roles
    assert "candidate_miner" in roles


def test_compose_dedupes_exact_connector_duplicate_only() -> None:
    dup = _conn(5, -6, connector_id="ext_00")
    out = compose_replay_overlay_cells(
        structural_overlay_cells=[],
        persistent_overlay_cells=[dup, dict(dup)],
        transient_overlay_cells=[],
    )
    connectors = [c for c in out if c.get("overlay_role") == "planned_exterior_connector"]
    assert len(connectors) == 1


def test_compose_orders_structural_then_persistent_then_transient() -> None:
    structural = [{"x": 0, "y": 0, "overlay_role": "decode", "kind": "internal_void"}]
    persistent = [_conn(1, 0)]
    transient = [_cand(2, 0)]
    out = compose_replay_overlay_cells(
        structural_overlay_cells=structural,
        persistent_overlay_cells=persistent,
        transient_overlay_cells=transient,
    )
    assert out[0]["overlay_role"] == "decode"
    assert out[1]["overlay_role"] == "planned_exterior_connector"
    assert out[2]["kind"] == "candidate_miner"
