"""Blueprint entry ``T`` → layout class for filtering mining-relevant BP rows."""

from __future__ import annotations

from enum import StrEnum


class PlotStyle(StrEnum):
    fluid_extension = "fluid_extension"
    extension = "extension"
    fluid_miner = "fluid_miner"
    miner = "miner"
    extractor = "extractor"
    booster = "booster"
    belt = "belt"
    pipe = "pipe"
    platform = "platform"


LAYOUT_STYLE_RULES: tuple[tuple[str, PlotStyle], ...] = (
    ("Layout_FluidMinerExtension", PlotStyle.fluid_extension),
    ("Layout_ShapeMinerExtension", PlotStyle.extension),
    ("Layout_FluidMiner", PlotStyle.fluid_miner),
    ("Layout_ShapeMiner", PlotStyle.miner),
)

EXTRACTION_STYLES: frozenset[PlotStyle] = frozenset(
    {
        PlotStyle.fluid_extension,
        PlotStyle.extension,
        PlotStyle.fluid_miner,
        PlotStyle.miner,
        PlotStyle.extractor,
        PlotStyle.booster,
    }
)

# Single fluid-mining tile look for all map cells (blueprint + inferred interior).
_FLUID_MINING_TILE: dict[str, str] = {"color": "#4f8fc4", "opacity": "0.52"}
MINING_MAP_STYLE_CATALOG: dict[str, dict[str, str]] = {
    "occupied": dict(_FLUID_MINING_TILE),
    "inferred": dict(_FLUID_MINING_TILE),
}


def classify_layout_type(layout_type: str | None) -> PlotStyle | None:
    """Map blueprint ``T`` to a style, or ``None`` if unknown / non-layout."""

    if layout_type is None:
        return None
    t = str(layout_type).strip()
    if not t:
        return None

    for token, style in LAYOUT_STYLE_RULES:
        if token in t:
            return style

    lowered = t.lower()
    if "shapeminer" in lowered and "fluid" not in lowered:
        return PlotStyle.miner
    if "fluidminer" in lowered.replace("_", ""):
        return PlotStyle.fluid_miner

    if "boost" in lowered:
        return PlotStyle.booster
    if "extractor" in lowered or "pump" in lowered:
        return PlotStyle.extractor
    if "belt" in lowered:
        return PlotStyle.belt
    if "pipe" in lowered:
        return PlotStyle.pipe
    if "foundation" in lowered:
        return PlotStyle.platform
    return None


def is_extraction_style(style: PlotStyle | None) -> bool:
    return style is not None and style in EXTRACTION_STYLES


def mining_surface_from_layout(layout_type: str | None) -> str | None:
    """Return ``shape`` / ``fluid`` for mining-relevant layouts, else ``None``."""

    style = classify_layout_type(layout_type)
    if style is None:
        return None
    if style in (PlotStyle.fluid_miner, PlotStyle.fluid_extension):
        return "fluid"
    if style in (PlotStyle.miner, PlotStyle.extension, PlotStyle.extractor, PlotStyle.booster):
        return "shape"
    return None


def asteroid_map_style_catalog() -> dict[str, dict[str, str]]:
    """Palette for unified mining map roles (``occupied`` / ``inferred``)."""

    return {k: dict(v) for k, v in MINING_MAP_STYLE_CATALOG.items()}
