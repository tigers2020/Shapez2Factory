"""Canonical coordinate semantics for replay / reconstruction / topology.

This package is the single place for rules such as raw vs server axes,
``x == 0`` conventions, and adjacency normalization. Rules are expanded
incrementally; callers should import explicit functions here rather than
duplicating coordinate logic in tooling apps.
"""

from __future__ import annotations

__all__: list[str] = []
