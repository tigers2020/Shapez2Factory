"""Replay track key conventions for RTTP (Lab UI vs optimization artifact)."""

from __future__ import annotations

RTTP_TRACK_KEY_PREFIX = "rttp-"
RTTP_OPTIMIZATION_TRACK_SUFFIX = ":rttp"


def rttp_optimization_track_key(run_key: str) -> str:
    """Dedicated track for RTTP milestone frames (not Lab reconstruction timeline)."""

    base = (run_key or "").strip() or "run"
    if base.endswith(RTTP_OPTIMIZATION_TRACK_SUFFIX):
        return base
    return f"{base}{RTTP_OPTIMIZATION_TRACK_SUFFIX}"


def is_rttp_optimization_track_key(track_key: str) -> bool:
    """True for RTTP-only tracks (legacy ``rttp-{run}`` and ``{run}:rttp``)."""

    key = str(track_key).strip()
    return key.startswith(RTTP_TRACK_KEY_PREFIX) or key.endswith(RTTP_OPTIMIZATION_TRACK_SUFFIX)


__all__ = [
    "RTTP_OPTIMIZATION_TRACK_SUFFIX",
    "RTTP_TRACK_KEY_PREFIX",
    "is_rttp_optimization_track_key",
    "rttp_optimization_track_key",
]
