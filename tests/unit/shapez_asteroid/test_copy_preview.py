from __future__ import annotations

import base64
import gzip
import json
import time
from unittest.mock import patch

from django.test import Client, override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_REPLAY_CONTRACT_VERSION,
)
from django_apps.shapez_asteroid.services.copy_preview_debug_dump import (
    _COPY_PREVIEW_DEBUG_MAX_STEMS,
    dump_copy_preview_debug,
)
from django_apps.shapez_asteroid.services.style_classifier import asteroid_map_style_catalog
from django_apps.shapez_core.services.shapez_copy_decode import SHAPEZ2_COPY_PREFIX_V4


def _encode_copy(obj: object) -> str:
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(body)
    b64 = base64.b64encode(compressed).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


def _post_json(client: Client, payload: dict, *, query: str = "") -> object:
    token = client.cookies.get("csrftoken")
    assert token is not None
    path = "/api/asteroid/copy-preview/"
    if query:
        path = f"{path}?{query.lstrip('?')}"
    return client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token.value,
    )


def test_copy_preview_success() -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    summary = body["summary"]
    assert summary["entry_count"] == 1
    assert summary["x_min"] == 1
    assert summary["x_max"] == 1
    assert summary["y_min"] == 2
    assert summary["y_max"] == 2
    assert "p4_reclaim_route_zone_excluded_cumulative_count" not in summary
    assert "p4_reclaim_last_commit_route_cells" not in summary
    assert "p4_reclaim_last_soft_protected_candidate_cells" not in summary
    assert body["mining_map"] == [
        {
            "x": 1,
            "y": 2,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "asteroid_field",
            "source_layout_kind": "miner",
        },
    ]
    assert body["style_catalog"] == asteroid_map_style_catalog()
    assert "occupied" in body["style_catalog"]
    assert "inferred" in body["style_catalog"]
    assert "belt" in body["style_catalog"]
    assert "pipe" in body["style_catalog"]
    assert "miner" in body["style_catalog"]
    assert "extractor" in body["style_catalog"]
    assert "asteroid_field" in body["style_catalog"]
    assert body["map_timeline"][-1]["mining_map"] == body["mining_map"]
    assert "decode_steps" not in body
    assert body["existing_layout_analysis"]["source_kind"] == "raw_asteroid_field"
    s0 = body["map_timeline"][0]["summary"]
    assert "p4_reclaim_route_zone_excluded_cumulative_count" not in s0
    assert "p4_reclaim_last_commit_route_cells" not in s0
    assert "p4_reclaim_last_soft_protected_candidate_cells" not in s0


def test_copy_preview_map_timeline_first_step_shows_transport() -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 5, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 6, "Y": 1, "T": "Layout_UndergroundBelt"},
                {"X": 7, "Y": 1, "T": "Layout_FluidPipe"},
            ],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)})
    assert response.status_code == 200
    body = response.json()
    first = body["map_timeline"][0]
    assert first["id"] == "with_transport"
    by_xy = {(c["x"], c["y"]): c["role"] for c in first["mining_map"]}
    assert by_xy[(6, 1)] == "belt"
    assert by_xy[(7, 1)] == "pipe"
    assert by_xy[(5, 1)] == "occupied"
    ela = body["existing_layout_analysis"]
    assert ela["source_kind"] == "existing_shape_layout"
    assert ela["transport_by_kind"] is not None
    assert "shape_belt" in ela["transport_by_kind"]
    assert "fluid_pipe" in ela["transport_by_kind"]
    for step in body["map_timeline"]:
        s = step["summary"]
        assert "p4_reclaim_last_commit_route_cells" not in s


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_skips_solver_overlay_by_default(mock_solver: object) -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)})
    assert response.status_code == 200
    mock_solver.assert_not_called()


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_includes_solver_overlay_when_enabled(mock_solver: object) -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline as real_build,
    )

    mock_solver.side_effect = real_build

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_overlay=1")
    assert response.status_code == 200
    mock_solver.assert_called_once()
    body = response.json()
    summary = body["summary"]
    assert summary.get("p4_reclaim_route_zone_excluded_cumulative_count") == 0
    assert summary.get("p4_reclaim_last_commit_route_cells") == []
    assert summary.get("p4_reclaim_last_soft_protected_candidate_cells") == []
    s0 = body["map_timeline"][0]["summary"]
    assert "p4_reclaim_route_zone_excluded_cumulative_count" in s0
    assert isinstance(s0["p4_reclaim_last_commit_route_cells"], list)


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_includes_solver_replay_when_flag(mock_solver: object) -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline as real_build,
    )

    mock_solver.side_effect = real_build

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 200
    mock_solver.assert_called_once()
    body = response.json()
    assert "solver_replay" in body
    assert body["solver_replay"]["contract_version"] == SOLVER_REPLAY_CONTRACT_VERSION
    assert isinstance(body["solver_replay"]["events"], list)
    assert "solver_timeline" in body
    assert isinstance(body["solver_timeline"], list)
    assert len(body["solver_timeline"]) >= 1
    assert isinstance(body["solver_replay"].get("ui_frames"), list)
    assert len(body["solver_replay"]["ui_frames"]) == len(body["solver_timeline"])
    s0 = body["map_timeline"][0]["summary"]
    assert "p4_reclaim_route_zone_excluded_cumulative_count" not in s0


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_solver_replay_one_ui_row_per_timeline_frame(mock_solver: object) -> None:
    """STEP10 UI는 ``solver_timeline`` 행당 ``ui_frames`` 한 줄(길이 일치); 이벤트 개수는 별도."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        SOLVER_FRAME_INIT,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline as real_build,
    )

    mock_solver.side_effect = real_build

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 200
    body = response.json()
    tl = body["solver_timeline"]
    ui = body["solver_replay"]["ui_frames"]
    ev = body["solver_replay"]["events"]
    assert len(ui) == len(tl) >= 1
    assert tl[0].get("id") == SOLVER_FRAME_INIT
    assert isinstance(ev, list)


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_solver_timeline_mining_map_roles_sane(mock_solver: object) -> None:
    """``mining_map`` 셀 ``role``은 허용 집합만 사용한다.

    미커밋 probe가 belt로 섞이는 회귀 방지.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline as real_build,
    )

    mock_solver.side_effect = real_build

    allowed = frozenset({None, "", "occupied", "belt", "pipe", "blocked"})
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 200
    body = response.json()
    for frame in body["solver_timeline"]:
        assert isinstance(frame, dict)
        for cell in frame.get("mining_map") or []:
            assert isinstance(cell, dict)
            role = cell.get("role")
            assert role in allowed, f"unexpected role {role!r} in frame {frame.get('id')}"


