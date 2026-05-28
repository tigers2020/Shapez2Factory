"""Layer 02 connector sprite rotation constants."""

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
    ROTATION_R0_E_CW,
)


def test_rotation_convention_r0_e_clockwise() -> None:
    assert ROTATION_R0_E_CW["east"] == 0
    assert ROTATION_R0_E_CW["south"] == 1
    assert ROTATION_R0_E_CW["west"] == 2
    assert ROTATION_R0_E_CW["north"] == 3


def test_connector_rotation_fieldward_mapping() -> None:
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.NORTH] == 1
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.EAST] == 2
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.SOUTH] == 3
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.WEST] == 0
