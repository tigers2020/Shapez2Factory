from __future__ import annotations

from django_apps.shapez_core.domain.shape_catalog import (
    COLOR_KINDS,
    SHAPE_KINDS,
    ColorKind,
    ShapeKind,
)
from django_apps.shapez_core.domain.shape_pattern import (
    NormalizedShapeCell,
    NormalizedShapeLayer,
    NormalizedShapePattern,
    quadrant_at_index,
)


class ShapeCodeParseError(ValueError):
    """Invalid shape code list, pattern, layer, or token."""

    def __init__(self, message: str, offset: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.offset = offset

    def __str__(self) -> str:
        if self.offset is None:
            return self.message
        return f"{self.message} (at {self.offset})"


def parse_shape_code_list(raw: str) -> tuple[NormalizedShapePattern, ...]:
    body = _extract_list_body(raw)
    pattern_strings = _split_pattern_segments(body)
    if not pattern_strings:
        raise ShapeCodeParseError("no patterns in shape code list", 0)
    return tuple(_parse_single_pattern(pattern) for pattern in pattern_strings)


def _extract_list_body(raw: str) -> str:
    stripped = raw.strip()
    if not stripped:
        raise ShapeCodeParseError("empty shape code", 0)

    opens = stripped.startswith("[")
    closes = stripped.endswith("]")
    if opens ^ closes:
        raise ShapeCodeParseError("mismatched brackets", 0)
    if opens:
        inner = stripped[1:-1].strip()
        if not inner:
            raise ShapeCodeParseError("empty bracket list", 1)
        if "[" in inner or "]" in inner:
            bad = next(index for index, char in enumerate(inner) if char in "[]")
            raise ShapeCodeParseError("nested or stray brackets are not allowed", bad + 1)
        return inner

    if "[" in stripped or "]" in stripped:
        bad = stripped.index("[") if "[" in stripped else stripped.index("]")
        raise ShapeCodeParseError("unexpected bracket", bad)
    return stripped


def _split_pattern_segments(body: str) -> list[str]:
    parts = [part.strip() for part in body.split(",")]
    segments = [part for part in parts if part]
    if len(segments) != len(parts):
        raise ShapeCodeParseError("empty pattern segment in list", 0)
    return segments


def _parse_single_pattern(raw_pattern: str) -> NormalizedShapePattern:
    raw_code = raw_pattern.strip()
    if not raw_code:
        raise ShapeCodeParseError("empty pattern", 0)

    layer_specs = [layer.strip() for layer in raw_code.split(":")]
    if any(not layer for layer in layer_specs):
        raise ShapeCodeParseError("empty layer in pattern", 0)

    layers: list[NormalizedShapeLayer] = []
    for layer_index, layer_str in enumerate(layer_specs):
        cells = _parse_layer(layer_index, layer_str)
        layers.append(NormalizedShapeLayer(layer_index=layer_index, cells=cells))

    normalized_code = ":".join(_layer_to_code(layer) for layer in layers)
    return NormalizedShapePattern(
        raw_code=raw_code,
        normalized_code=normalized_code,
        layers=tuple(layers),
    )


def _layer_to_code(layer: NormalizedShapeLayer) -> str:
    return "".join(cell.raw_token for cell in layer.cells)


def _parse_layer(layer_index: int, layer_str: str) -> tuple[NormalizedShapeCell, ...]:
    if len(layer_str) != 8:
        raise ShapeCodeParseError(
            f"layer {layer_index} must be 8 characters (four tokens), got {len(layer_str)}",
            None,
        )

    cells: list[NormalizedShapeCell] = []
    for quadrant in range(4):
        token = layer_str[quadrant * 2 : quadrant * 2 + 2]
        shape_ch = token[0]
        color_ch = token[1]
        shape_kind = _require_shape(shape_ch, layer_index, quadrant)
        if shape_kind.code == "P":
            if color_ch != "-":
                raise ShapeCodeParseError(
                    f"pin quadrant must be P-, got {token!r} "
                    f"in layer {layer_index} quadrant {quadrant}",
                    None,
                )
            pin_color_kind = COLOR_KINDS["u"]
            cells.append(
                NormalizedShapeCell(
                    quadrant_index=quadrant,
                    position=quadrant_at_index(quadrant),
                    shape_code="P",
                    color_code="-",
                    shape_kind=shape_kind.solver_kind,
                    color_kind=pin_color_kind.solver_kind,
                    raw_token="P-",
                )
            )
            continue

        color_kind = _require_color(color_ch, layer_index, quadrant)
        _validate_token_pair(layer_index, quadrant, token, shape_kind, color_kind)
        cells.append(
            NormalizedShapeCell(
                quadrant_index=quadrant,
                position=quadrant_at_index(quadrant),
                shape_code=shape_ch,
                color_code=color_ch,
                shape_kind=shape_kind.solver_kind,
                color_kind=color_kind.solver_kind,
                raw_token=token,
            )
        )
    return tuple(cells)


def _require_shape(shape_ch: str, layer_index: int, quadrant: int) -> ShapeKind:
    shape_kind = SHAPE_KINDS.get(shape_ch)
    if shape_kind is None:
        raise ShapeCodeParseError(
            f"unknown shape code {shape_ch!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
    return shape_kind


def _require_color(color_ch: str, layer_index: int, quadrant: int) -> ColorKind:
    color_kind = COLOR_KINDS.get(color_ch)
    if color_kind is None:
        raise ShapeCodeParseError(
            f"unknown color code {color_ch!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
    return color_kind


def _validate_token_pair(
    layer_index: int,
    quadrant: int,
    token: str,
    shape_kind: ShapeKind,
    color_kind: ColorKind,
) -> None:
    if shape_kind.empty != color_kind.empty:
        raise ShapeCodeParseError(
            f"shape/color emptiness mismatch for token {token!r} "
            f"in layer {layer_index} quadrant {quadrant}",
            None,
        )
    if shape_kind.empty:
        return
    if not shape_kind.colorable and color_kind.code != "u":
        raise ShapeCodeParseError(
            f"shape {shape_kind.code!r} is not colorable; only uncolored (u) is allowed, "
            f"got {token!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
