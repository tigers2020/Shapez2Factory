"""v2 copy-preview behavior artifact (output-only JSON file)."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import RequestFactory, override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization import (
    public_artifacts,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.solver import (
    build_copy_preview_v2_sidecars,
)
from django_apps.shapez_asteroid.services.behavior_artifact_collector import (
    BehaviorArtifactCollector,
    build_decode_failure_behavior_document,
)
from django_apps.shapez_asteroid.services.v2_behavior_artifact_dump import (
    dump_v2_behavior_artifact_json,
    input_digest_prefix_from_code,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy_trace


def _minimal_valid_copy_code() -> str:
    root = {"BP": {"Entries": [{"X": 2, "Y": 2, "T": "Layout_ShapeMiner"}]}}
    raw = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw)
    b64 = base64.b64encode(gz).decode("ascii").rstrip("=")
    return "SHAPEZ2-4-" + b64


def _encode_decoded(doc: dict) -> str:
    raw = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw)
    b64 = base64.b64encode(gz).decode("ascii").rstrip("=")
    return "SHAPEZ2-4-" + b64


def _assert_required_schema(doc: dict) -> None:
    assert doc["schema_version"] == public_artifacts.COPY_PREVIEW_BEHAVIOR_SCHEMA_VERSION
    assert doc["artifact_kind"] == "copy_preview_behavior"
    assert doc["algorithm_input"] is False
    assert doc["http_response_included"] is False
    assert doc["includes_mining_map"] is False
    assert doc["includes_full_pass1_events"] is True
    assert doc["pass1_replay_events_truncated"] is False
    assert doc["pass1_replay_event_count"] == len(doc["pass1_replay_events"])
    assert doc["runtime_trace_events_truncated"] is False
    assert doc["runtime_trace_event_count"] == len(doc["runtime_trace_events"])
    # Raw copy string must not appear outside decode_trace (steps may mention the prefix).
    sans_decode = {k: v for k, v in doc.items() if k != "decode_trace"}
    assert "SHAPEZ2-4-" not in json.dumps(sans_decode)


def test_dump_skipped_when_dir_empty(tmp_path: Path) -> None:
    code = _minimal_valid_copy_code()
    trace = decode_shapez2_copy_trace(code)
    assert trace.success and trace.data is not None
    collector = BehaviorArtifactCollector(input_digest_prefix=input_digest_prefix_from_code(code))
    collector.record_decode_trace(trace)
    build_copy_preview_v2_sidecars(trace.data, behavior_artifact=collector)
    dump_v2_behavior_artifact_json(collector.build_document(), "")
    assert list(tmp_path.iterdir()) == []


def test_artifact_contains_preview_meta_and_pass1_events(tmp_path: Path) -> None:
    code = _minimal_valid_copy_code()
    collector = BehaviorArtifactCollector(input_digest_prefix=input_digest_prefix_from_code(code))
    trace = decode_shapez2_copy_trace(code)
    assert trace.success and trace.data is not None
    collector.record_decode_trace(trace)
    build_copy_preview_v2_sidecars(trace.data, behavior_artifact=collector)
    doc = collector.build_document()
    _assert_required_schema(doc)
    assert doc["runtime_trace_event_count"] >= 8
    kinds = [e.get("event_type") for e in doc["runtime_trace_events"]]
    assert kinds.count("phase_started") == 4
    assert kinds.count("phase_finished") == 4
    for row in doc["preview_frames"]:
        assert "mining_map" not in row
        assert "id" in row
        assert "summary" in row
    assert isinstance(doc["pass1_replay_events"], list)
    dump_v2_behavior_artifact_json(doc, tmp_path)
    written = list(tmp_path.glob("v2_behavior_artifact_*_behavior_artifact.json"))
    assert len(written) == 1


def test_extension_only_sidecar_mineable_count_matches_extensions() -> None:
    """Copy-preview summary: extension-only BP must keep mineable_placement_count > 0."""

    n = 25
    decoded = {
        "BP": {
            "Entries": [
                {"X": 400 + i, "Y": 50, "T": "Layout_ShapeMinerExtension"} for i in range(n)
            ]
        }
    }
    side = build_copy_preview_v2_sidecars(decoded)
    rs = side["reconstruction_summary"]
    assert rs["extraction_shell_count"] == 0
    assert rs["extension_cell_count"] == n
    assert rs["mineable_placement_count"] == n


def test_diagnose_not_called_extension_only_mineable_restored() -> None:
    """Regression: extensions without shell must still yield mineable (no empty diagnosis)."""

    entries = [{"X": 30 + i, "Y": 40, "T": "Layout_ShapeMinerExtension"} for i in range(5)]
    decoded = {"BP": {"Entries": entries}}
    code = _encode_decoded(decoded)
    trace = decode_shapez2_copy_trace(code)
    assert trace.success
    collector = BehaviorArtifactCollector(input_digest_prefix=input_digest_prefix_from_code(code))
    collector.record_decode_trace(trace)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization.dto_adapters._recon_diag.diagnose_reconstruction_mineable_empty",  # noqa: E501
    ) as mock_diag:
        build_copy_preview_v2_sidecars(decoded, behavior_artifact=collector)
    mock_diag.assert_not_called()


def test_diagnose_not_called_when_mineable_nonempty() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    decoded = {"BP": {"Entries": entries}}
    code = _encode_decoded(decoded)
    trace = decode_shapez2_copy_trace(code)
    assert trace.success
    collector = BehaviorArtifactCollector(input_digest_prefix=input_digest_prefix_from_code(code))
    collector.record_decode_trace(trace)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization.dto_adapters._recon_diag.diagnose_reconstruction_mineable_empty",  # noqa: E501
    ) as mock_diag:
        build_copy_preview_v2_sidecars(decoded, behavior_artifact=collector)
    mock_diag.assert_not_called()


def test_diagnosis_error_swallowed(tmp_path: Path) -> None:
    code = _minimal_valid_copy_code()
    collector = BehaviorArtifactCollector(input_digest_prefix=input_digest_prefix_from_code(code))
    trace = decode_shapez2_copy_trace(code)
    assert trace.data is not None
    collector.record_decode_trace(trace)
    empty_mineable_recon = ReconstructionDTO(
        full_barrier_cells=((2, 2), (3, 2)),
        extraction_shell_cells=((2, 2), (3, 2)),
        mineable_placement_cells=(),
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization.dto_adapters._recon_diag.diagnose_reconstruction_mineable_empty",  # noqa: E501
        side_effect=RuntimeError("boom"),
    ):
        collector.record_copy_preview_pipeline(
            existing_layout_analysis={"existing_layout_source_kind": "x"},
            reconstruction={"mineable_placement_cells": []},
            reconstruction_summary={"mineable_placement_count": 0},
            preview_frames=[{"id": "f", "summary": {"entry_count": 0}}],
            pass1_replay_events=[],
            decoded_for_diagnosis=trace.data,
            reconstruction_dto=empty_mineable_recon,
            partial_pipeline={"phases_included": []},
            preview_schema_version=2,
        )
    doc = collector.build_document()
    assert doc["step_1_diagnosis"] is None
    assert doc["step_1_diagnosis_error"] is not None
    assert "RuntimeError" in doc["step_1_diagnosis_error"]
    dump_v2_behavior_artifact_json(doc, tmp_path)


def test_pass1_runs_once_per_preview_build(monkeypatch: pytest.MonkeyPatch) -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
        pass1_outer as po,
    )

    calls = {"n": 0}
    orig = po.run_pass1_outer_placement

    def _wrap(*a: object, **k: object) -> object:
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(pv, "run_pass1_outer_placement", _wrap)
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    decoded = {"BP": {"Entries": entries}}
    build_copy_preview_v2_sidecars(decoded)
    assert calls["n"] == 1


def test_build_sidecars_keys_unchanged_with_collector() -> None:
    decoded: dict = {"BP": {"Entries": []}}
    baseline = build_copy_preview_v2_sidecars(decoded)
    c = BehaviorArtifactCollector(input_digest_prefix="0" * 16)
    c.record_decode_trace(decode_shapez2_copy_trace(_minimal_valid_copy_code()))
    with_collector = build_copy_preview_v2_sidecars(decoded, behavior_artifact=c)
    assert set(baseline.keys()) == set(with_collector.keys())


@pytest.mark.django_db
def test_copy_preview_view_response_excludes_artifact(tmp_path: Path) -> None:
    from django_apps.shapez_asteroid import views as asteroid_views

    code = _minimal_valid_copy_code()
    rf = RequestFactory()
    body = json.dumps({"code": code})
    copy_debug = tmp_path / "copy_debug"
    with override_settings(BASE_DIR=tmp_path, SHAPEZ_COPY_DEBUG_DIR=str(copy_debug)):
        req = rf.post(
            "/api/asteroid/copy-preview/",
            data=body,
            content_type="application/json",
        )
        resp = asteroid_views.copy_preview(req)
    data = json.loads(resp.content.decode("utf-8"))
    assert data.get("ok") is True
    assert "schema_version" not in data
    assert "pass1_replay_events" not in data
    assert "algorithm_input" not in data
    ba_dir = tmp_path / "var" / "behavior_artifact"
    arts = list(ba_dir.glob("v2_behavior_artifact_*_behavior_artifact.json"))
    assert len(arts) == 1
    loaded = json.loads(arts[0].read_text(encoding="utf-8"))
    _assert_required_schema(loaded)


def test_decode_failure_artifact_minimal(tmp_path: Path) -> None:
    trace = decode_shapez2_copy_trace("not-a-valid-copy")
    doc = build_decode_failure_behavior_document(
        trace=trace,
        input_digest_prefix="deadbeef" * 2,
    )
    _assert_required_schema(doc)
    assert doc["decode_trace"]["success"] is False
    dump_v2_behavior_artifact_json(doc, tmp_path)
    assert list(tmp_path.glob("v2_behavior_artifact_*_behavior_artifact.json"))
