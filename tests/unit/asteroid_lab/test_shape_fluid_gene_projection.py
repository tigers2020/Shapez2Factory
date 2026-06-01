"""Shape → fluid gene template projection."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_EXTRACTOR_OFFSET,
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
    CANONICAL_OUTPUT_DIR,
    CANONICAL_ROUTE_PROBE_START_OFFSET,
    GeneTemplate,
)
from django_apps.asteroid_lab.genetic_sample.shape_fluid_gene_projection import (
    expand_gene_templates_with_fluid_clones,
    fluid_gene_template_from_shape,
)


def _shape_template() -> GeneTemplate:
    return GeneTemplate(
        gene_id="miner_seed_m3e_01",
        name="m3e_01",
        occupied_offsets=frozenset({CANONICAL_EXTRACTOR_OFFSET, (-1, 0)}),
        extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
        extension_offsets=((-1, 0),),
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
        throughput_factor=16,
        topology_signature_base="abc",
        resource_kind="shape",
    )


def test_fluid_gene_template_from_shape_preserves_topology() -> None:
    shape = _shape_template()
    fluid = fluid_gene_template_from_shape(shape)

    assert fluid.gene_id == "fluid_miner_seed_m3e_01"
    assert fluid.resource_kind == "fluid"
    assert fluid.occupied_offsets == shape.occupied_offsets
    assert fluid.extension_offsets == shape.extension_offsets
    assert fluid.throughput_factor == 16


def test_expand_gene_templates_with_fluid_clones_doubles_shape_pool() -> None:
    shape = _shape_template()
    expanded = expand_gene_templates_with_fluid_clones((shape,))

    assert len(expanded) == 2
    assert expanded[0].gene_id == "fluid_miner_seed_m3e_01"
    assert expanded[1].gene_id == "miner_seed_m3e_01"


def test_fluid_gene_template_from_shape_rejects_non_shape() -> None:
    fluid = _shape_template()
    fluid = fluid_gene_template_from_shape(fluid)
    with pytest.raises(ValueError, match="shape resource_kind"):
        fluid_gene_template_from_shape(fluid)
