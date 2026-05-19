"""Gene projection tests (PR1, Server Coord only)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.enums import Direction
from django_apps.asteroid_lab.optimization.gene_projection import project_gene_placement
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _minimal_template():
    templates = load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")
    return templates[0]


def test_gene_projection_uses_relative_offsets() -> None:
    gene = _minimal_template()
    anchor = (5, 3)
    placed = project_gene_placement(anchor=anchor, rotation=Direction.E, gene=gene)

    assert placed.extractor == anchor
    assert placed.fixed_output_transport == (6, 3)
    assert placed.route_probe_start == (7, 3)
    assert placed.occupied_cells == frozenset({anchor})


@pytest.mark.parametrize(
    ("rotation", "expected_transport", "expected_probe_start"),
    [
        (Direction.E, (6, 3), (7, 3)),
        (Direction.S, (5, 2), (5, 1)),
        (Direction.W, (4, 3), (3, 3)),
        (Direction.N, (5, 4), (5, 5)),
    ],
)
def test_gene_projection_rotates_canonical_e_to_all_directions(
    rotation: Direction,
    expected_transport: tuple[int, int],
    expected_probe_start: tuple[int, int],
) -> None:
    gene = _minimal_template()
    anchor = (5, 3)
    placed = project_gene_placement(anchor=anchor, rotation=rotation, gene=gene)

    assert placed.output_dir is rotation
    assert placed.fixed_output_transport == expected_transport
    assert placed.route_probe_start == expected_probe_start
    assert placed.route_probe_start not in placed.occupied_cells
    assert placed.fixed_output_transport not in placed.occupied_cells


def test_gene_projection_uses_server_coords_only() -> None:
    """Optimization projection must not call raw/server conversion helpers."""

    gene = _minimal_template()
    with patch(
        "django_apps.asteroid_lab.snapshots.server_coords.server_xy_for_raw_xy",
    ) as mock_raw:
        project_gene_placement(anchor=(0, 0), rotation=Direction.E, gene=gene)
        mock_raw.assert_not_called()
