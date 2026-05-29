"""Semantic equivalence keys for rim bundle dedupe (gene_key excluded)."""

from __future__ import annotations

import hashlib
import json

from django_apps.asteroid_lab.layers.contracts.candidates import BundleCandidate
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def build_equivalence_key(
    *,
    transport_kind: TransportKind,
    resource_kind: ResourceKind,
    output_dir: str,
    throughput_factor: int,
    route_probe_start_coord: Coord,
    mining_occupied_cells: frozenset[Coord],
    transport_stub_cells: frozenset[Coord],
    topology_signature: str,
) -> str:
    payload = {
        "transport_kind": transport_kind.value,
        "resource_kind": resource_kind.value,
        "output_dir": output_dir,
        "throughput_factor": throughput_factor,
        "route_probe_start_coord": list(route_probe_start_coord),
        "mining_occupied_cells": sorted(mining_occupied_cells),
        "transport_stub_cells": sorted(transport_stub_cells),
        "topology_signature": topology_signature,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_equivalence_key_from_candidate(candidate: BundleCandidate) -> str:
    return build_equivalence_key(
        transport_kind=candidate.transport_kind,
        resource_kind=candidate.resource_kind,
        output_dir=candidate.output_dir.value,
        throughput_factor=candidate.throughput_factor,
        route_probe_start_coord=candidate.route_probe_start_coord,
        mining_occupied_cells=candidate.mining_occupied_cells,
        transport_stub_cells=candidate.transport_stub_cells,
        topology_signature=candidate.topology_signature,
    )


__all__ = ["build_equivalence_key", "build_equivalence_key_from_candidate"]
