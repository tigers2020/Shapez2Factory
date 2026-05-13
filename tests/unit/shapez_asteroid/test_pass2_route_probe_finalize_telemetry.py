"""Pass2 route probe stats: NDJSON telemetry contract on finalize."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as _p12_route_probe,
)


def test_finalize_pass2_fills_margin_diagnostic_when_trace_missing_key() -> None:
    """``pass2_probe_last_goal_trace``에 diagnostic이 없으면 gap-fill로 키를 보장한다."""

    stats_sink: dict[str, object] = {
        "pass2_probe_goal_set_kind_counts": {"first_route": 1},
        "pass2_probe_last_final_goal_count": 0,
        "pass2_probe_last_goal_trace": {
            "final_goal_count": 0,
            "universe_cell_count": 5,
            "mineable_asteroid_bbox": {"x_min": 1, "x_max": 2, "y_min": 1, "y_max": 2},
        },
    }
    _p12_route_probe.finalize_pass2_route_probe_stats(stats_sink)
    lt = stats_sink["pass2_probe_last_goal_trace"]
    assert isinstance(lt, dict)
    md = lt.get("pass2_external_margin_diagnostic")
    assert isinstance(md, dict)
    assert "universe_scan_cell_count" in md
    assert md.get("solver_summary_gap_fill") is True
