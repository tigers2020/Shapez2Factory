"""Load ``GeneTemplate`` from JSON fixtures or ``GeneratedSampleGene`` (no Django ORM)."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    EXTRACTOR_GRID,
    OUTPUT_TRANSPORT_GRID,
    GeneratedSampleGene,
)
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_EXTRACTOR_OFFSET,
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
    CANONICAL_OUTPUT_DIR,
    CANONICAL_ROUTE_PROBE_START_OFFSET,
    ExtensionAttachment,
    GeneTemplate,
    extension_attachments_parent_first,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_ROUTE_PROBE_START_OFFSET_CANONICAL: Coord = (2, 0)


def _parse_coord_pair(raw: object, *, field: str) -> Coord:
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        msg = f"{field} must be [x, y]"
        raise ValueError(msg)
    x, y = raw[0], raw[1]
    if not isinstance(x, int) or not isinstance(y, int):
        msg = f"{field} coordinates must be integers"
        raise ValueError(msg)
    return (x, y)


def _parse_direction(raw: object) -> Direction:
    if isinstance(raw, Direction):
        return raw
    if not isinstance(raw, str):
        msg = "output_dir must be a direction string"
        raise ValueError(msg)
    for member in Direction:
        if member.value == raw.lower() or member.name.lower() == raw.lower():
            return member
    msg = f"unknown output_dir: {raw!r}"
    raise ValueError(msg)


def parse_gene_template_record(record: dict[str]) -> GeneTemplate:
    gene_id = record.get("gene_id")
    if not isinstance(gene_id, str) or not gene_id:
        msg = "gene_id must be a non-empty string"
        raise ValueError(msg)

    name = record.get("name")
    if not isinstance(name, str) or not name:
        msg = "name must be a non-empty string"
        raise ValueError(msg)

    output_dir = _parse_direction(record.get("output_dir", "e"))
    if output_dir is not CANONICAL_OUTPUT_DIR:
        msg = "fixture GeneTemplate must use canonical output_dir E"
        raise ValueError(msg)

    extractor_offset = _parse_coord_pair(
        record.get("extractor_offset", [0, 0]),
        field="extractor_offset",
    )
    if extractor_offset != CANONICAL_EXTRACTOR_OFFSET:
        msg = "extractor_offset must be [0, 0] for canonical templates"
        raise ValueError(msg)

    raw_ext = record.get("extension_offsets", [])
    if not isinstance(raw_ext, list):
        msg = "extension_offsets must be a list"
        raise ValueError(msg)
    extension_offsets = tuple(
        sorted(
            (_parse_coord_pair(item, field="extension_offsets[]") for item in raw_ext),
            key=lambda c: (c[0], c[1]),
        )
    )

    occupied_raw = record.get("occupied_offsets")
    if occupied_raw is None:
        occupied_offsets = frozenset({extractor_offset, *extension_offsets})
    else:
        if not isinstance(occupied_raw, list):
            msg = "occupied_offsets must be a list"
            raise ValueError(msg)
        occupied_offsets = frozenset(
            _parse_coord_pair(item, field="occupied_offsets[]") for item in occupied_raw
        )

    fixed_output_transport_offset = _parse_coord_pair(
        record.get(
            "fixed_output_transport_offset",
            list(CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET),
        ),
        field="fixed_output_transport_offset",
    )
    route_probe_start_offset = _parse_coord_pair(
        record.get(
            "route_probe_start_offset",
            list(CANONICAL_ROUTE_PROBE_START_OFFSET),
        ),
        field="route_probe_start_offset",
    )

    throughput_factor = record.get("throughput_factor")
    if throughput_factor is None:
        throughput_factor = throughput_factor_for_extension_count(len(extension_offsets))
    if not isinstance(throughput_factor, int):
        msg = "throughput_factor must be an integer"
        raise ValueError(msg)

    topology_signature_base = record.get("topology_signature_base", gene_id)
    if not isinstance(topology_signature_base, str) or not topology_signature_base:
        msg = "topology_signature_base must be a non-empty string"
        raise ValueError(msg)

    raw_attach = record.get("extension_attachments", [])
    extension_attachments: tuple[ExtensionAttachment, ...] = ()
    if raw_attach:
        if not isinstance(raw_attach, list):
            msg = "extension_attachments must be a list"
            raise ValueError(msg)
        parsed: list[ExtensionAttachment] = []
        for item in raw_attach:
            if not isinstance(item, dict):
                msg = "extension_attachments[] must be objects"
                raise ValueError(msg)
            ad = item.get("attach_dir")
            if not isinstance(ad, str) or not ad:
                msg = "extension_attachments[].attach_dir required"
                raise ValueError(msg)
            parsed.append(
                ExtensionAttachment(
                    parent_offset=_parse_coord_pair(
                        item.get("parent_offset"), field="parent_offset"
                    ),
                    child_offset=_parse_coord_pair(item.get("child_offset"), field="child_offset"),
                    attach_dir=ad,
                )
            )
        extension_attachments = tuple(
            sorted(parsed, key=lambda a: (a.child_offset[0], a.child_offset[1]))
        )

    return GeneTemplate(
        gene_id=gene_id,
        name=name,
        occupied_offsets=occupied_offsets,
        extractor_offset=extractor_offset,
        extension_offsets=extension_offsets,
        output_dir=output_dir,
        fixed_output_transport_offset=fixed_output_transport_offset,
        route_probe_start_offset=route_probe_start_offset,
        throughput_factor=throughput_factor,
        topology_signature_base=topology_signature_base,
        extension_attachments=extension_attachments,
    )


def _extension_attachments_from_generated(
    gene: GeneratedSampleGene,
) -> tuple[ExtensionAttachment, ...]:
    by_id = {n.node_id: n for n in gene.nodes}
    parsed: list[ExtensionAttachment] = []
    for node in gene.nodes:
        if node.kind != "extension" or node.parent_id is None or node.attach_dir is None:
            continue
        parent = by_id.get(node.parent_id)
        if parent is None:
            continue
        parsed.append(
            ExtensionAttachment(
                parent_offset=parent.coord,
                child_offset=node.coord,
                attach_dir=str(node.attach_dir),
            )
        )
    return extension_attachments_parent_first(tuple(parsed))


def load_gene_templates_from_json(path: str | Path) -> tuple[GeneTemplate, ...]:
    p = Path(path)
    if p.is_dir():
        files = sorted(p.glob("*.json"))
    elif p.is_file():
        files = [p]
    else:
        msg = f"gene template path not found: {p}"
        raise FileNotFoundError(msg)

    templates: list[GeneTemplate] = []
    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    msg = f"each record in {fp} must be an object"
                    raise ValueError(msg)
                templates.append(parse_gene_template_record(item))
        elif isinstance(data, dict):
            templates.append(parse_gene_template_record(data))
        else:
            msg = f"unsupported JSON root in {fp}"
            raise ValueError(msg)

    return tuple(sorted(templates, key=lambda g: g.gene_id))


def gene_template_from_generated_sample(gene: GeneratedSampleGene) -> GeneTemplate:
    extension_coords: list[Coord] = []
    for node in gene.nodes:
        if node.kind == "extension":
            extension_coords.append(node.coord)

    extension_offsets = tuple(sorted(extension_coords, key=lambda c: (c[0], c[1])))
    occupied_offsets = frozenset({EXTRACTOR_GRID, *extension_offsets})

    if gene.extension_count != len(extension_offsets):
        msg = "extension_count does not match extension nodes"
        raise ValueError(msg)

    if OUTPUT_TRANSPORT_GRID in occupied_offsets:
        msg = "output transport cell must not be in occupied offsets"
        raise ValueError(msg)

    return GeneTemplate(
        gene_id=gene.key,
        name=gene.name,
        occupied_offsets=occupied_offsets,
        extractor_offset=EXTRACTOR_GRID,
        extension_offsets=extension_offsets,
        output_dir=CANONICAL_OUTPUT_DIR,
        fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
        route_probe_start_offset=_ROUTE_PROBE_START_OFFSET_CANONICAL,
        throughput_factor=throughput_factor_for_extension_count(gene.extension_count),
        topology_signature_base=gene.key,
        extension_attachments=_extension_attachments_from_generated(gene),
    )


__all__ = [
    "gene_template_from_generated_sample",
    "load_gene_templates_from_json",
    "parse_gene_template_record",
]
