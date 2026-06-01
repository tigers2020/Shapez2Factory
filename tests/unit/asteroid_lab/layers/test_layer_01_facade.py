"""Layer 1 reconstruction facade."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)


def _canon_cleanup_recon():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return cleanup, recon


@pytest.mark.django_db
def test_run_layer_01_returns_layer01_output(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    cleanup, recon = _canon_cleanup_recon()
    out = run_layer_01(cleanup=cleanup, recon=recon)
    assert out.complete_map is not None
    assert out.capacity_envelope["capacity_basis"] == "terrain_upper_bound"
    assert "by_resource" in out.capacity_envelope
    assert "present_resource_kinds" in out.capacity_envelope
