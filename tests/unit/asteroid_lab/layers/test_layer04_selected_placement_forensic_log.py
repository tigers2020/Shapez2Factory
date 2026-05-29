"""Layer 04 selected-placement forensic JSONL (observability only)."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.stack_result import StackRunResult
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.forensic_log import (
    LAYER04_SELECTED_PLACEMENTS_FILENAME,
    RECORD_TYPE_LAYER04_SELECTED_PLACEMENT,
    build_layer04_selected_placement_record,
    write_layer04_selected_placements_log,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.layers.observability.layer_post_summary_log import (
    LayerPostSummaryLogSession,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_layer04_selected_placement_forensic_log_contains_rotation_and_route_path(
    tmp_path: Path,
) -> None:
    probe = succeeded_probe_at(
        (3, -10),
        output_dir=Direction.N,
        transport=frozenset({(3, -9)}),
        goal=(3, -8),
    )
    placement = build_rim_bundle_placement(probe)
    assert placement.probed_route_path_cells

    path = write_layer04_selected_placements_log(
        run_dir=tmp_path,
        selected_placements=(placement,),
    )
    assert path.name == LAYER04_SELECTED_PLACEMENTS_FILENAME
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["record_type"] == RECORD_TYPE_LAYER04_SELECTED_PLACEMENT
    assert record["anchor_coord"] == {"x": 3, "y": -10}
    assert record["cell_placements"][0]["rotation"] == 3
    assert record["probed_route_path_cells"]
    assert {"x": 3, "y": -9} in record["probed_route_path_cells"]


def test_build_layer04_selected_placement_record_sorts_cells_deterministically() -> None:
    probe = succeeded_probe_at((3, -10), output_dir=Direction.N)
    placement = build_rim_bundle_placement(probe)
    record = build_layer04_selected_placement_record(placement)
    extractor = record["extractor_cells"]
    assert extractor == sorted(extractor, key=lambda c: (c["x"], c["y"]))


def test_write_layer04_selected_placements_log_orders_by_candidate_id(tmp_path: Path) -> None:
    p_b = build_rim_bundle_placement(
        succeeded_probe_at((5, 0), equivalence_key="eq_b", gene_key="seed_b"),
    )
    p_a = build_rim_bundle_placement(
        succeeded_probe_at((3, 0), equivalence_key="eq_a", gene_key="seed_a"),
    )
    path = write_layer04_selected_placements_log(
        run_dir=tmp_path,
        selected_placements=(p_b, p_a),
    )
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["candidate_id"] <= second["candidate_id"]


def test_manifest_lists_layer04_forensic_artifact(tmp_path: Path) -> None:
    placement = build_rim_bundle_placement(succeeded_probe_at((3, -10), output_dir=Direction.N))
    write_layer04_selected_placements_log(
        run_dir=tmp_path,
        selected_placements=(placement,),
    )
    session = LayerPostSummaryLogSession(
        run_id="forensic-manifest",
        run_dir=tmp_path,
        project_slug="demo",
    )
    session.close(
        StackRunResult(
            status=StackRunStatus.SUCCESS,
            completed_layer_slugs=("layer_04_rim_bundle_placement",),
            failed_layer_slug=None,
            diagnostic_snapshot=None,
        )
    )
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    artifact_name = manifest["artifacts"]["layer04_selected_placements"]
    assert artifact_name == LAYER04_SELECTED_PLACEMENTS_FILENAME
