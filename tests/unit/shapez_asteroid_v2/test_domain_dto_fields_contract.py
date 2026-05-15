"""Frozen field names for core Pass DTOs (``03_data_schema_dto.md`` §19.1)."""

from __future__ import annotations

from dataclasses import fields

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    Pass2Result,
    TraceEvent,
)


def test_pass1_result_field_names_frozen() -> None:
    assert {f.name for f in fields(Pass1Result)} == frozenset(
        {
            "placements",
            "placement_occupied_cells",
            "output_stub_cells",
            "occupied_cells",
            "placement_commit_entries",
            "beam_trace",
        }
    )


def test_pass2_result_field_names_frozen() -> None:
    assert {f.name for f in fields(Pass2Result)} == frozenset(
        {
            "provisional_placements",
            "blocked_cells_delta",
            "placement_commit_entries",
            "beam_trace",
            "corridor_opening_trace",
            "pass1_after_corridor_gate",
            "solver_ctx_after_corridor_gate",
        }
    )


def test_trace_event_field_names_frozen() -> None:
    assert {f.name for f in fields(TraceEvent)} == frozenset(
        {
            "run_id",
            "phase",
            "step_index",
            "event_type",
            "committed",
            "commit_reason",
            "rejected_reason",
            "rollback_reason",
            "recovery_trigger",
            "computation_cycle",
            "route_level",
            "transport_kind",
        }
    )
