"""Convert ``miner_seed_v2`` ``GeneSeed`` rows to canonical-E ``GeneTemplate`` (no D4 expansion)."""

from __future__ import annotations

import logging
from enum import StrEnum

from django_apps.asteroid_lab.genetic_sample.gene_template import (
    CANONICAL_EXTRACTOR_OFFSET,
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
    CANONICAL_OUTPUT_DIR,
    CANONICAL_ROUTE_PROBE_START_OFFSET,
    GeneTemplate,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    MINER_SEED_SCHEMA_V2,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_equivalence import (
    MinerSeedLayoutValidationError,
    assert_miner_seed_layout_strict,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_parent_tree import (
    equipment_nodes,
    parent_edges_bfs,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    topology_signature_from_decoded_root,
)
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

logger = logging.getLogger(__name__)

_VALID_RESOURCE_KINDS = frozenset({"shape", "fluid", "both"})


class MinerGeneSeedTemplateErrorCode(StrEnum):
    NOT_MINER_SEED = "not_miner_seed"
    MISSING_DECODED_JSON = "missing_decoded_json"
    INVALID_LAYOUT = "invalid_layout"
    INVALID_THROUGHPUT = "invalid_throughput"


def is_miner_seed_v2(seed: GeneSeed) -> bool:
    gene_key = str(seed.gene_key or "")
    if not gene_key.startswith("miner_seed_"):
        return False
    meta = seed.metadata_json if isinstance(seed.metadata_json, dict) else {}
    return meta.get("schema") == MINER_SEED_SCHEMA_V2 and meta.get("is_seed") is True


def _rel_offset(origin: tuple[int, int], xy: tuple[int, int]) -> Coord:
    ox, oy = origin
    return (xy[0] - ox, xy[1] - oy)


def _resource_kind_from_metadata(meta: dict[str, object]) -> str:
    stored = meta.get("resource_kind_stored", "shape")
    if stored == "shape":
        return "shape"
    if stored == "fluid":
        return "fluid"
    if stored in _VALID_RESOURCE_KINDS:
        return str(stored)
    return "shape"


def gene_template_from_miner_gene_seed(
    seed: GeneSeed,
) -> tuple[GeneTemplate | None, MinerGeneSeedTemplateErrorCode | None]:
    """Map island-local miner paste (miner R=0, belt east) to canonical-E ``GeneTemplate``."""

    if not is_miner_seed_v2(seed):
        return None, MinerGeneSeedTemplateErrorCode.NOT_MINER_SEED

    gene_key = str(seed.gene_key or "")
    root = seed.decoded_json if isinstance(seed.decoded_json, dict) else {}
    if not root:
        return None, MinerGeneSeedTemplateErrorCode.MISSING_DECODED_JSON

    try:
        assert_miner_seed_layout_strict(root)
        miner_xy, nodes = equipment_nodes(root)
    except (MinerSeedLayoutValidationError, ValueError) as exc:
        logger.debug("miner seed layout invalid for %r: %s", gene_key, exc)
        return None, MinerGeneSeedTemplateErrorCode.INVALID_LAYOUT

    extension_offsets = tuple(
        sorted(
            (_rel_offset(miner_xy, xy) for xy in nodes if xy != miner_xy),
            key=lambda c: (c[0], c[1]),
        )
    )
    occupied_offsets = frozenset({CANONICAL_EXTRACTOR_OFFSET, *extension_offsets})

    meta = seed.metadata_json if isinstance(seed.metadata_json, dict) else {}
    ext_count = count_extensions(root)
    throughput = meta.get("throughput_factor")
    if throughput is None:
        throughput = throughput_factor_for_extension_count(ext_count)
    if not isinstance(throughput, int) or throughput not in {4, 8, 12, 16}:
        return None, MinerGeneSeedTemplateErrorCode.INVALID_THROUGHPUT

    topology = meta.get("topology_signature")
    if not isinstance(topology, str) or not topology:
        topology = topology_signature_from_decoded_root(root)

    edge_list = parent_edges_bfs(miner_xy, nodes)
    extension_attachments = ()
    _ = edge_list  # parent tree validated; attachments not required for L3 snapshot

    return (
        GeneTemplate(
            gene_id=gene_key,
            name=str(seed.name or gene_key),
            occupied_offsets=occupied_offsets,
            extractor_offset=CANONICAL_EXTRACTOR_OFFSET,
            extension_offsets=extension_offsets,
            output_dir=CANONICAL_OUTPUT_DIR,
            fixed_output_transport_offset=CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
            route_probe_start_offset=CANONICAL_ROUTE_PROBE_START_OFFSET,
            throughput_factor=throughput,
            topology_signature_base=topology,
            extension_attachments=extension_attachments,
            resource_kind=_resource_kind_from_metadata(meta),
        ),
        None,
    )


__all__ = [
    "MinerGeneSeedTemplateErrorCode",
    "gene_template_from_miner_gene_seed",
    "is_miner_seed_v2",
]
