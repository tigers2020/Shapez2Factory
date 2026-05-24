"""Shared fixtures for ``tests/unit/asteroid_lab``."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    load_reconstruction_fixture_line_pairs,
)
from django_apps.shapez_core.models import (
    ShapezBasedataRelease,
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
)


@pytest.fixture
def lab_sprite_identifiers_for_admin() -> ShapezBasedataRelease:
    r = ShapezBasedataRelease.objects.create(
        game_version=900_043,
        notes="genetic-lab-sprite-test",
        integrity_status_id=ShapezBasedataRelease.IntegrityStatus.IMPORTED.value,
    )
    cat = ShapezIdentifierCategory.objects.create(release=r, key="BuildingVariantIds", sort_order=0)
    for value, rel in (
        ("SpacePipe_LeftTurn", "SpacePipe/SpacePipe_LeftTurn.svg"),
        ("SpacePipe_RightTurn", "SpacePipe/SpacePipe_RightTurn.svg"),
        ("SpacePipe_LeftFwdSplitter", "SpacePipe/SpacePipe_LeftFwdSplitter.svg"),
        ("SpacePipe_Forward", "SpacePipe/SpacePipe_Forward.svg"),
    ):
        ShapezGameIdentifier.objects.create(
            release=r,
            identifier_category=cat,
            value=value,
            normalized_value=value,
            sprite_static_relpath=rel,
        )
    return r


@pytest.fixture(params=range(len(load_reconstruction_fixture_line_pairs())))
def reconstruction_fixture_line_index(request: pytest.FixtureRequest) -> int:
    return int(request.param)


CONNECTED_BRANCH_GENE_KEY = (
    '{"e":[[[-1,1],[-1,2],"S"],[[0,0],[0,1],"S"],[[0,1],[-1,1],"W"]],"ec":3,"tk":"pipe"}'
)


@pytest.fixture(scope="module")
def exhaustive_genes_ext3() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=3)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=0)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=0, transport_kinds=("belt",))


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt_v1() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(
        max_extensions=0,
        transport_kinds=("belt",),
        generator_version="exhaustive_sample_gene_v1",
    )


@pytest.fixture(scope="module")
def exhaustive_genes_ext1_belt() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(max_extensions=1, transport_kinds=("belt",))


@pytest.fixture
def connected_branch_gene_ext3(
    exhaustive_genes_ext3: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> GeneratedSampleGene:
    genes, _stats = exhaustive_genes_ext3
    return next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)


def _perimeter_cells(block: frozenset[Coord]) -> frozenset[Coord]:
    neighbors4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
    return frozenset(
        coord
        for coord in block
        if any((coord[0] + dx, coord[1] + dy) not in block for dx, dy in neighbors4)
    )


def _external_void_ring(mineable: frozenset[Coord]) -> frozenset[Coord]:
    neighbors4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
    void: set[Coord] = set()
    for coord in mineable:
        for dx, dy in neighbors4:
            neighbor = (coord[0] + dx, coord[1] + dy)
            if neighbor not in mineable:
                void.add(neighbor)
    return frozenset(void)


def _external_margin_goals(
    rim: frozenset[Coord],
    external_void: frozenset[Coord],
) -> tuple[RouteGoal, ...]:
    seen: set[Coord] = set()
    goals: list[RouteGoal] = []
    for rim_cell in sorted(rim):
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            neighbor = (rim_cell[0] + dx, rim_cell[1] + dy)
            if neighbor not in external_void or neighbor in seen:
                continue
            seen.add(neighbor)
            goals.append(
                RouteGoal(
                    coord=neighbor,
                    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                    transport_kind=TransportKind.SHAPE_BELT,
                    priority=20,
                    existing_trunk=False,
                )
            )
    return tuple(goals)


@pytest.fixture
def greenfield_optimization_input(
    catalog_slice_minimal: BuildingCatalogSlice,
) -> OptimizationInput:
    """Minimal greenfield map: 4×4 mineable block (16 cells), empty trunk/protected."""

    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = _perimeter_cells(mineable)
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=_external_margin_goals(rim, external_void),
        existing_transport_cells=frozenset(),
        catalog_slice=catalog_slice_minimal,
    )


@pytest.fixture
def catalog_slice_minimal() -> BuildingCatalogSlice:
    from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

    return build_minimal_test_catalog_slice()


@pytest.fixture
def greenfield_with_catalog(
    greenfield_optimization_input: OptimizationInput,
    catalog_slice_minimal: BuildingCatalogSlice,
) -> OptimizationInput:
    return replace(
        greenfield_optimization_input,
        catalog_slice=catalog_slice_minimal,
    )
