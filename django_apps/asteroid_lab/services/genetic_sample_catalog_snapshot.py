"""ORM -> GeneticSampleSeedSnapshot payload serializer (adapter boundary; ORM allowed here only).

Serializes ``GeneSeed`` rows into a pure ``genetic_sample_seed_v1`` JSON payload that core
``GeneticSampleSeedSnapshot.from_payload`` can parse.

Priority:
1. ``miner_seed_v2`` canonical rows (18) -> canonical-E templates (D4 expansion stays in L3).
2. Otherwise exhaustive ``gene_key`` rows resolved via the exhaustive generator cache.
3. Empty ``entries`` when neither path yields templates (L3 ``missing_genetic_sample_seeds``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from django.db.models import QuerySet

from django_apps.asteroid_lab.genetic_sample.gene_template import GeneTemplate
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    load_gene_templates_from_gene_seeds,
    queryset_has_miner_seed_v2,
)

SCHEMA_VERSION = "genetic_sample_seed_v1"
SORT_KEY = "by_gene_id_then_throughput_desc"
MINER_SOURCE_BATCH_ID = "miner_seed_v2"


def _entry_from_template(template: GeneTemplate) -> dict[str, object]:
    raw_output_dir = (
        template.output_dir.value
        if hasattr(template.output_dir, "value")
        else str(template.output_dir)
    )
    output_dir = raw_output_dir.upper()
    return {
        "gene_id": template.gene_id,
        "resource_kind": template.resource_kind,
        "canonical_output_dir": output_dir,
        "occupied_offsets": sorted([list(o) for o in template.occupied_offsets]),
        "extractor_offset": list(template.extractor_offset),
        "extension_offsets": [list(o) for o in template.extension_offsets],
        "output_stub_offset": list(template.fixed_output_transport_offset),
        "route_probe_start_offset": list(template.route_probe_start_offset),
        "throughput_factor": int(template.throughput_factor),
        "topology_signature_base": template.topology_signature_base,
    }


def build_genetic_sample_seed_snapshot(
    queryset: QuerySet[GeneSeed],
    *,
    source_batch_id: str = "exhaustive_sample_gene_v1",
) -> dict[str, object]:
    """Build a ``genetic_sample_seed_v1`` payload from a ``GeneSeed`` queryset."""
    templates, _skipped, _errors = load_gene_templates_from_gene_seeds(queryset)
    batch_id = MINER_SOURCE_BATCH_ID if queryset_has_miner_seed_v2(queryset) else source_batch_id
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
        "source_batch_id": batch_id,
        "deterministic_sort_key": SORT_KEY,
        "entries": entries,
    }


__all__ = [
    "MINER_SOURCE_BATCH_ID",
    "SCHEMA_VERSION",
    "SORT_KEY",
    "build_genetic_sample_seed_snapshot",
]
