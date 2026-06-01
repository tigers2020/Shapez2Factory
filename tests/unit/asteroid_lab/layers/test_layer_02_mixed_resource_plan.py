"""L2 must plan connectors for every present resource kind (mixed-map contract)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import TransportKind
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan,
)
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_cleanup_and_recon_from_cells,
    minimal_complete_map_from_cells,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


def _field_cell(x: int, y: int, *, cell_kind: str) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


@pytest.mark.django_db
def test_l2_plan_builds_pipe_connectors_for_fluid() -> None:
    shape_shell = build_rect_field_with_void_shell(width=8, height=8, void_pad=10)
    complete_map = minimal_complete_map_from_cells(
        *(
            _field_cell(x, y, cell_kind="asteroid_fluid_field")
            for x in range(8)
            for y in range(8)
        ),
    )
    complete_map = type(complete_map)(
        cells=complete_map.cells,
        field_cells=shape_shell.field_cells,
        shape_field_cell_count=0,
        fluid_field_cell_count=len(shape_shell.field_cells),
        external_void_cells=shape_shell.external_void_cells,
        coord_frame=complete_map.coord_frame,
    )
    plan = build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind="fluid",
        terrain_upper_bound_per_min=Decimal("2400"),
        throughput_target_percent=80,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    assert plan.planned_connectors
    assert {c.layout_t for c in plan.planned_connectors} == {"SpacePipe_Forward"}


@pytest.mark.django_db
def test_shape_primary_mixed_map_still_provides_pipe_goals() -> None:
    shell = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    cells: list[DecodedCellDTO] = []
    fluid_coords = {(0, 0), (1, 0), (2, 0), (3, 0)}
    for x, y in shell.field_cells:
        kind = (
            "asteroid_fluid_field"
            if (x, y) in fluid_coords
            else "asteroid_shape_field"
        )
        cells.append(_field_cell(x, y, cell_kind=kind))
    cleanup, recon = minimal_cleanup_and_recon_from_cells(*cells)
    layer01 = run_layer_01(cleanup=cleanup, recon=recon)
    assert layer01.capacity_envelope["primary_resource_kind"] == "shape"
    assert layer01.capacity_envelope["present_resource_kinds"] == ["shape", "fluid"]

    plan = execute_layer_02_exterior_transport_plan(
        complete_map=layer01.complete_map,
        capacity_envelope=layer01.capacity_envelope,
        throughput_target_percent=80,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    pipe_goals = build_layer03_route_goals(plan, transport_kind=TransportKind.FLUID_PIPE)
    assert pipe_goals


@pytest.mark.django_db
def test_envelope_lists_present_resource_kinds_for_mixed_map() -> None:
    complete = minimal_complete_map_from_cells(
        _field_cell(0, 0, cell_kind="asteroid_shape_field"),
        _field_cell(1, 0, cell_kind="asteroid_fluid_field"),
    )
    env = build_reconstruction_capacity_envelope(complete_map=complete)
    assert env["present_resource_kinds"] == ["shape", "fluid"]
