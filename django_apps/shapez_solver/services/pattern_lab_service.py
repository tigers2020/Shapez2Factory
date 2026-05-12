from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.domain.shape import Shape, ShapeLayer, ShapePart
from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.services.pattern_catalog_repository import (
    PatternCatalogRepository,
    PatternMacroCandidate,
)
from django_apps.shapez_solver.services.pattern_classifier import pattern_signature


@dataclass(frozen=True, slots=True)
class SymbolMapEntry:
    """symbolic signature 문자와 실제 shape token의 대응."""

    symbol: str
    token: str


@dataclass(frozen=True, slots=True)
class RotationVariant:
    """사분면 회전 variant와 해당 signature."""

    shape_code: str
    signature: str


@dataclass(frozen=True, slots=True)
class PatternLabAnalysis:
    """Pattern Lab 화면에 표시할 분석 결과."""

    input_shape_code: str
    canonical_code: str
    signature: str
    symbol_map: tuple[SymbolMapEntry, ...]
    rotation_variants: tuple[RotationVariant, ...]
    distinct_part_count: int
    db_candidates: tuple[PatternMacroCandidate, ...]
    warnings: tuple[str, ...] = ()
    error: str = ""


def analyze_pattern_lab_shape(
    shape_code: str,
    *,
    repository: PatternCatalogRepository | None = None,
) -> PatternLabAnalysis:
    """shape code를 pattern catalog 관점에서 분석한다."""

    normalized_input = shape_code.strip()
    if not normalized_input:
        return _error_result(shape_code, "Shape code is empty.")

    try:
        patterns = parse_shape_code_list(normalized_input)
    except ShapeCodeParseError as exc:
        return _error_result(normalized_input, str(exc))

    target_shape = shape_from_pattern(patterns[0])
    canonical_code = target_shape.canonical_code
    warnings: list[str] = []
    if len(patterns) > 1:
        warnings.append("Multiple patterns were provided; only the first pattern was analyzed.")
    if patterns[0].raw_code != patterns[0].normalized_code:
        warnings.append(
            f"Pattern '{patterns[0].raw_code}' was normalized to "
            f"'{patterns[0].normalized_code}'."
        )

    if not target_shape.is_single_layer():
        return _error_result(
            normalized_input,
            "Pattern Lab currently supports single-layer shape codes only.",
            canonical_code=canonical_code,
            warnings=tuple(warnings),
        )

    signature = pattern_signature(canonical_code)
    repo = repository or PatternCatalogRepository()
    candidates = repo.find_macro_candidates(signature=signature)
    symbol_map = _build_symbol_map(canonical_code)

    return PatternLabAnalysis(
        input_shape_code=normalized_input,
        canonical_code=canonical_code,
        signature=signature,
        symbol_map=symbol_map,
        rotation_variants=_build_rotation_variants(canonical_code),
        distinct_part_count=len({entry.token for entry in symbol_map}),
        db_candidates=candidates,
        warnings=tuple(warnings),
    )


def _paint_shape(shape: Shape, color: str) -> Shape:
    """레이어의 비어 있지 않은 사분면 색만 바꾼다 (무채색 골격 코드용)."""

    return Shape(
        layers=tuple(
            ShapeLayer(
                quadrants=(
                    (
                        layer.quadrants[0]
                        if layer.quadrants[0].is_empty
                        else ShapePart(
                            layer.quadrants[0].kind,
                            color,
                            layer.quadrants[0].material,
                        )
                    ),
                    (
                        layer.quadrants[1]
                        if layer.quadrants[1].is_empty
                        else ShapePart(
                            layer.quadrants[1].kind,
                            color,
                            layer.quadrants[1].material,
                        )
                    ),
                    (
                        layer.quadrants[2]
                        if layer.quadrants[2].is_empty
                        else ShapePart(
                            layer.quadrants[2].kind,
                            color,
                            layer.quadrants[2].material,
                        )
                    ),
                    (
                        layer.quadrants[3]
                        if layer.quadrants[3].is_empty
                        else ShapePart(
                            layer.quadrants[3].kind,
                            color,
                            layer.quadrants[3].material,
                        )
                    ),
                )
            )
            for layer in shape.layers
        )
    ).strip_top_empty_layers()


def _build_symbol_map(shape_code: str) -> tuple[SymbolMapEntry, ...]:
    tokens = _shape_tokens(shape_code)
    token_to_symbol: dict[str, str] = {}
    entries: list[SymbolMapEntry] = []
    for token in tokens:
        if token in token_to_symbol:
            continue
        symbol = chr(ord("A") + len(token_to_symbol))
        token_to_symbol[token] = symbol
        entries.append(SymbolMapEntry(symbol=symbol, token=token))
    return tuple(entries)


