"""Top-level ``BP.Entries[*].T`` → lab cell / transport classification (A5)."""

from __future__ import annotations


def classify_blueprint_entry(tile_type: str | None) -> tuple[str, str]:
    """Return ``(cell_kind, transport_kind)`` for one blueprint entry type string ``T``.

    Rules (top-level entries only; nested ``B.Entries`` are classified separately).
    """

    t = "" if tile_type is None else str(tile_type)
    if t.startswith("SpacePipe"):
        return ("space_pipe", "fluid_pipe")
    if t.startswith("SpaceBelt"):
        return ("space_belt", "shape_belt")
    if t == "Layout_FluidMiner":
        return ("fluid_miner", "fluid_pipe")
    if t == "Layout_FluidMinerExtension":
        return ("fluid_miner_extension", "fluid_pipe")
    if t in ("Layout_ShapeMiner", "Layout_ProMiner"):
        return ("shape_miner", "shape_belt")
    if t == "Layout_ShapeMinerExtension":
        return ("shape_miner_extension", "shape_belt")
    return ("unknown", "none")


__all__ = ["classify_blueprint_entry"]
