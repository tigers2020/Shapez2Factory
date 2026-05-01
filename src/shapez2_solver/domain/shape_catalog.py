from __future__ import annotations

from dataclasses import dataclass


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


# Official shape codes (dev plan §4 MVP + reviewer sketch).
SHAPE_KINDS: dict[str, ShapeKind] = {
    "C": ShapeKind("C", "Circle", "circle", colorable=True),
    "R": ShapeKind("R", "Rectangle", "rectangle", colorable=True),
    "S": ShapeKind("S", "Star", "spike", colorable=True),
    "W": ShapeKind("W", "Diamond", "diamond", colorable=True),
    "c": ShapeKind("c", "Crystal", "crystal", colorable=True),
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
