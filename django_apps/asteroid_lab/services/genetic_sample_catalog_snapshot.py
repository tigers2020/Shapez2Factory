"""ORM -> GeneCatalogSnapshot payload serializer (adapter boundary; ORM allowed here only).

Serializes ``GeneticSample`` rows into a pure ``gene_catalog_v1`` JSON payload that core
``GeneCatalogSnapshot.from_payload`` can parse. Resolution currently flows through
``load_gene_templates_from_genetic_samples``, which only resolves ``gene_key``s present in the
exhaustive generator cache; ``miner_seed_*`` rows are skipped today. Including miner-seed genes in
the catalog is a future extension and is intentionally NOT implemented here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from django.db.models import QuerySet

from django_apps.asteroid_lab.genetic_sample.gene_template import GeneTemplate
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    load_gene_templates_from_genetic_samples,
)

SCHEMA_VERSION = "gene_catalog_v1"
SORT_KEY = "by_gene_id_then_throughput_desc"


def _entry_from_template(template: GeneTemplate) -> dict[str, Any]:
    raw_output_dir = (
        template.output_dir.value
        if hasattr(template.output_dir, "value")
        else str(template.output_dir)
    )
    # Core schema requires canonical "E"; the Direction StrEnum stores lowercase "e".
    output_dir = raw_output_dir.upper()
    return {
        "gene_id": template.gene_id,
        "resource_kind": "both",
        "canonical_output_dir": output_dir,
        "occupied_offsets": sorted([list(o) for o in template.occupied_offsets]),
        "extractor_offset": list(template.extractor_offset),
        "extension_offsets": [list(o) for o in template.extension_offsets],
        "output_stub_offset": list(template.fixed_output_transport_offset),
        "route_probe_start_offset": list(template.route_probe_start_offset),
        "throughput_factor": int(template.throughput_factor),
        "topology_signature_base": template.topology_signature_base,
    }


def build_gene_catalog_snapshot(
    queryset: QuerySet[GeneticSample],
    *,
    source_batch_id: str = "exhaustive_sample_gene_v1",
) -> dict[str, Any]:
    """Build a ``gene_catalog_v1`` payload from a ``GeneticSample`` queryset.

    Entries are sorted by ``(gene_id, -throughput_factor)`` (the ``deterministic_sort_key``).
    """
    templates, _skipped, _errors = load_gene_templates_from_genetic_samples(queryset)
    entries = sorted(
        (_entry_from_template(t) for t in templates),
        key=lambda e: (e["gene_id"], -e["throughput_factor"]),
    )
    provenance_hash = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "provenance_hash": provenance_hash,
        "source_batch_id": source_batch_id,
        "deterministic_sort_key": SORT_KEY,
        "entries": entries,
    }


__all__ = ["SCHEMA_VERSION", "SORT_KEY", "build_gene_catalog_snapshot"]
