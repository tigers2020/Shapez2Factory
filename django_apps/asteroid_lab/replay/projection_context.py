"""Replay coordinate projection (Phase 9C; island-native frames)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.replay.timeline_dtos import ReplayCell


def lab_xy_from_replay_cell(x: int, y: int) -> tuple[int, int]:
    """Island-local replay cell coordinates (identity; PR-F canonical path)."""

    return int(x), int(y)


@dataclass(frozen=True, slots=True)
class ReplayProjectionContext:
    """Adapter-only projection inputs (never algorithm input)."""

    base_ref: str | None = None
    fallback_full_cells: tuple[ReplayCell, ...] = ()
