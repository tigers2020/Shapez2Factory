"""Import vs algorithm coordinate boundaries (Sequence 12L)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.snapshots.server_coords import raw_x_to_dense_x


def test_raw_x_zero_rejected_at_dense_conversion_boundary() -> None:
    with pytest.raises(ValueError, match="no x == 0"):
        raw_x_to_dense_x(0)


def test_optimization_package_has_no_raw_to_server_bridge() -> None:
    """Algorithm tree must not import asteroid_lab raw→dense helpers (adapter boundary only)."""

    repo = Path(__file__).resolve().parents[3]
    root = repo / "django_apps" / "shapez_asteroid" / "optimization"
    forbidden = (
        "server_xy_for_raw_xy",
        "raw_x_to_dense_x",
        "asteroid_lab.snapshots.server_coords",
        "raw_x",
        "raw_y",
    )
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.relative_to(repo)} must not contain {token!r}"


def test_post_inspection_evolution_has_no_raw_coord_bridge() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "web"
        / "services"
        / "asteroid_lab_post_inspection_evolution.py"
    )
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "server_xy_for_raw_xy",
        "raw_x_to_dense_x",
        "asteroid_lab.snapshots.server_coords",
        "raw_x",
        "raw_y",
    )
    for token in forbidden:
        assert token not in text, f"post_inspection evolution must not contain {token!r}"


def test_optimization_adapter_has_no_raw_coord_bridge() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "shapez_asteroid"
        / "adapters"
        / "reconstruction_adapter.py"
    )
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "server_xy_for_raw_xy",
        "raw_x_to_dense_x",
        "Cannot map raw",
    )
    for token in forbidden:
        assert token not in text, f"optimization adapter must not contain {token!r}"
