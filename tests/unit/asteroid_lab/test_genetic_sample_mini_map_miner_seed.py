"""Admin mini-map for DB miner seeds (island-local X==0 column)."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample_mini_map import genetic_sample_mini_map_html
from django_apps.asteroid_lab.models import GeneticSample
from tests.unit.asteroid_lab.test_genetic_sample_mini_map import _by_raw, _MiniMapCellParser


def _parse_cells(html: str) -> dict[tuple[int, int], dict[str, int | str]]:
    p = _MiniMapCellParser()
    p.feed(html)
    p.close()
    return _by_raw(p.cells)


@pytest.mark.django_db
def test_miner_seed_m2e_02_mini_map_shows_raw_x_zero_column(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    """``miner_seed_m2e_02``: omitted ``X`` (raw 0) and ``X==-1`` both appear in the grid."""

    call_command("seed_miner_patterns", verbosity=0)
    row = GeneticSample.objects.get(gene_key="miner_seed_m2e_02")
    html = str(genetic_sample_mini_map_html(row.decoded_json))
    by_s = _parse_cells(html)
    raw_xs = {xy[0] for xy in by_s if by_s[xy]["data-sprite"]}
    assert 0 in raw_xs
    assert -1 in raw_xs


@pytest.mark.django_db
def test_miner_seed_m0e_01_mini_map_includes_raw_x_zero(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    call_command("seed_miner_patterns", verbosity=0)
    row = GeneticSample.objects.get(gene_key="miner_seed_m0e_01")
    html = str(genetic_sample_mini_map_html(row.decoded_json))
    by_s = _parse_cells(html)
    assert any(xy[0] == 0 and by_s[xy]["data-sprite"] for xy in by_s)