def test_copy_preview_unknown_t_zero_extraction() -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 2, "T": "t"}]},
    }
    response = _post_json(client, {"code": _encode_copy(data)})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["summary"]["entry_count"] == 0
    assert body["mining_map"] == []
    assert "style_catalog" in body


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_merges_final_validation_optimization_into_last_summary(
    mock_solver: object,
) -> None:
    def fake(_decoded: dict) -> dict:
        return {
            "solver_timeline": [],
            "final_validation": {
                "optimization_final_internal_transport_count": 38,
                "optimization_counterfactual_internal_transport_sequential_v1": 32,
                "optimization_internal_transport_quality_ratio": 1.1875,
                "optimization_counterfactual_aggregation": "sequential_trunk_v1",
                "optimization_counterfactual_failure_reason": None,
                "optimization_warnings": [],
                "solver_quality_tier": "SUCCESS_VALID_WITH_OPTIMIZATION_WARNING",
                "solver_result_tier": "SUCCESS_VALID_WITH_OPTIMIZATION_WARNING",
                "solver_quality_summary": "Valid layout, optimization warning",
                "optimization_warning_count": 1,
            },
            "solver_summary": {
                "routing_state": {
                    "hard_protected_corridors": [[1, 2]],
                    "soft_protected_corridors": [[3, 4]],
                },
            },
        }

    mock_solver.side_effect = fake

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 200
    mock_solver.assert_called_once()
    body = response.json()
    summ = body["summary"]
    assert summ.get("optimization_final_internal_transport_count") == 38
    assert summ.get("optimization_counterfactual_internal_transport_sequential_v1") == 32
    assert summ.get("optimization_internal_transport_quality_ratio") == 1.1875
    assert summ.get("optimization_counterfactual_aggregation") == "sequential_trunk_v1"
    assert summ.get("solver_quality_tier") == "SUCCESS_VALID_WITH_OPTIMIZATION_WARNING"
    assert summ.get("solver_quality_summary") == "Valid layout, optimization warning"
    assert summ.get("optimization_warning_count") == 1
    assert "optimization_internal_transport_quality_ratio" not in body["map_timeline"][0]["summary"]
    assert body["summary"].get("replay_protected_corridor_counts") == {
        "hard": 1,
        "soft": 1,
        "candidate": 0,
    }


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_merges_solver_summary_ui_fields_and_runtime_flags(
    mock_solver: object,
) -> None:
    def fake(_decoded: dict) -> dict:
        return {
            "solver_timeline": [],
            "final_validation": {
                "optimization_warnings": [],
                "solver_quality_tier": "PARTIAL_SUCCESS_VALID_PRESERVE_LOSS",
                "solver_result_tier": "PARTIAL_SUCCESS_VALID_PRESERVE_LOSS",
                "solver_quality_summary": "Valid layout, preserve or routing degradation",
            },
            "solver_summary": {
                "routing_state": None,
                "step4_committed": False,
                "step4_partial_failure": True,
                "pass3_skipped": True,
                "pass3_skip_reason": "step4_not_committed",
                "p4_reclaim_shadow_skip_reason": "pass3_not_eligible",
                "preserve_quality_score": 0.612,
                "transport_connected": True,
                "pass12_stub_route_recovery_enabled": False,
                "pass12_stub_route_recovery_eligible_count": 13,
                "step4_no_route_exhausted_breakdown": {
                    "count": 2,
                    "dominant_blocker_category": "trunk_union_goals_unreachable_from_stub",
                    "sample_rows": [{"placement_id": "p1"}],
                },
            },
        }

    mock_solver.side_effect = fake

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 200
    body = response.json()
    summ = body["summary"]
    assert summ["pass3_skipped"] is True
    assert summ["pass3_skip_reason"] == "step4_not_committed"
    assert summ["p4_reclaim_shadow_skip_reason"] == "pass3_not_eligible"
    assert summ["step4_committed"] is False
    assert summ["preserve_quality_score"] == 0.612
    assert summ["transport_connected"] is True
    assert summ["pass12_stub_route_recovery_eligible_count"] == 13
    bd = summ["step4_no_route_exhausted_breakdown"]
    assert isinstance(bd, dict)
    assert bd["count"] == 2
    assert bd["sample_rows"] == [{"placement_id": "p1"}]
    flags = body["mining_layout_runtime_flags"]
    assert "shapez_mining_pass12_preserve_stub_route_recovery" in flags
    assert isinstance(flags["shapez_mining_pass12_preserve_stub_route_recovery"], bool)


