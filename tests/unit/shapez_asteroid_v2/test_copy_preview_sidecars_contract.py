"""Copy-preview sidecars: partial pipeline JSON without full solve or replay input."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.solver import (
    build_copy_preview_v2_sidecars,
)


def test_sidecars_include_full_reconstruction_and_partial_pipeline_meta() -> None:
    decoded: dict = {"BP": {"Entries": []}}
    side = build_copy_preview_v2_sidecars(decoded)
    assert side["mining_layout_engine"] == "v2"
    assert side["pipeline_scope"] == "decode_to_pass1_preview"
    assert side["executed_stage_max"] == "pass1"
    assert side["executed_passes"] == ["decode", "step_0_5", "step_1", "pass1"]
    assert {item["pass"]: item["reason"] for item in side["skipped_passes"]}[
        "pass2"
    ] == "copy_preview_pass1_only"
    assert isinstance(side["reconstruction"], dict)
    assert side["reconstruction"]["mineable_placement_cells"] == []
    assert side["reconstruction"]["extractor_cells"] == []
    assert side["reconstruction"]["extension_cells"] == []

    pp = side["partial_pipeline"]
    assert pp["pipeline_scope"] == "decode_to_pass1_preview"
    assert {item["pass"]: item["reason"] for item in pp["skipped_passes"]}[
        "pass2"
    ] == "copy_preview_pass1_only"
    assert "step_1_reconstruction" in pp["phases_included"]
    assert "step_10_replay_snapshots" in pp["phases_not_included"]
    assert "replay" in pp["note"].lower()

    rs = side["reconstruction_summary"]
    assert rs["mineable_placement_count"] == 0
    assert rs.get("interior_patch_count") == 0
    assert "extractor_cell_count" in rs
    assert "extension_cell_count" in rs

    rt = side["runtime_trace_events"]
    assert isinstance(rt, list)
    assert len(rt) >= 1
    assert "runtime_trace_events_truncated" in side
    assert side["runtime_trace_events_truncated"] is False
