"""CLR parser for simulation_systems source_type_name."""

from __future__ import annotations

from django_apps.game_data.services.simulation_clr_parser import parse_simulation_clr


def test_parse_island_generic() -> None:
    raw = (
        "AtomicStatefulIslandSimulationSystem`2[[SpaceConveyorSimulation, Game.Content, "
        "Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],"
        "[SpaceConveyorSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, "
        "PublicKeyToken=null]]"
    )
    parsed = parse_simulation_clr(raw)
    assert parsed.family == "AtomicStatefulIslandSimulationSystem"
    assert parsed.simulation_class == "SpaceConveyorSimulation"
    assert parsed.state_class == "SpaceConveyorSimulationState"
    assert parsed.is_standalone is False


def test_parse_building_generic_sample_16() -> None:
    raw = (
        "AtomicStatefulBuildingSimulationSystem`2[[SplitterTShapeSimulation, Game.Content, "
        "Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],"
        "[PrioritySplitterSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, "
        "PublicKeyToken=null]]"
    )
    parsed = parse_simulation_clr(raw)
    assert parsed.simulation_class == "SplitterTShapeSimulation"
    assert parsed.state_class == "PrioritySplitterSimulationState"


def test_parse_standalone_converter() -> None:
    raw = "Game.Content.AtomicIslands.Converters.SpaceConverterSystem"
    parsed = parse_simulation_clr(raw)
    assert parsed.is_standalone is True
    assert parsed.family == "SpaceConverterSystem"
    assert parsed.simulation_class == "SpaceConverterSystem"
    assert parsed.state_class is None


def test_parse_empty_returns_unknown() -> None:
    parsed = parse_simulation_clr("")
    assert parsed.family == "unknown"
