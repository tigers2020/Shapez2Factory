"""STEP 1 reconstruction: decoded JSON in, ``ReconstructionDTO`` out (no NDJSON)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import analyze_to_context
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import decoded_blueprint
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    MineableCellSemantic,
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    AsteroidResourceKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    compute_patch_interior_cells,
    reconstruct_asteroid_mining_field,
    validate_reconstruction_placement_contract,
    validate_reconstruction_semantic_contract,
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
    by_cell = {s.cell: s for s in recon.mineable_cell_semantics}
    assert set(by_cell) == set(recon.mineable_placement_cells)
    for c in inner:
        assert by_cell[c].resource_kind is AsteroidResourceKind.SHAPE_ASTEROID
        assert by_cell[c].source == "interior_patch_inferred"


def test_interior_patch_inherits_fluid_shell_resource_kind() -> None:
    entries = [
        {"X": x, "Y": y, "T": "AsteroidField_Fluid_Test"}
        for x, y in [
            (10, 10),
            (11, 10),
            (12, 10),
            (10, 11),
            (12, 11),
            (10, 12),
            (11, 12),
            (12, 12),
        ]
    ]
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": entries}})
    assert set(recon.interior_patch_cells) == {(11, 11)}
    by_cell = {s.cell: s for s in recon.mineable_cell_semantics}
    assert by_cell[(11, 11)].resource_kind is AsteroidResourceKind.FLUID_ASTEROID


def test_interior_patch_unknown_when_shell_adjacency_mixed_shape_and_fluid() -> None:
    entries: list[dict[str, int | str]] = []
    for x in (10, 11, 12):
        for y in (10, 11, 12):
            if not (x in (10, 12) or y in (10, 12)):
                continue
            t = "AsteroidField_Fluid_Test" if x == 10 else "AsteroidField_Shape_Test"
            entries.append({"X": x, "Y": y, "T": t})
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": entries}})
    by_cell = {s.cell: s for s in recon.mineable_cell_semantics}
    assert by_cell[(11, 11)].resource_kind is AsteroidResourceKind.UNKNOWN_ASTEROID


def test_validate_reconstruction_semantic_contract_rejects_non_covering_semantics() -> None:
    bad = ReconstructionDTO(
        mineable_placement_cells=((1, 1),),
        interior_patch_cells=(),
        full_barrier_cells=((1, 1),),
        mineable_cell_semantics=(
            MineableCellSemantic((1, 1), AsteroidResourceKind.SHAPE_ASTEROID, "extraction_shell"),
            MineableCellSemantic((2, 2), AsteroidResourceKind.SHAPE_ASTEROID, "extraction_shell"),
        ),
    )
    try:
        validate_reconstruction_semantic_contract(bad)
    except ValueError as exc:
        assert "mineable_cell_semantics" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_validate_reconstruction_semantic_contract_rejects_semantics_on_belt_cell() -> None:
    bad = ReconstructionDTO(
        mineable_placement_cells=((1, 1),),
        interior_patch_cells=(),
        belt_cells=((1, 1),),
        full_barrier_cells=((1, 1),),
        mineable_cell_semantics=(
            MineableCellSemantic((1, 1), AsteroidResourceKind.SHAPE_ASTEROID, "extraction_shell"),
        ),
    )
    try:
        validate_reconstruction_semantic_contract(bad)
    except ValueError as exc:
        assert "belt/pipe" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_closing_prevents_tiny_perimeter_gap_leakage_fixture() -> None:
    """Four diagonal shell corners leave a Chebyshev hole; closing seals (``patch_interior``)."""

    corners = {(1, 1), (3, 1), (1, 3), (3, 3)}
    open_interior = compute_patch_interior_cells(corners, perimeter_bridge_steps=0)
    closed_interior = compute_patch_interior_cells(corners, perimeter_bridge_steps=1)
    assert len(closed_interior) > len(open_interior)
    assert (2, 2) in closed_interior
    assert all(c[0] != 0 for c in closed_interior)

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
    b = reconstruct_asteroid_mining_field(
        decoded_blueprint.DecodedBlueprintDocument(_root=dict(decoded))
    )
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
    assert set(recon.equipment_footprint_mineable_cells) == {(5, 5), (6, 5)}
    assert set(recon.mineable_placement_cells) == {(5, 5), (6, 5)}


def test_extension_only_layout_restores_mineable_from_footprints() -> None:
    """No raw asteroid shell rows: extensions still evidence restored mineable region."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 10, "Y": 10, "T": "Layout_ShapeMinerExtension"},
                {"X": 11, "Y": 10, "T": "Layout_ShapeMinerExtension"},
                {"X": 12, "Y": 10, "T": "Layout_ShapeMinerExtension"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.extraction_shell_cells == ()
    assert len(recon.extension_cells) == 3
    assert set(recon.mineable_placement_cells) == {(10, 10), (11, 10), (12, 10)}
    assert recon.equipment_footprint_mineable_cells == recon.extension_cells


def test_belt_on_same_cell_as_extension_blocks_that_cell_from_mineable() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 4, "Y": 4, "T": "Belt_Straight"},
                {"X": 4, "Y": 4, "T": "Layout_ShapeMinerExtension"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (4, 4) in recon.belt_cells and (4, 4) in recon.extension_cells
    assert (4, 4) not in recon.mineable_placement_cells
    assert (4, 4) in recon.equipment_footprint_mineable_cells


def test_miner_only_without_shell_yields_mineable_extractor_cells() -> None:
    """Extractor footprint alone restores mineable when no asteroid shell rows exist."""

    decoded = {"BP": {"Entries": [{"X": 7, "Y": 7, "T": "Layout_ShapeMiner"}]}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.extraction_shell_cells == ()
    assert (7, 7) in recon.extractor_cells
    assert set(recon.mineable_placement_cells) == {(7, 7)}


def test_pipe_overlapping_miner_excludes_coordinate_from_mineable() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 8, "Y": 8, "T": "Layout_ShapeMiner"},
                {"X": 8, "Y": 8, "T": "SpacePipe_Straight"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (8, 8) in recon.extractor_cells and (8, 8) in recon.pipe_cells
    assert (8, 8) not in recon.mineable_placement_cells


def test_platform_overlapping_extension_excludes_coordinate_from_mineable() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 9, "Y": 9, "T": "Layout_ShapeMinerExtension"},
                {"X": 9, "Y": 9, "T": "Foundation_Test"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (9, 9) in recon.extension_cells
    assert (9, 9) not in recon.mineable_placement_cells


def test_blueprint_entries_at_x_zero_are_never_ingested() -> None:
    """X==0 column is skipped at scan (same convention as ``blueprint_map_summary``)."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 0, "Y": 10, "T": "Layout_ShapeMinerExtension"},
                {"X": 1, "Y": 10, "T": "Layout_ShapeMinerExtension"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (0, 10) not in recon.extension_cells and (0, 10) not in recon.full_barrier_cells
    assert (1, 10) in recon.extension_cells
    assert set(recon.mineable_placement_cells) == {(1, 10)}


def test_distant_coordinates_without_blueprint_rows_not_in_mineable() -> None:
    """Arbitrary empty map sites are not mineable — only reconstructed region cells are."""

    decoded = {"BP": {"Entries": _hollow_square_shell(inner_x0=2, inner_y0=2, size=4)}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (500, 500) not in recon.mineable_placement_cells


def test_many_extensions_no_shell_mineable_matches_extension_count() -> None:
    """Regression shape: large extension-only layouts must keep mineable > 0 (artifact-style)."""

    n = 80
    decoded = {
        "BP": {
            "Entries": [
                {"X": 200 + i, "Y": 300, "T": "Layout_ShapeMinerExtension"} for i in range(n)
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.extraction_shell_cells == ()
    assert len(recon.extension_cells) == n
    assert len(recon.mineable_placement_cells) == n
    assert len(recon.equipment_footprint_mineable_cells) == n


def test_fully_occupied_interior_no_inferior_patch_mineable_is_shell_plus_miner() -> None:
    """Inner 2×2 filled with BP rows: no interior_patch; mineable = shell ∪ miner − blockers."""

    entries = list(_hollow_square_shell(inner_x0=2, inner_y0=2, size=4))
    entries += [
        {"X": 3, "Y": 3, "T": "Belt_Straight"},
        {"X": 4, "Y": 3, "T": "Foundation_Test"},
        {"X": 3, "Y": 4, "T": "Layout_ShapeMiner"},
        {"X": 4, "Y": 4, "T": "Z_Unknown_Blocker_Xyz"},
    ]
    recon = reconstruct_asteroid_mining_field({"BP": {"Entries": entries}})
    assert recon.interior_patch_cells == ()
    assert (3, 4) in recon.mineable_placement_cells
    for blocked in ((3, 3), (4, 3), (4, 4)):
        assert blocked not in recon.mineable_placement_cells
    assert len(recon.mineable_placement_cells) == len(recon.extraction_shell_cells) + 1


def test_interior_patch_from_extension_ring_without_asteroid_field_rows() -> None:
    """Equipment-only perimeter (no ``AsteroidField*``) still closes an interior void."""

    entries: list[dict[str, int | str]] = []
    for x in range(10, 14):
        for y in range(10, 14):
            if x in (10, 13) or y in (10, 13):
                entries.append({"X": x, "Y": y, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    inner = {(11, 11), (12, 11), (11, 12), (12, 12)}
    assert recon.extraction_shell_cells == ()
    assert set(recon.interior_patch_cells) == inner
    assert inner <= set(recon.mineable_placement_cells)
    assert len(recon.mineable_placement_cells) == len(recon.extension_cells) + len(inner)


def test_validate_reconstruction_placement_contract_rejects_disjoint_interior() -> None:
    bad = ReconstructionDTO(
        mineable_placement_cells=((1, 1),),
        interior_patch_cells=((2, 2),),
        full_barrier_cells=((1, 1), (2, 2)),
    )
    try:
        validate_reconstruction_placement_contract(bad)
    except ValueError as exc:
        assert "interior_patch_cells" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_reconstruction_never_contains_x_zero_cells_across_negative_positive_shell() -> None:
    """Two physical columns only (``x=-1`` and ``x=1``); outputs must omit ``x==0``."""

    entries: list[dict[str, object]] = []
    for y in range(0, 4):
        entries.append({"X": -1, "Y": y, "T": "AsteroidField_Test"})
        entries.append({"X": 1, "Y": y, "T": "AsteroidField_Test"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    for cells in (
        recon.mineable_placement_cells,
        recon.extraction_shell_cells,
        recon.interior_patch_cells,
        recon.full_barrier_cells,
    ):
        assert all(c[0] != 0 for c in cells)
