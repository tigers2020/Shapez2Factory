"""
Extractor + extensions + output stub as a single commit unit (bundle).

Shared typing between Pass1/Pass2; no routing geometry commits here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PlacementBundleCandidate:
    """Placeholder bundle descriptor until topology generator exists."""

    bundle_id: str
    extractor_cell: tuple[int, int]
    metadata: dict[str, Any] | None = None
