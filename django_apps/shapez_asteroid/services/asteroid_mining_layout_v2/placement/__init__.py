"""
STEP 2–3 placement: Pass1 outer-first, Pass2 internal fill (provisional only).

Must not commit final routes; STEP 4 owns ``ROUTED_CONFIRMED`` (CANON).
"""

from __future__ import annotations

from . import bundle_candidate, pass1_outer, pass2_internal

Pass1BundleCandidate = bundle_candidate.Pass1BundleCandidate
Pass2BundleCandidate = bundle_candidate.Pass2BundleCandidate
build_pass2_blocked_set = pass2_internal.build_pass2_blocked_set
cheap_escape_feasible = pass1_outer.cheap_escape_feasible
compute_mineable_perimeter_depth_by_cell = pass1_outer.compute_mineable_perimeter_depth_by_cell
is_pass1_rim_extractor_cell = pass1_outer.is_pass1_rim_extractor_cell
pass1_mineable_outer_first_order = pass1_outer.pass1_mineable_outer_first_order
run_pass1_outer_placement = pass1_outer.run_pass1_outer_placement
run_pass2_internal_fill = pass2_internal.run_pass2_internal_fill

__all__ = [
    "Pass1BundleCandidate",
    "Pass2BundleCandidate",
    "build_pass2_blocked_set",
    "cheap_escape_feasible",
    "compute_mineable_perimeter_depth_by_cell",
    "is_pass1_rim_extractor_cell",
    "pass1_mineable_outer_first_order",
    "run_pass1_outer_placement",
    "run_pass2_internal_fill",
]
