"""Slice 7: public behavior artifact JSON keys and serialization layering (no key churn)."""

from __future__ import annotations

import json
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    reconstruct_asteroid_mining_field,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization import (
    build_decode_failure_behavior_document,
    dto_adapters,
    existing_layout_analysis_to_json,
    public_artifacts,
    to_jsonable,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.solver import (
    build_copy_preview_v2_sidecars,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy_trace


def test_preview_json_compatibility_surface_still_exports_to_jsonable() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import preview_json

    assert preview_json.to_jsonable is to_jsonable


def test_assemble_and_decode_failure_match_required_top_level_keys() -> None:
    trace = decode_shapez2_copy_trace("x")
    fail_doc = build_decode_failure_behavior_document(
        trace=trace,
        input_digest_prefix="ab" * 16,
    )
    assert set(fail_doc) == public_artifacts.COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS
    assert fail_doc["schema_version"] == public_artifacts.COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION
    assert fail_doc["algorithm_input"] is False

    ok_doc = dto_adapters.assemble_copy_preview_behavior_document(
        input_digest_prefix="cd" * 16,
        decode_trace={"steps": [], "success": True, "error": None},
        step_0_5={"existing_layout_x": 1},
        step_1={"mineable_placement_cells": []},
        step_1_diagnosis=None,
        step_1_diagnosis_error=None,
        preview_frames_thin=[{"id": "a", "summary": {"entry_count": 0}}],
        pass1_replay_events=[{"kind": "noop"}],
        partial_pipeline={"phases_included": []},
        preview_schema_version=2,
        reconstruction_summary={"mineable_placement_count": 0},
    )
    assert set(ok_doc) == public_artifacts.COPY_PREVIEW_BEHAVIOR_DOCUMENT_REQUIRED_KEYS
    json.dumps(fail_doc)
    json.dumps(ok_doc)


def test_existing_layout_analysis_public_keys_keep_prefix() -> None:
    decoded: dict[str, Any] = {"BP": {"Entries": []}}
    analysis = analyze_decoded_layout(decoded)
    blob = existing_layout_analysis_to_json(analysis)
    assert blob
    assert all(k.startswith("existing_layout_") for k in blob)


def test_preview_thin_summaries_match_full_timeline_for_recon_frames() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    side = build_copy_preview_v2_sidecars(decoded)
    frames = side["v2_preview_map_timeline"]
    inner_full = next(f for f in frames if f["id"] == "v2_recon_inner_patch")
    mine_full = next(f for f in frames if f["id"] == "v2_recon_mineable")
    thin = dto_adapters.preview_frames_thin_for_behavior_artifact(frames)
    inner_thin = next(f for f in thin if f["id"] == "v2_recon_inner_patch")
    mine_thin = next(f for f in thin if f["id"] == "v2_recon_mineable")
    assert inner_thin["summary"] == inner_full["summary"]
    assert mine_thin["summary"] == mine_full["summary"]
    inferred_n = sum(1 for r in inner_full["mining_map"] if r.get("role") == "inferred")
    assert inferred_n == len(recon.interior_patch_cells)
    phased = sum(1 for r in mine_full["mining_map"] if r.get("phase") == "v2_recon_mineable")
    assert phased == len(recon.mineable_placement_cells)


def test_build_sidecars_reconstruction_json_matches_reconstruction_dto_counts() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    side = build_copy_preview_v2_sidecars(decoded)
    rj = side["reconstruction"]
    assert len(rj["interior_patch_cells"]) == len(recon.interior_patch_cells)
    assert len(rj["mineable_placement_cells"]) == len(recon.mineable_placement_cells)
