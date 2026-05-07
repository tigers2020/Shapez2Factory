"""Blueprint entry ``T`` → plot style for asteroid extraction semantic map."""

from __future__ import annotations

from enum import StrEnum


class PlotStyle(StrEnum):
    fluid_extension = "fluid_extension"
    extension = "extension"
    fluid_miner = "fluid_miner"
    miner = "miner"
    extractor = "extractor"
    booster = "booster"
    patch_interior = "patch_interior"
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

STYLE_METADATA: dict[PlotStyle, dict[str, str]] = {
    PlotStyle.fluid_miner: {"color": "#4ea1ff", "legend_group": "fluid"},
    PlotStyle.fluid_extension: {"color": "#6bb8ff", "legend_group": "fluid"},
    PlotStyle.extractor: {"color": "#3d8dff", "legend_group": "fluid"},
    PlotStyle.miner: {"color": "#ff6464", "legend_group": "shape"},
    PlotStyle.extension: {"color": "#ff8d8d", "legend_group": "shape"},
    PlotStyle.booster: {"color": "#b26bff", "legend_group": "boost"},
    PlotStyle.patch_interior: {"color": "#38bdf8", "legend_group": "patch"},
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


def extraction_style_catalog() -> dict[str, dict[str, str]]:
    """JSON-serializable palette for extraction ``PlotStyle`` values only."""

    return {
        style.value: dict(meta)
        for style, meta in STYLE_METADATA.items()
        if style in EXTRACTION_STYLES
    }


def asteroid_map_style_catalog() -> dict[str, dict[str, str]]:
    """Palette for map rendering: extraction buildings + inferred patch interior."""

    out = extraction_style_catalog()
    if PlotStyle.patch_interior in STYLE_METADATA:
        out[PlotStyle.patch_interior.value] = dict(STYLE_METADATA[PlotStyle.patch_interior])
    return out
