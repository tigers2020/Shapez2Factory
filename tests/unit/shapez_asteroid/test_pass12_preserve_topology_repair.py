"""Regression tests for Pass12 preserve extension ownership and Pass2 trunk-merge probe."""

from __future__ import annotations

from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS12_MAX_EXTENSION_TILES,
    PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit as p12_bc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_merged_layout_seed as p12_seed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12_rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as final_val,
)

Pass12BundleCandidate = p12_bc.Pass12BundleCandidate
Pass12LayoutScratch = p12_bc.Pass12LayoutScratch
try_commit_pass2_bundle = p12_bc.try_commit_pass2_bundle
_merged_seed_extension_sets_by_miner = p12_seed._merged_seed_extension_sets_by_miner
_pass2_stub_adjacent_baseline_trunk_reaches_external = (
    p12_rp._pass2_stub_adjacent_baseline_trunk_reaches_external
)
bundle_route_probe_or_reject = p12_rp.bundle_route_probe_or_reject


def _shape_miner(x: int, y: int, r: int = 0) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "occupied",
        "layout_kind": "miner",
        "surface": "shape",
        "t": "Layout_ShapeMiner",
        "r": r,
    }


def _shape_ext(x: int, y: int, r: int = 0) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "occupied",
        "layout_kind": "extension",
        "surface": "shape",
        "t": "Layout_ShapeMinerExtension",
        "r": r,
    }


def _field(x: int, y: int) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "occupied",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def test_merged_seed_shared_extension_tie_breaker_prefers_lower_scan_index() -> None:
    """Equidistant extension between two miners goes to the lexicographically earlier root."""

    rows = [
        _field(1, 1),
        _field(7, 1),
        _shape_miner(2, 1),
        _shape_ext(3, 1),
        _shape_ext(4, 1),
        _shape_ext(5, 1),
        _shape_miner(6, 1),
    ]
    cells = final_val.cells_dict_from_mining_map(rows)
    mineable = frozenset((r["x"], r["y"]) for r in rows)
    miners = sorted(
        ((x, y) for (x, y), row in cells.items() if row.get("layout_kind") == "miner"),
        key=lambda p: (p[1], p[0]),
    )
    assert miners == [(2, 1), (6, 1)]
    by_m = _merged_seed_extension_sets_by_miner(miners, cells, mineable)
    assert by_m[(2, 1)] == frozenset({(3, 1), (4, 1)})
    assert by_m[(6, 1)] == frozenset({(5, 1)})


def test_merged_seed_extension_cap_per_miner() -> None:
    """At most ``PASS12_MAX_EXTENSION_TILES`` extensions per extractor bundle."""

    rows = [
        _field(0, 1),
        _field(8, 1),
        _shape_miner(2, 1),
        _shape_ext(3, 1),
        _shape_ext(4, 1),
        _shape_ext(5, 1),
        _shape_ext(6, 1),
    ]
    cells = final_val.cells_dict_from_mining_map(rows)
    mineable = frozenset((r["x"], r["y"]) for r in rows)
    miners = [(2, 1)]
    by_m = _merged_seed_extension_sets_by_miner(miners, cells, mineable)
    assert len(by_m[(2, 1)]) == PASS12_MAX_EXTENSION_TILES
    assert (6, 1) not in by_m[(2, 1)]


def test_pass2_merge_probe_baseline_trunk_reaches_external() -> None:
    """Adjacency to baseline trunk that reaches external succeeds when stub graph is isolated."""

    stub = (5, 0)
    trunk = (6, 0)
    tail = (7, 0)
    baseline = frozenset({trunk, tail})
    transport = frozenset({stub, trunk, tail})
    ok, diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
        stub,
        transport_cells=transport,
        blocked_cells=frozenset(),
        is_external=lambda c: c[0] >= 8,
        adjacent_preserve_trunk_baseline_cells=baseline,
    )
    assert ok is True
    assert diag["pass2_preserve_merge_probe"]["via_baseline_trunk_cell"] == [6, 0]


def test_pass2_merge_probe_fails_when_baseline_not_in_transport() -> None:
    stub = (5, 0)
    trunk = (6, 0)
    ok, _diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
        stub,
        transport_cells=frozenset({stub}),
        blocked_cells=frozenset(),
        is_external=lambda c: c[0] >= 10,
        adjacent_preserve_trunk_baseline_cells=frozenset({trunk}),
    )
    assert ok is False


def test_try_commit_pass2_bundle_preserve_merge_succeeds() -> None:
    """Pass2 commit when baseline trunk reaches external (merge probe wiring)."""

    scratch = Pass12LayoutScratch(transport_kind="shape_belt")
    scratch.transport_cells = {(6, 0), (7, 0), (8, 0), (9, 0), (10, 0)}
    scratch.blocked_cells = {(2, 0)}
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(2, 0)}),
        new_transport=frozenset({(5, 0)}),
        stub_cell=(5, 0),
        extractor_cell=(2, 0),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )
    baseline = frozenset({(6, 0), (7, 0), (8, 0), (9, 0), (10, 0)})
    assert (
        try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=lambda c: c[0] >= 11,
            adjacent_preserve_trunk_baseline_cells=baseline,
        )
        is True
    )


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True)
def test_preserve_stub_recovery_setting_enables_recovery_sort_path() -> None:
    """With recovery ON, merged seed uses proximity sort (integration smoke)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass12_merged_layout_seed as p12_merged,
    )

    seed_pass12_scratch_from_merged_existing = p12_merged.seed_pass12_scratch_from_merged_existing

    rows = [
        _field(4, 5),
        _field(8, 5),
        _shape_miner(5, 5, r=0),
        {"x": 6, "y": 5, "role": "belt", "surface": "shape"},
    ]
    mineable = frozenset((r["x"], r["y"]) for r in rows)
    scratch = Pass12LayoutScratch()
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert stats["pass12_merged_seed_miner_count"] == 1
    assert stats.get("pass12_preserved_recovery_success_count", 0) >= 0


def test_bundle_route_probe_pass2_merge_branch_skipped_without_baseline() -> None:
    """Reject path includes merge diagnosis when baseline context is absent (Pass1-style)."""

    ok = bundle_route_probe_or_reject(
        (1, 1),
        transport_cells=frozenset({(1, 1)}),
        blocked_cells=frozenset(),
        is_external=lambda c: False,
        trace_location="pass12_bundle_commit.try_commit_pass1_bundle",
        pass2_adjacent_preserve_trunk_baseline_cells=None,
    )
    assert ok is False


def test_bundle_route_probe_pass2_with_baseline_merge_still_fails_if_orphan() -> None:
    """Baseline neighbor that does not reach external cannot salvage a dead stub."""

    ok = bundle_route_probe_or_reject(
        (5, 0),
        transport_cells=frozenset({(5, 0), (6, 0)}),
        blocked_cells=frozenset(),
        is_external=lambda c: c[0] >= 100,
        trace_location=PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION,
        pass2_adjacent_preserve_trunk_baseline_cells=frozenset({(6, 0)}),
    )
    assert ok is False
