"""
v2 orchestration entrypoint (STEP 0 … STEP 10 wiring).

Keeps Django ORM out of the import path; callers pass plain data / paths later.
"""

from __future__ import annotations

from typing import Any


def solve_mining_layout_v2_stub(_request: dict[str, Any]) -> dict[str, Any]:
    """End-to-end solve (not implemented)."""
    msg = "solve_mining_layout_v2_stub is not implemented (skeleton only)"
    raise NotImplementedError(msg)
