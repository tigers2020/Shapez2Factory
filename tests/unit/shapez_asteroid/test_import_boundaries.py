"""Import vs algorithm coordinate boundaries (Sequence 12L)."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_ALGORITHM_COORD_TOKENS = (
    "raw_to_server",
    "server_to_raw",
    "server_xy_for_raw_xy",
    "raw_x_to_dense_x",
    "asteroid_lab.snapshots.server_coords",
    "raw_x",
    "raw_y",
    "raw_coord",
    "visual_coord",
)


def test_optimization_package_has_no_raw_to_server_bridge() -> None:
    """Algorithm tree must not import raw/server conversion helpers."""

    repo = Path(__file__).resolve().parents[3]
    root = repo / "django_apps" / "shapez_asteroid" / "optimization"
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
            assert token not in text, f"{path.relative_to(repo)} must not contain {token!r}"


def test_post_inspection_evolution_has_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = repo / "django_apps" / "web" / "services" / "asteroid_lab_post_inspection_evolution.py"
    text = path.read_text(encoding="utf-8")
    for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
        assert token not in text, f"post_inspection evolution must not contain {token!r}"


def test_asteroid_lab_optimization_services_have_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    root = repo / "django_apps" / "asteroid_lab" / "services"
    for path in sorted(root.glob("*optimization*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
            assert token not in text, f"{path.relative_to(repo)} must not contain {token!r}"


def test_optimization_adapter_has_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = repo / "django_apps" / "shapez_asteroid" / "adapters" / "reconstruction_adapter.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "raw_to_server",
        "server_to_raw",
        "server_xy_for_raw_xy",
        "raw_x_to_dense_x",
        "Cannot map raw",
        "raw_coord",
        "visual_coord",
    )
    for token in forbidden:
        assert token not in text, f"optimization adapter must not contain {token!r}"
