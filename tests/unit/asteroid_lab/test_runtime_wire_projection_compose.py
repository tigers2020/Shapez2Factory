"""algorithm_rerun_count == 0 on lab replay compose (wire projection)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
from django_apps.asteroid_lab.services.lab_replay_diagnostics import (
    DIAGNOSTIC_MISSING_RUNTIME_WIRES,
    DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN,
)
from shapez2_factory.adapters.asteroid_lab.runtime_wires import (
    MANIFEST_PATH_KEY,
    RUNTIME_WIRES_ARTIFACT_REL_PATH,
    build_runtime_wires_document,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)
from tests.unit.asteroid_lab.test_artifact_replay_viewer_compose import _write_artifact

pytestmark = pytest.mark.django_db

LAYER_RUN_PATCHES = [
    "shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run.execute_layer_02_exterior_transport_plan",
    "shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run.run_layer_03_rim_greedy_placement",
    "shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run.run_layer_04_inner_pattern_fill",
    "shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run.run_layer_05_transport_routing",
]


def _raise_if_called(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("solver layer must not execute during replay compose")


@pytest.fixture
def block_layer_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    for target in LAYER_RUN_PATCHES:
        monkeypatch.setattr(target, _raise_if_called)


def _minimal_l3_result() -> object:
    placement = CommittedRimSeedPlacement(
        placement_id="p-001",
        variant_id="m0e",
        anchor=(3, 3),
        output_dir="E",
        seed_id="m0e",
        miner_cells=frozenset({(3, 3)}),
        extension_cells=frozenset({(4, 3)}),
        m_output_stub=(5, 3),
        throughput_factor=4,
        route_probe_path=((6, 3),),
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        winning_variant_id="m0e",
        metrics=RimGreedyMetrics(
            rim_anchor_count=4,
            route_feasible_rim_anchor_count=4,
            committed_placement_count=1,
            winning_variant_id="m0e",
            pass2_score=4.0,
        ),
    )


def _write_wires_artifact(
    artifact_dir: Path,
    *,
    run_key: str,
    wires_doc: dict[str, object] | None = None,
    include_wires: bool = True,
) -> m.SolverRun:
    complete_map = golden_5x5_complete_map()
    core_lines = [
        {
            "record_type": "frame",
            "frame_index": 0,
            "event": "layer_done",
            "layer_slug": "layer_02_exterior_transport",
            "outcome": "completed",
            "elapsed_ms": 1,
        },
        {
            "record_type": "frame",
            "frame_index": 1,
            "event": "layer_done",
            "layer_slug": "layer_03_rim_greedy_placement",
            "outcome": "completed",
            "elapsed_ms": 2,
        },
    ]
    _write_artifact(
        artifact_dir,
        run_key=run_key,
        core_lines=core_lines,
        complete_map=complete_map,
    )
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    complete_map_hash = manifest["content_hashes"]["output/layer01_complete_map.json"]
    doc = wires_doc or build_runtime_wires_document(
        run_key=run_key,
        written_at_utc="2026-06-10T00:00:00Z",
        complete_map_hash=complete_map_hash,
        transport_summary={
            "requested_resource_kind": "shape",
            "effective_transport_kind": "shape_belt",
        },
        exterior_plan=minimal_l2_plan_for_golden(),
        rim_greedy=_minimal_l3_result(),
    )
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if include_wires:
        wires_path = artifact_dir / RUNTIME_WIRES_ARTIFACT_REL_PATH
        wires_path.parent.mkdir(parents=True, exist_ok=True)
        wires_bytes = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
        wires_path.write_bytes(wires_bytes)
        manifest["paths"][MANIFEST_PATH_KEY] = RUNTIME_WIRES_ARTIFACT_REL_PATH
        manifest["content_hashes"][RUNTIME_WIRES_ARTIFACT_REL_PATH] = hashlib.sha256(
            wires_bytes
        ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    project = m.AsteroidProject.objects.create(name="Wire", slug=f"wire-{run_key}")
    return m.SolverRun.objects.create(
        project=project,
        run_key=run_key,
        artifact_root=str(artifact_dir.resolve()),
        lifecycle_status="succeeded",
    )


@pytest.fixture
def runtime_wire_artifact_fixture(tmp_path: Path) -> m.SolverRun:
    return _write_wires_artifact(tmp_path, run_key="wire-projection-run")


def test_compose_with_valid_wires_never_executes_layers(
    block_layer_execution: None,
    runtime_wire_artifact_fixture: m.SolverRun,
) -> None:
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        compose_lab_replay_frames_from_artifact_run,
    )

    run = runtime_wire_artifact_fixture
    frames = compose_lab_replay_frames_from_artifact_run(run)
    assert frames is not None
    l3_complete = next(
        f for f in frames if f.get("event_type") == EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
    )
    overlay = (l3_complete.get("map_view") or {}).get("overlay_cells") or []
    assert overlay, "L3 complete must carry overlays from wire projection"
    assert l3_complete["inspector"]["replay_source"] == "artifact_runtime_wire_projection"


def test_compose_missing_wires_degrades_without_layer_execution(
    block_layer_execution: None,
    tmp_path: Path,
) -> None:
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        compose_lab_replay_frames_from_artifact_run,
        extract_replay_compose_meta,
    )

    run = _write_wires_artifact(tmp_path, run_key="wire-missing", include_wires=False)
    frames = compose_lab_replay_frames_from_artifact_run(run)
    assert frames is not None
    meta = extract_replay_compose_meta(frames)
    assert meta is not None
    assert meta["diagnostic_reason"] == DIAGNOSTIC_MISSING_RUNTIME_WIRES
    assert meta["algorithm_rerun_count"] == 0


def test_compose_unknown_wire_schema_degrades(
    block_layer_execution: None,
    tmp_path: Path,
) -> None:
    from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
        compose_lab_replay_frames_from_artifact_run,
        extract_replay_compose_meta,
    )

    complete_map = golden_5x5_complete_map()
    _write_artifact(
        tmp_path,
        run_key="wire-bad-schema",
        core_lines=[
            {
                "record_type": "frame",
                "frame_index": 0,
                "event": "layer_done",
                "layer_slug": "layer_02_exterior_transport",
                "outcome": "completed",
                "elapsed_ms": 1,
            }
        ],
        complete_map=complete_map,
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    complete_map_hash = manifest["content_hashes"]["output/layer01_complete_map.json"]
    bad_doc = build_runtime_wires_document(
        run_key="wire-bad-schema",
        written_at_utc="2026-06-10T00:00:00Z",
        complete_map_hash=complete_map_hash,
        transport_summary={
            "requested_resource_kind": "shape",
            "effective_transport_kind": "shape_belt",
        },
        exterior_plan=minimal_l2_plan_for_golden(),
        rim_greedy=_minimal_l3_result(),
    )
    bad_doc["schema_version"] = "solver_runtime_wires_v99"
    wires_path = tmp_path / RUNTIME_WIRES_ARTIFACT_REL_PATH
    wires_path.parent.mkdir(parents=True, exist_ok=True)
    wires_bytes = json.dumps(bad_doc, sort_keys=True, separators=(",", ":")).encode("utf-8")
    wires_path.write_bytes(wires_bytes)
    manifest["paths"][MANIFEST_PATH_KEY] = RUNTIME_WIRES_ARTIFACT_REL_PATH
    manifest["content_hashes"][RUNTIME_WIRES_ARTIFACT_REL_PATH] = hashlib.sha256(
        wires_bytes
    ).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    project = m.AsteroidProject.objects.create(name="Wire", slug="wire-bad-schema")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="wire-bad-schema",
        artifact_root=str(tmp_path.resolve()),
        lifecycle_status="succeeded",
    )
    frames = compose_lab_replay_frames_from_artifact_run(run)
    assert frames is not None
    meta = extract_replay_compose_meta(frames)
    assert meta is not None
    assert meta["diagnostic_reason"] == DIAGNOSTIC_RUNTIME_WIRE_SCHEMA_UNKNOWN
