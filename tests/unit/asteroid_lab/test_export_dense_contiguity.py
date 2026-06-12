"""Export ``X`` columns: dense index set must have no gaps (west-branch spread regression)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    export_dense_x_is_contiguous,
    export_dense_x_set,
    to_official_island_root,
)
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import build_layout_root
from django_apps.asteroid_lab.snapshots.copy_json_coords import raw_x_to_export_column


def _lab_to_official_entries(
    exts: list[dict[str]], *, transport_kind: str = "pipe"
) -> list[dict[str]]:
    lab = build_layout_root(transport_kind=transport_kind, exts=exts)
    official = to_official_island_root(lab)
    entries = official["BP"]["Entries"]
    assert isinstance(entries, list)
    return entries


def test_export_dense_x_contiguous_west_branch_lab() -> None:
    exts = [
        {
            "id": "E1",
            "coord": (-1, 0),
            "parent_id": "E0",
            "parent_coord": (0, 0),
            "attach_dir": "W",
        },
        {
            "id": "E2",
            "coord": (-1, 1),
            "parent_id": "E1",
            "parent_coord": (-1, 0),
            "attach_dir": "S",
        },
        {"id": "E3", "coord": (0, 1), "parent_id": "E0", "parent_coord": (0, 0), "attach_dir": "S"},
    ]
    entries = _lab_to_official_entries(exts)
    assert export_dense_x_is_contiguous(entries)
    dense = export_dense_x_set(entries)
    assert -3 not in dense
    assert -2 not in dense or len(dense) <= 2


def test_exhaustive_genes_official_export_dense_x_never_gapped(
    exhaustive_genes_ext3: tuple[list, object],
) -> None:
    genes, _stats = exhaustive_genes_ext3
    for g in genes:
        official = to_official_island_root(g.layout_json)
        entries = official["BP"]["Entries"]
        assert isinstance(entries, list)
        assert export_dense_x_is_contiguous(entries)


def test_spread_bug_pattern_dense_set_has_gap() -> None:
    """Historical bug export: dense columns {-3, -1, 0} with missing -2."""

    export_x_values = (-3, -1, 0)
    dense = {raw_x_to_export_column(x) for x in export_x_values}
    assert dense == {-3, -1, 0}
    assert not (max(dense) - min(dense) + 1 == len(dense))