def _build_rotation_variants(shape_code: str) -> tuple[RotationVariant, ...]:
    tokens = _shape_tokens(shape_code)
    if len(tokens) != 4:
        return ()
    variants: list[RotationVariant] = []
    seen: set[str] = set()
    for offset in range(4):
        rotated = tokens[offset:] + tokens[:offset]
        variant_code = "".join(rotated)
        if variant_code in seen:
            continue
        seen.add(variant_code)
        variants.append(
            RotationVariant(
                shape_code=variant_code,
                signature=pattern_signature(variant_code),
            )
        )
    return tuple(variants)


MAX_PATTERN_FAMILY_LAYERS = 4


def _structural_family_mismatch_for_layer_code(
    layer_code: str,
    *,
    family_signature: str,
    allow_rotation: bool,
) -> str | None:
    """단일 레이어(8자)에 대해 family와 불일치 시 이유 문자열, 아니면 None."""
    fam_sig = (family_signature or "").strip()
    if not fam_sig:
        return None
    try:
        layer_patterns = parse_shape_code_list(layer_code.strip())
    except ShapeCodeParseError as exc:
        return f"parse error: {exc}"

    target_shape = shape_from_pattern(layer_patterns[0])
    if not target_shape.is_single_layer():
        return "multi-layer shape is not supported for pattern family check"

    canonical_code = target_shape.canonical_code
    structural_code = _paint_shape(target_shape, "u").canonical_code
    structural_sig = pattern_signature(structural_code)

    if not allow_rotation:
        if structural_sig != fam_sig:
            return f"structural pattern signature {structural_sig!r} != family {fam_sig!r}"
        return None

    acceptable: set[str] = {structural_sig}
    acceptable.update(v.signature for v in _build_rotation_variants(canonical_code))
    if fam_sig not in acceptable:
        return (
            f"pattern family {fam_sig!r} not in allowed signatures "
            f"{sorted(acceptable)!r} (structural {structural_sig!r}, rotation allowed)"
        )
    return None


def explain_pattern_family_mismatch(
    shape_code: str,
    *,
    family_signature: str,
    allow_rotation: bool,
) -> str | None:
    """
    canonical / 무채색 구조 코드 / 사분면 회전 variant로
    ``family_signature``와의 불일치를 설명한다. 일치하면 ``None``.

    - ``allow_rotation``이 거짓이면 구조 시그니처만 사용한다.
    - 참이면 구조 시그니처 및 ``_build_rotation_variants(canonical_code)``의
      시그니처 합집합에 ``family_signature``가 포함되는지 본다.
    - 다층(``:``) 코드는 레이어당 위 규칙을 적용. 레이어 수 최대
      ``MAX_PATTERN_FAMILY_LAYERS``.
    """
    fam_sig = (family_signature or "").strip()
    if not fam_sig:
        return None
    normalized = shape_code.strip()
    if not normalized:
        return None
    try:
        patterns = parse_shape_code_list(normalized)
    except ShapeCodeParseError as exc:
        return f"parse error: {exc}"

    target_shape = shape_from_pattern(patterns[0])
    layer_count = len(target_shape.layers)
    if layer_count > MAX_PATTERN_FAMILY_LAYERS:
        return f"multi-layer shape exceeds maximum of {MAX_PATTERN_FAMILY_LAYERS} layers"

    for layer_index, layer in enumerate(target_shape.layers):
        layer_code = "".join(f"{part.kind}{part.color}" for part in layer.quadrants)
        detail = _structural_family_mismatch_for_layer_code(
            layer_code,
            family_signature=fam_sig,
            allow_rotation=allow_rotation,
        )
        if detail:
            return f"layer {layer_index}: {detail}"
    return None


def _shape_tokens(shape_code: str) -> tuple[str, ...]:
    if ":" in shape_code:
        return ()
    return tuple(shape_code[index : index + 2] for index in range(0, len(shape_code), 2))


def _error_result(
    input_shape_code: str,
    error: str,
    *,
    canonical_code: str = "",
    warnings: tuple[str, ...] = (),
) -> PatternLabAnalysis:
    return PatternLabAnalysis(
        input_shape_code=input_shape_code,
        canonical_code=canonical_code,
        signature="",
        symbol_map=(),
        rotation_variants=(),
        distinct_part_count=0,
        db_candidates=(),
        warnings=warnings,
        error=error,
    )


__all__ = [
    "PatternLabAnalysis",
    "RotationVariant",
    "SymbolMapEntry",
    "analyze_pattern_lab_shape",
    "explain_pattern_family_mismatch",
]
