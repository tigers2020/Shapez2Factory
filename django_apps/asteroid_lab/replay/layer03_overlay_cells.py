"""L3 replay candidate observation overlay projection (output-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.overlay_wire_contract import build_output_hint_overlay_cell
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
)

OVERLAY_KIND_CANDIDATE_MINER = "candidate_miner"
OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB = "candidate_transport_stub"
OVERLAY_KIND_CANDIDATE_ROUTE_PATH = "candidate_route_path"


def overlay_for_probed(entry: RouteProbedBundleCandidate) -> tuple[ReplayOverlayCell, ...]:
    candidate = entry.candidate
    profile_transport = candidate.transport_kind.value
    overlay: list[ReplayOverlayCell] = []
    for x, y in sorted(candidate.mining_occupied_cells):
        overlay.append(
            build_output_hint_overlay_cell(
                x=x,
                y=y,
                kind=OVERLAY_KIND_CANDIDATE_MINER,
                profile_transport_kind=profile_transport,
            )
        )
    for x, y in sorted(candidate.transport_stub_cells):
        overlay.append(
            build_output_hint_overlay_cell(
                x=x,
                y=y,
                kind=OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
                profile_transport_kind=profile_transport,
            )
        )
    if entry.route_probe_result is not None:
        for x, y in entry.route_probe_result.path_coords:
            overlay.append(
                build_output_hint_overlay_cell(
                    x=x,
                    y=y,
                    kind=OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
                    profile_transport_kind=profile_transport,
                )
            )
    return tuple(overlay)


def overlay_cell_count_for_candidate(entry: RouteProbedBundleCandidate) -> int:
    return len(overlay_for_probed(entry))


__all__ = [
    "OVERLAY_KIND_CANDIDATE_MINER",
    "OVERLAY_KIND_CANDIDATE_ROUTE_PATH",
    "OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB",
    "overlay_cell_count_for_candidate",
    "overlay_for_probed",
]
