"""Absolute placement cells derived from bundle pattern + anchor."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord


def fixed_output_transport_cell(candidate: BundleCandidate) -> Coord:
    """Absolute FOT coord from projected ``BundlePattern`` only (PR1.5).

    No rotation re-derivation or catalog fallback in commit/validation paths.
    """
    offset = candidate.pattern.fixed_output_transport_offset
    anchor = candidate.anchor_coord
    return (anchor[0] + offset[0], anchor[1] + offset[1])


__all__ = ["fixed_output_transport_cell"]
