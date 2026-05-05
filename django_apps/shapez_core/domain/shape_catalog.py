from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ShapeKind:
    code: str
    name: str
    solver_kind: str
    colorable: bool
    empty: bool = False


@dataclass(frozen=True, slots=True)
class ColorKind:
    code: str
    name: str
    solver_kind: str
    empty: bool = False


SHAPE_KINDS: dict[str, ShapeKind] = {
    "C": ShapeKind("C", "Circle", "circle", colorable=True),
    "R": ShapeKind("R", "Rectangle", "rectangle", colorable=True),
    "S": ShapeKind("S", "Star", "spike", colorable=True),
    "W": ShapeKind("W", "Diamond", "diamond", colorable=True),
    "c": ShapeKind("c", "Crystal", "crystal", colorable=True),
    # Pin quadrants are spelled P- in shape codes; "-" here is not an empty quadrant.
    "P": ShapeKind("P", "Pin", "pin", colorable=False),
    "-": ShapeKind("-", "Empty", "empty", colorable=False, empty=True),
}

COLOR_KINDS: dict[str, ColorKind] = {
    "u": ColorKind("u", "Uncolored", "uncolored", empty=False),
    "r": ColorKind("r", "Red", "red", empty=False),
    "g": ColorKind("g", "Green", "green", empty=False),
    "b": ColorKind("b", "Blue", "blue", empty=False),
    "c": ColorKind("c", "Cyan", "cyan", empty=False),
    "m": ColorKind("m", "Magenta", "magenta", empty=False),
    "y": ColorKind("y", "Yellow", "yellow", empty=False),
    "w": ColorKind("w", "White", "white", empty=False),
    "-": ColorKind("-", "Empty", "empty", empty=True),
}

# 유체 소스·레거시 painter 잉크: 원색만 직접 선택. 문서: documents/game_rules/fluid_carrier.md
FLUID_SOURCE_PRIMARY_COLORS: Final[frozenset[str]] = frozenset({"r", "g", "b"})
# color_mixer 등으로만 달성한다고 가정하는 보조·합성 색(참고용 집합).
FLUID_MIXER_DERIVED_COLORS: Final[frozenset[str]] = frozenset({"c", "m", "y", "w"})
