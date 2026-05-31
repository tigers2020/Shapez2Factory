"""Project shape miner ``GeneTemplate`` rows to fluid pump variants (same topology).

CANON: shape Asteroid Miner and fluid Asteroid Pump share extension topology; only
``resource_kind`` and absolute mini-unit rate differ (30 vs 300 shapes/L per min at
base; ×16 → 480 vs 4,800 per platform). Exterior saturation ratios differ (12 vs 72)
and are owned by L2 EVTC — not duplicated here.
"""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.genetic_sample.gene_template import GeneTemplate

FLUID_GENE_ID_PREFIX = "fluid_"


def fluid_gene_template_from_shape(shape: GeneTemplate) -> GeneTemplate:
    """Clone a shape miner template as a fluid pump (canonical-E footprint unchanged)."""

    if shape.resource_kind != "shape":
        msg = f"expected shape resource_kind, got {shape.resource_kind!r}"
        raise ValueError(msg)
    gene_id = shape.gene_id
    if gene_id.startswith(FLUID_GENE_ID_PREFIX):
        fluid_id = gene_id
    else:
        fluid_id = f"{FLUID_GENE_ID_PREFIX}{gene_id}"
    return replace(
        shape,
        gene_id=fluid_id,
        name=f"{shape.name} (fluid)",
        resource_kind="fluid",
    )


def expand_gene_templates_with_fluid_clones(
    templates: tuple[GeneTemplate, ...],
) -> tuple[GeneTemplate, ...]:
    """Append fluid projections for every shape template; sort by ``gene_id``."""

    expanded: list[GeneTemplate] = list(templates)
    for template in templates:
        if template.resource_kind == "shape":
            expanded.append(fluid_gene_template_from_shape(template))
    expanded.sort(key=lambda t: t.gene_id)
    return tuple(expanded)


__all__ = [
    "FLUID_GENE_ID_PREFIX",
    "expand_gene_templates_with_fluid_clones",
    "fluid_gene_template_from_shape",
]
