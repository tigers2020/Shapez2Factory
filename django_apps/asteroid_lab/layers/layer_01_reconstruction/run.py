"""Layer 1 facade — delegates to reconstruction/ (no layers import in reconstruction/)."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
    Layer01ReconstructionOutput,
)
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)


def run_layer_01(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> Layer01ReconstructionOutput:
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    capacity_envelope = build_reconstruction_capacity_envelope(complete_map=complete_map)
    return Layer01ReconstructionOutput(
        complete_map=complete_map,
        capacity_envelope=capacity_envelope,
    )
