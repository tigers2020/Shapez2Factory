"""Replay payload limits by track (Phase 9 pre-9B lock)."""

from __future__ import annotations

# Lab timeline adapter & composer (full_map frames; 9B does not truncate).
MAX_LAB_REPLAY_TIMELINE_FRAMES = 500
MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME = 2000

# Solver runtime recorder: align with Lab full_map cap (parity with reconstruction.completed).
MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME = MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME

# Layer 03 pool summary overlay (central assembler).
LAYER03_REPLAY_TOP_N = 8

# Layer 04 per-run selected placement replay frames (central assembler).
MAX_LAYER04_REPLAY_SELECTED = 32
