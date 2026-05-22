"""simulation_systems.json path classification rules (Phase 2)."""

from __future__ import annotations

from django_apps.game_data.coverage import reason_codes as rc
from django_apps.game_data.coverage.disposition import Disposition

# Longest matching suffix wins (ordered most-specific first).
_RULES: list[tuple[str, Disposition, str]] = [
    (
        "simulation_parameters.ConnectableSimulations[].Connectors",
        Disposition.PROMOTED,
        "SimulationConnector",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation._Lanes",
        Disposition.PROMOTED,
        "SimulationLaneDefinition",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation.InputLanes",
        Disposition.CROSS_REF,
        "lane importer alias",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].ChunkBounds",
        Disposition.PROMOTED,
        "SimulationChunkBounds",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].TileBounds",
        Disposition.PROMOTED,
        "SimulationTileBounds",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Building",
        Disposition.CROSS_REF,
        "BuildingVariant",
    ),
    (
        "simulation_parameters.ConnectableSimulations[].JunctionsByPivot",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Junctions",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].TileConnectors",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation.State",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation.NextBundle",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation._NextBundle",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation.ProviderConductors",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Simulation.ReceiverConductors",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations[].Buildings",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    (
        "simulation_parameters.ConnectableSimulations",
        Disposition.PROMOTED,
        "ConnectableSimulation",
    ),
    (
        "TileBasedSystems[].ConnectableSimulations",
        Disposition.CROSS_REF,
        "params ConnectableSimulations",
    ),
    ("TileBasedSystems[].ChainPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems[].ExtractorPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems[]._Networks", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    (
        "TileBasedSystems[].JumpLaneLenghtInItemsByDistance",
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    ("definition_snapshot.ChainPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ChainPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ExtractorPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("Interlock.", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("k__BackingField", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    (".Assembly.", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("DefinedTypes", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("ExportedTypes", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("Listeners[]", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ISimulationSystem.", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("IShapeCollectorSystem.", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("IRocketProducerSystem.", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("SimulationFactory.", Disposition.IGNORE_AUDIT, rc.SIMULATION_FACTORY_STUB),
    ("$type", Disposition.IGNORE_AUDIT, rc.RUNTIME_UNITY_METADATA),
    ("$unity", Disposition.IGNORE_AUDIT, rc.RUNTIME_UNITY_METADATA),
]


def classify_norm_path(norm_path: str) -> tuple[Disposition, str] | None:
    """Return disposition for a normalized path (may include definition_snapshot prefix)."""
    path = (norm_path or "").strip()
    if not path:
        return None

    best: tuple[int, Disposition, str] | None = None
    for suffix, disposition, note in _RULES:
        if suffix in path:
            rank = len(suffix)
            if best is None or rank > best[0]:
                best = (rank, disposition, note)

    if best is not None:
        return best[1], best[2]

    if path.startswith("definition_snapshot."):
        return Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE
    if path.startswith("simulation_parameters."):
        return Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE
    return None


def manifest_entries_from_rules() -> dict[str, tuple[Disposition, str]]:
    out: dict[str, tuple[Disposition, str]] = {}
    for suffix, disposition, note in _RULES:
        out[f"simulation_systems.json:{suffix}"] = (disposition, note)
    return out
