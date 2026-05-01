from __future__ import annotations

from shapez2_solver.domain.shape_catalog import COLOR_KINDS, SHAPE_KINDS, ColorKind, ShapeKind
from shapez2_solver.domain.shape_pattern import (
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
    """Parse a shape code list into one or more normalized patterns.

    Grammar (dev plan §6): optional brackets, comma-separated ``shape_pattern``,
    each pattern is ``shape_layer (':' shape_layer)*``, each layer four two-char tokens.
    """
    body = _extract_list_body(raw)
    pattern_strings = _split_pattern_segments(body)
    if not pattern_strings:
        raise ShapeCodeParseError("no patterns in shape code list", 0)
    return tuple(_parse_single_pattern(p) for p in pattern_strings)


def _extract_list_body(raw: str) -> str:
    s = raw.strip()
    if not s:
        raise ShapeCodeParseError("empty shape code", 0)
    opens = s.startswith("[")
    closes = s.endswith("]")
    if opens ^ closes:
        raise ShapeCodeParseError("mismatched brackets", 0)
    if opens:
        inner = s[1:-1].strip()
        if not inner:
            raise ShapeCodeParseError("empty bracket list", 1)
        if "[" in inner or "]" in inner:
            bad = next(i for i, ch in enumerate(inner) if ch in "[]")
            raise ShapeCodeParseError("nested or stray brackets are not allowed", bad + 1)
        return inner
    if "[" in s or "]" in s:
        bad = s.index("[") if "[" in s else s.index("]")
        raise ShapeCodeParseError("unexpected bracket", bad)
    return s


def _split_pattern_segments(body: str) -> list[str]:
    parts = [p.strip() for p in body.split(",")]
    segments = [p for p in parts if p]
    if len(segments) != len(parts):
        raise ShapeCodeParseError("empty pattern segment in list", 0)
    return segments


def _parse_single_pattern(raw_pattern: str) -> NormalizedShapePattern:
    raw_code = raw_pattern.strip()
    if not raw_code:
        raise ShapeCodeParseError("empty pattern", 0)
    layer_specs = [lay.strip() for lay in raw_code.split(":")]
    if any(not lay for lay in layer_specs):
        raise ShapeCodeParseError("empty layer in pattern", 0)

    layers: list[NormalizedShapeLayer] = []
    for layer_index, layer_str in enumerate(layer_specs):
        cells = _parse_layer(layer_index, layer_str)
        layers.append(NormalizedShapeLayer(layer_index=layer_index, cells=cells))

    normalized_code = ":".join(_layer_to_code(lyr) for lyr in layers)
    return NormalizedShapePattern(
        raw_code=raw_code,
        normalized_code=normalized_code,
        layers=tuple(layers),
    )


def _layer_to_code(layer: NormalizedShapeLayer) -> str:
    return "".join(c.raw_token for c in layer.cells)


def _parse_layer(layer_index: int, layer_str: str) -> tuple[NormalizedShapeCell, ...]:
    if len(layer_str) != 8:
        raise ShapeCodeParseError(
            f"layer {layer_index} must be 8 characters (four tokens), got {len(layer_str)}",
            None,
        )

    cells: list[NormalizedShapeCell] = []
    for q in range(4):
        token = layer_str[q * 2 : q * 2 + 2]
        shape_ch = token[0]
        color_ch = token[1]
        sk = _require_shape(shape_ch, layer_index, q)
        ck = _require_color(color_ch, layer_index, q)
        _validate_token_pair(layer_index, q, token, sk, ck)
        position = quadrant_at_index(q)
        cells.append(
            NormalizedShapeCell(
                quadrant_index=q,
                position=position,
                shape_code=shape_ch,
                color_code=color_ch,
                shape_kind=sk.solver_kind,
                color_kind=ck.solver_kind,
                raw_token=token,
            )
        )
    return tuple(cells)


def _require_shape(shape_ch: str, layer_index: int, quadrant: int) -> ShapeKind:
    sk = SHAPE_KINDS.get(shape_ch)
    if sk is None:
        raise ShapeCodeParseError(
            f"unknown shape code {shape_ch!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
    return sk


def _require_color(color_ch: str, layer_index: int, quadrant: int) -> ColorKind:
    ck = COLOR_KINDS.get(color_ch)
    if ck is None:
        raise ShapeCodeParseError(
            f"unknown color code {color_ch!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
    return ck


def _validate_token_pair(
    layer_index: int,
    quadrant: int,
    token: str,
    sk: ShapeKind,
    ck: ColorKind,
) -> None:
    if sk.empty != ck.empty:
        raise ShapeCodeParseError(
            f"shape/color emptiness mismatch for token {token!r} "
            f"in layer {layer_index} quadrant {quadrant}",
            None,
        )
    if sk.empty:
        return
    if not sk.colorable and ck.code != "u":
        raise ShapeCodeParseError(
            f"shape {sk.code!r} is not colorable; only uncolored (u) is allowed, "
            f"got {token!r} in layer {layer_index} quadrant {quadrant}",
            None,
        )
