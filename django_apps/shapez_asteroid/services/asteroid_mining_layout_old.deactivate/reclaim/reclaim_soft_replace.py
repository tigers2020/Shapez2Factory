"""P4 §14.3: re-export soft-corridor atomic replace (implementation in routing layer)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.protected_corridor_replace import (  # noqa: E501
    _p4_soft_replace_neutral_trace,
    try_atomic_replace_soft_corridor,
)

_try_atomic_replace_soft_corridor = try_atomic_replace_soft_corridor

__all__ = [
    "_p4_soft_replace_neutral_trace",
    "_try_atomic_replace_soft_corridor",
    "try_atomic_replace_soft_corridor",
]
