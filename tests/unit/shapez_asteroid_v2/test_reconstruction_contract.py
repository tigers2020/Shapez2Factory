"""STEP 1 reconstruction: decoded JSON in, ``ReconstructionDTO`` out (no NDJSON)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import analyze_to_context
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedBlueprintDocument,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    compute_patch_interior_cells,
    reconstruct_asteroid_mining_field,
)


def _hollow_square_shell(*, inner_x0: int, inner_y0: int, size: int) -> list[dict[str, object]]:
    """Asteroid shell ring with empty interior; ``size`` = outer square side length (>= 3)."""

    entries: list[dict[str, object]] = []
    ix1 = inner_x0 + size - 1
    iy1 = inner_y0 + size - 1
    for x in range(inner_x0, ix1 + 1):
        for y in range(inner_y0, iy1 + 1):
            on_edge = x in (inner_x0, ix1) or y in (inner_y0, iy1)
            if on_edge:
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    return entries


def test_empty_blueprint_returns_empty_reconstruction() -> None:
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": []}})
    assert recon.mineable_placement_cells == ()
    assert recon.full_barrier_cells == ()


def test_reconstruction_accepts_decoded_existing_layout_none() -> None:
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": []}}, None)
    assert recon.extraction_shell_cells == ()


def test_belt_and_pipe_cells_are_separate() -> None:
    decoded = {
        "BP": {
            "Entries": [
                *_hollow_square_shell(inner_x0=10, inner_y0=10, size=5),
                {"X": 12, "Y": 12, "T": "Belt_Straight"},
                {"X": 14, "Y": 14, "T": "SpacePipe_Straight"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (12, 12) in recon.belt_cells
    assert (12, 12) not in recon.pipe_cells
    assert (14, 14) in recon.pipe_cells
    assert (14, 14) not in recon.belt_cells


def test_existing_layout_context_does_not_replace_mineable() -> None:
    island = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=5)}}
    ctx = analyze_to_context(island)
    foreign = {
        "BP": {
            "Entries": [
                {"X": 100, "Y": 100, "T": "Layout_FluidMiner"},
                {"X": 101, "Y": 100, "T": "SpacePipe_Straight"},
            ]
        }
    }
    bad_ctx = analyze_to_context(foreign)
    r0 = reconstruct_asteroid_mining_field(island, None)
    r1 = reconstruct_asteroid_mining_field(island, ctx)
    r2 = reconstruct_asteroid_mining_field(island, bad_ctx)
    assert r0.mineable_placement_cells == r1.mineable_placement_cells == r2.mineable_placement_cells
    assert r0.extraction_shell_cells == r1.extraction_shell_cells


def test_orphan_transport_not_in_extraction_shell() -> None:
    decoded = {
        "BP": {
            "Entries": [
                *_hollow_square_shell(inner_x0=2, inner_y0=2, size=4),
                {"X": 50, "Y": 50, "T": "SpacePipe_Straight"},
                {"X": 51, "Y": 50, "T": "SpacePipe_Straight"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    shell = set(recon.extraction_shell_cells)
    assert (50, 50) not in shell and (51, 50) not in shell
    assert (50, 50) in recon.pipe_cells


def test_interior_patch_inferred_from_shell_without_interior_blueprint_entries() -> None:
    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=4)}}
    recon = reconstruct_asteroid_mining_field(decoded)
    inner = {(x, y) for x in (3, 4) for y in (3, 4)}
    assert set(recon.interior_patch_cells) == inner
    assert inner <= set(recon.mineable_placement_cells)


def test_closing_prevents_tiny_perimeter_gap_leakage_fixture() -> None:
    """Four diagonal shell corners leave a Chebyshev hole; closing seals (``patch_interior``)."""

    corners = {(1, 1), (3, 1), (1, 3), (3, 3)}
    open_interior = compute_patch_interior_cells(corners, perimeter_bridge_steps=0)
    closed_interior = compute_patch_interior_cells(corners, perimeter_bridge_steps=1)
    assert len(closed_interior) > len(open_interior)
    assert closed_interior == [(2, 2)]

    decoded = {
        "BP": {
            "Entries": [{"X": x, "Y": y, "T": "AsteroidField_Corner"} for x, y in sorted(corners)]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (2, 2) in recon.interior_patch_cells
    assert (2, 2) in recon.mineable_placement_cells


def test_reconstruction_is_deterministic() -> None:
    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=4)}}
    a = reconstruct_asteroid_mining_field(decoded)
    b = reconstruct_asteroid_mining_field(DecodedBlueprintDocument(_root=dict(decoded)))
    assert a == b


def test_external_margin_bbox_source_mineable_vs_none() -> None:
    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=5)}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.external_margin_bbox_source == "mineable"
    assert recon.asteroid_bbox is not None
    assert recon.external_margin >= 3

    only_pipe = {"BP": {"Entries": [{"X": 10, "Y": 10, "T": "SpacePipe_Straight"}]}}
    r2 = reconstruct_asteroid_mining_field(only_pipe)
    assert r2.external_margin_bbox_source == "none"


def test_external_margin_bbox_source_shell_when_mineable_empty() -> None:
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
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": ring + belts}})
    assert recon.mineable_placement_cells == ()
    assert recon.extraction_shell_cells
    assert recon.external_margin_bbox_source == "shell"


def test_raw_asteroid_and_existing_layout_outputs_are_not_conflated() -> None:
    raw = {"BP": {"Entries": [{"X": 2, "Y": 2, "T": "AsteroidField_X"}]}}
    existing = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "Layout_FluidMiner"},
                {"X": 3, "Y": 2, "T": "SpacePipe_Straight"},
            ]
        }
    }
    rr = reconstruct_asteroid_mining_field(raw)
    re = reconstruct_asteroid_mining_field(existing)
    assert rr.extraction_shell_cells and not re.extraction_shell_cells
    assert re.pipe_cells and (3, 2) not in rr.pipe_cells


def test_extractor_and_extension_cells_populated() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 5, "T": "Layout_ShapeMiner"},
                {"X": 6, "Y": 5, "T": "Layout_ShapeMinerExtension"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (5, 5) in recon.extractor_cells
    assert (6, 5) in recon.extension_cells