@patch("django_apps.shapez_asteroid.services.asteroid_mining_layout.build_solver_timeline")
def test_copy_preview_solver_timeline_raises_returns_500(mock_solver: object) -> None:
    mock_solver.side_effect = RuntimeError("boom")

    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)}, query="include_solver_replay=1")
    assert response.status_code == 500
    err = response.json()
    assert err["ok"] is False
    assert err["error_code"] == "solver_timeline_failed"
    assert err["detail"] == "boom"


def test_copy_preview_invalid_copy() -> None:
    client = Client()
    client.get("/asteroid/")
    response = _post_json(client, {"code": "SHAPEZ2-4-@@@@YYYY"})

    assert response.status_code == 400
    err = response.json()
    assert err["ok"] is False
    assert err["error_code"] == "decode_trace_error"
    assert "decode_steps" not in err


def test_copy_preview_invalid_json() -> None:
    client = Client()
    client.get("/asteroid/")
    token = client.cookies.get("csrftoken")
    assert token is not None
    response = client.post(
        "/api/asteroid/copy-preview/",
        data="{",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token.value,
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid json"
    assert body["error_code"] == "invalid_json"


def test_copy_preview_code_not_string() -> None:
    client = Client()
    client.get("/asteroid/")
    response = _post_json(client, {"code": 1})

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "code must be a string"
    assert body["error_code"] == "code_not_string"


def test_copy_preview_debug_dump_writes_encrypt_and_json(tmp_path) -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}]},
    }
    code = _encode_copy(data)
    with override_settings(SHAPEZ_COPY_DEBUG_DIR=str(tmp_path)):
        response = _post_json(client, {"code": code})

    assert response.status_code == 200
    txt_files = sorted(tmp_path.glob("copy_preview_*_encrypt_code.txt"))
    json_files = sorted(tmp_path.glob("copy_preview_*_decoded.json"))
    assert len(txt_files) == 1
    assert len(json_files) == 1
    assert txt_files[0].read_text(encoding="utf-8").strip() == code.strip()
    saved = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert saved == data


def test_copy_preview_debug_dump_prunes_to_ten_stems(tmp_path) -> None:
    base = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}]},
    }
    n = _COPY_PREVIEW_DEBUG_MAX_STEMS
    for i in range(n + 1):
        payload = {**base, "seq": i}
        code = _encode_copy(payload)
        dump_copy_preview_debug(code, payload, tmp_path)
        if i < n:
            time.sleep(0.002)

    txt_files = sorted(tmp_path.glob("copy_preview_*_encrypt_code.txt"))
    json_files = sorted(tmp_path.glob("copy_preview_*_decoded.json"))
    assert len(txt_files) == n
    assert len(json_files) == n
    seqs = sorted(json.loads(p.read_text(encoding="utf-8"))["seq"] for p in json_files)
    assert seqs == list(range(1, n + 1))
