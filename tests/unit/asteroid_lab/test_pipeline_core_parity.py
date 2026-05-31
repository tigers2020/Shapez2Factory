"""PR-CLI-2f Step 2 (tests-first) — core decode/cleanup/reconstruction parity with the Django path.

Oracle: the existing Django pipeline (``decode_shapez_copy_string`` → ``deconstruct_snapshot`` →
``run_topology_reconstruction``) on a recorded reconstruction fixture line. The relocated **core**
pipeline must produce value-identical ``DecodedBlueprintSnapshotDTO`` / ``CleanupResult`` /
``ReconstructionResult`` (these DTOs already live in core, so ``==`` compares by value across paths).

RED until PR-CLI-2f Step 4: the core modules do not exist yet, so the in-test core import raises.
"""

from __future__ import annotations

import importlib

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot as dj_deconstruct
from django_apps.asteroid_lab.reconstruction.pipeline import (
    run_topology_reconstruction as dj_run_topology,
)
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string as dj_decode,
    load_reconstruction_fixture_line_pairs,
)


def _first_required_copy_string() -> str:
    pairs = load_reconstruction_fixture_line_pairs()
    assert pairs, "no reconstruction fixture lines available"
    return pairs[0][0]


def _import_core():
    try:
        copy_decode_topology = importlib.import_module(
            "shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract"
        )
        cleanup_pipeline = importlib.import_module(
            "shapez2_factory.domain.asteroid_lab.cleanup.pipeline"
        )
        recon_pipeline = importlib.import_module(
            "shapez2_factory.domain.asteroid_lab.reconstruction.pipeline"
        )
    except ModuleNotFoundError as exc:  # pragma: no cover - RED until Step 4 relocation
        pytest.fail(f"core pipeline not relocated yet (PR-CLI-2f Step 4): {exc}")
    return (
        copy_decode_topology.decode_shapez_copy_string,
        cleanup_pipeline.deconstruct_snapshot,
        recon_pipeline.run_topology_reconstruction,
    )


def test_core_pipeline_matches_django_path() -> None:
    copy_string = _first_required_copy_string()
    core_decode, core_deconstruct, core_run_topology = _import_core()

    dj_snap = dj_decode(copy_string)
    core_snap = core_decode(copy_string)
    assert core_snap == dj_snap, "decode/normalize/snapshot parity broken"

    dj_cleanup = dj_deconstruct(dj_snap)
    core_cleanup = core_deconstruct(core_snap)
    assert core_cleanup == dj_cleanup, "cleanup parity broken"

    dj_recon = dj_run_topology(dj_cleanup)
    core_recon = core_run_topology(core_cleanup)
    assert core_recon == dj_recon, "reconstruction parity broken"
