"""STEP 1 reconstruction diagnostics (read-only counts and primary_cause)."""

from __future__ import annotations

import copy

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    MineableEmptyCause,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    diagnose_reconstruction_mineable_empty,
    reconstruct_asteroid_mining_field,
)


def _hollow_square_shell(*, inner_x0: int, inner_y0: int, size: int) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    ix1 = inner_x0 + size - 1
    iy1 = inner_y0 + size - 1
    for x in range(inner_x0, ix1 + 1):
        for y in range(inner_y0, iy1 + 1):
            on_edge = x in (inner_x0, ix1) or y in (inner_y0, iy1)
            if on_edge:
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    return entries


def test_diagnose_not_empty_hollow_shell() -> None:
    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=4)}}
    d = diagnose_reconstruction_mineable_empty(decoded)
    assert d.primary_cause == MineableEmptyCause.NOT_EMPTY
    assert d.mineable_placement_count > 0
    assert d.preview_timeline_frame_count is not None
    assert d.preview_timeline_frame_count > 0


def test_diagnose_duplicate_coord_overlay_ring_plus_belts() -> None:
    ring = [
        {"X": x, "Y": y, "T": "AsteroidField_Test"}
        for x, y in [(2, 2), (3, 2), (4, 2), (2, 3), (4, 3), (2, 4), (3, 4), (4, 4)]
    ]
    belt_coords = [
        (2, 2),
        (3, 2),
        (4, 2),
        (2, 3),
        (4, 3),
        (2, 4),
        (3, 4),
        (4, 4),
        (3, 3),
    ]
    belts = [{"X": x, "Y": y, "T": "Belt_Straight"} for x, y in belt_coords]
    decoded = {"BP": {"Entries": ring + belts}}
    d = diagnose_reconstruction_mineable_empty(decoded)
    assert d.primary_cause == MineableEmptyCause.DUPLICATE_COORD_OVERLAY_BLOCKED
    assert d.mineable_placement_count == 0
    assert d.coords_with_shell_and_blocking_count > 0
    assert d.duplicate_coord_count > 0
    assert d.duplicate_coord_samples


def test_diagnose_shell_t_not_recognized_asteroid_like_other() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "Asteroid_Mystery_NotField"},
            ]
        }
    }
    d = diagnose_reconstruction_mineable_empty(decoded)
    assert d.extraction_shell_count == 0
    assert d.asteroid_like_unrecognized_t_counts
    assert d.primary_cause == MineableEmptyCause.SHELL_T_NOT_RECOGNIZED


def test_diagnose_does_not_mutate_reconstruction_argument() -> None:
    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=4)}}
    recon = reconstruct_asteroid_mining_field(decoded)
    snap = copy.deepcopy(recon)
    diagnose_reconstruction_mineable_empty(decoded, reconstruction=recon)
    assert recon == snap


def test_diagnose_empty_blueprint_unknown() -> None:
    d = diagnose_reconstruction_mineable_empty({"BP": {"Entries": []}})
    assert d.primary_cause == MineableEmptyCause.UNKNOWN
    assert d.mineable_placement_count == 0
    assert d.extraction_shell_count == 0


def test_diagnose_small_fragmented_shell_lt_four_cells() -> None:
    """Three colinear shell cells, no overlay: mineable should still be >0; not SMALL."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "AsteroidField_Test"},
                {"X": 3, "Y": 2, "T": "AsteroidField_Test"},
                {"X": 4, "Y": 2, "T": "AsteroidField_Test"},
            ]
        }
    }
    d = diagnose_reconstruction_mineable_empty(decoded)
    assert d.extraction_shell_count == 3
    assert d.primary_cause == MineableEmptyCause.NOT_EMPTY


def test_duplicate_coord_sample_has_blocking_kinds() -> None:
    ring = [{"X": 2, "Y": 2, "T": "AsteroidField_Test"}, {"X": 2, "Y": 2, "T": "Belt_Straight"}]
    d = diagnose_reconstruction_mineable_empty({"BP": {"Entries": ring}})
    assert d.duplicate_coord_samples
    s0 = d.duplicate_coord_samples[0]
    assert s0.cell == (2, 2)
    assert s0.has_shell and s0.has_blocking
    assert "belt" in s0.blocking_kinds


def test_diagnose_extension_only_mineable_primary_not_empty() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 20, "Y": 20, "T": "Layout_ShapeMinerExtension"},
                {"X": 21, "Y": 20, "T": "Layout_ShapeMinerExtension"},
            ]
        }
    }
    d = diagnose_reconstruction_mineable_empty(decoded)
    assert d.primary_cause == MineableEmptyCause.NOT_EMPTY
    assert d.mineable_placement_count == 2
    assert d.extraction_shell_count == 0
    assert d.extension_count == 2
    assert d.candidate_before_blocking_count == 2
    assert d.blocked_candidate_count == 0
