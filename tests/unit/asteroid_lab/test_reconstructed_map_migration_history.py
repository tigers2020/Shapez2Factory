from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_MIGRATIONS = _REPO / "django_apps" / "asteroid_lab" / "migrations"


def test_migration_0006_keeps_original_server_coordinate_columns() -> None:
    text = (_MIGRATIONS / "0006_reconstructed_map_layers.py").read_text(encoding="utf-8")

    assert 'name="anchor_server_x"' in text
    assert 'name="anchor_server_y"' in text
    assert '("server_x", models.IntegerField())' in text
    assert '("server_y", models.IntegerField())' in text
    assert 'fields=["map", "server_x", "server_y"]' in text
    assert 'fields=("map", "server_x", "server_y", "kind", "source")' in text


def test_migration_0009_removes_original_anchor_server_columns() -> None:
    text = (_MIGRATIONS / "0009_reconstructed_map_full_map_only.py").read_text(encoding="utf-8")

    assert 'name="anchor_server_x"' in text
    assert 'name="anchor_server_y"' in text
