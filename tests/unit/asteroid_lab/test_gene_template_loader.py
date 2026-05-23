"""GeneTemplate loader and canonical contract tests (PR1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
)
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
    CANONICAL_ROUTE_PROBE_START_OFFSET,
    GeneTemplate,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.genetic_sample.gene_template_loader import (
    gene_template_from_generated_sample,
    load_gene_templates_from_json,
    parse_gene_template_record,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def test_gene_template_loader_loads_fixture_json() -> None:
    templates = load_gene_templates_from_json(_FIXTURE_DIR)
    ids = {t.gene_id for t in templates}
    assert "fixture_minimal_extractor_e" in ids
    assert "fixture_ext1_n" in ids
    assert len(templates) >= 3

    minimal = next(t for t in templates if t.gene_id == "fixture_minimal_extractor_e")
    assert minimal.fixed_output_transport_offset == CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET
    assert minimal.route_probe_start_offset == CANONICAL_ROUTE_PROBE_START_OFFSET
    assert minimal.output_dir is Direction.E
    assert minimal.throughput_factor == 4


def test_gene_template_from_generated_sample_uses_canonical_e(
    exhaustive_genes_ext1_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    genes, _stats = exhaustive_genes_ext1_belt
    assert genes
    tpl = gene_template_from_generated_sample(genes[0])
    assert tpl.output_dir is Direction.E
    assert tpl.extractor_offset == (0, 0)
    assert tpl.fixed_output_transport_offset == (1, 0)
    assert tpl.route_probe_start_offset == (2, 0)
    assert tpl.fixed_output_transport_offset not in tpl.occupied_offsets
    assert tpl.route_probe_start_offset not in tpl.occupied_offsets


def test_gene_template_rejects_stub_inside_occupied() -> None:
    with pytest.raises(ValueError, match="route_probe_start_offset"):
        parse_gene_template_record(
            {
                "gene_id": "bad_stub",
                "name": "Bad",
                "output_dir": "e",
                "extractor_offset": [0, 0],
                "extension_offsets": [],
                "occupied_offsets": [[0, 0]],
                "fixed_output_transport_offset": [1, 0],
                "route_probe_start_offset": [0, 0],
                "throughput_factor": 4,
                "topology_signature_base": "bad",
            }
        )


def test_gene_template_rejects_transport_inside_occupied() -> None:
    with pytest.raises(ValueError, match="fixed_output_transport_offset"):
        parse_gene_template_record(
            {
                "gene_id": "bad_transport",
                "name": "Bad",
                "output_dir": "e",
                "extractor_offset": [0, 0],
                "extension_offsets": [[1, 0]],
                "occupied_offsets": [[0, 0], [1, 0]],
                "fixed_output_transport_offset": [1, 0],
                "route_probe_start_offset": [2, 0],
                "throughput_factor": 8,
                "topology_signature_base": "bad",
            }
        )


@pytest.mark.parametrize(
    ("extension_count", "expected_factor"),
    [(0, 4), (1, 8), (2, 12), (3, 16)],
)
def test_gene_template_throughput_factor_matches_extension_count(
    extension_count: int,
    expected_factor: int,
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
    exhaustive_genes_ext1_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
    exhaustive_genes_ext3: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    assert throughput_factor_for_extension_count(extension_count) == expected_factor

    if extension_count == 0:
        genes, _ = exhaustive_genes_ext0_belt
    elif extension_count == 1:
        genes, _ = exhaustive_genes_ext1_belt
    else:
        genes, _ = exhaustive_genes_ext3
    match = [g for g in genes if g.extension_count == extension_count]
    assert match
    tpl = gene_template_from_generated_sample(match[0])
    assert tpl.throughput_factor == expected_factor


def test_gene_template_post_init_validates() -> None:
    with pytest.raises(ValueError, match="route_probe_start_offset"):
        GeneTemplate(
            gene_id="x",
            name="x",
            occupied_offsets=frozenset({(0, 0)}),
            extractor_offset=(0, 0),
            extension_offsets=(),
            output_dir=Direction.E,
            fixed_output_transport_offset=(1, 0),
            route_probe_start_offset=(0, 0),
            throughput_factor=4,
            topology_signature_base="x",
        )
