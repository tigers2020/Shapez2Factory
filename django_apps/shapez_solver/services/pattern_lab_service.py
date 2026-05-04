from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.factory_demand import (
    UnsupportedFactoryDemandError,
    compute_factory_batch,
    inventory_search_goal_shape_code,
)
from django_apps.shapez_solver.domain.inventory_state import InventoryState
from django_apps.shapez_solver.services.macro_action_generator import (
    CatalogBackedMacroActionGenerator,
    MacroInventorySearchRequestView,
)
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
class PatternLabMacroResult:
    """DB macro 후보와 Python strategy dry-run 결과."""

    candidate: PatternMacroCandidate
    can_generate: bool
    generated_macro_kinds: tuple[str, ...]
    primitive_step_count: int


@dataclass(frozen=True, slots=True)
class PatternLabAnalysis:
    """Pattern Lab 화면에 표시할 분석 결과."""

    input_shape_code: str
    canonical_code: str
    inventory_goal_code: str
    signature: str
    inventory_signature: str
    symbol_map: tuple[SymbolMapEntry, ...]
    rotation_variants: tuple[RotationVariant, ...]
    distinct_part_count: int
    target_count: int | None
    source_counts: dict[str, int]
    db_candidates: tuple[PatternMacroCandidate, ...]
    macro_results: tuple[PatternLabMacroResult, ...]
    warnings: tuple[str, ...] = ()
    error: str = ""


def analyze_pattern_lab_shape(
    shape_code: str,
    *,
    repository: PatternCatalogRepository | None = None,
    macro_generator: CatalogBackedMacroActionGenerator | None = None,
) -> PatternLabAnalysis:
    """shape code를 pattern catalog와 macro strategy 관점에서 분석한다."""

    normalized_input = shape_code.strip()
    if not normalized_input:
        return _error_result(shape_code, "Shape code is empty.")

    try:
        patterns = parse_shape_code_list(normalized_input)
    except ShapeCodeParseError as exc:
        return _error_result(normalized_input, str(exc))

    target_shape = shape_from_pattern(patterns[0])
    canonical_code = target_shape.canonical_code
    warnings = []
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
    inventory_goal_code = inventory_search_goal_shape_code(target_shape)
    inventory_signature = pattern_signature(inventory_goal_code)
    source_counts: dict[str, int] = {}
    target_count = None
    try:
        batch = compute_factory_batch(target_shape)
        target_count = batch.target_count
        source_counts = dict(batch.base_source_counts)
    except UnsupportedFactoryDemandError as exc:
        warnings.append(f"Factory batch unsupported: {exc}")

    repo = repository or PatternCatalogRepository()
    candidates = repo.find_macro_candidates(signature=inventory_signature)
    generator = macro_generator or CatalogBackedMacroActionGenerator(repository=repo)
    macro_results = _build_macro_results(
        candidates=candidates,
        generator=generator,
        target_code=inventory_goal_code,
        target_count=target_count,
        source_counts=source_counts,
    )

    return PatternLabAnalysis(
        input_shape_code=normalized_input,
        canonical_code=canonical_code,
        inventory_goal_code=inventory_goal_code,
        signature=signature,
        inventory_signature=inventory_signature,
        symbol_map=_build_symbol_map(canonical_code),
        rotation_variants=_build_rotation_variants(canonical_code),
        distinct_part_count=len({entry.token for entry in _build_symbol_map(canonical_code)}),
        target_count=target_count,
        source_counts=source_counts,
        db_candidates=candidates,
        macro_results=macro_results,
        warnings=tuple(warnings),
    )


def _build_macro_results(
    *,
    candidates: tuple[PatternMacroCandidate, ...],
    generator: CatalogBackedMacroActionGenerator,
    target_code: str,
    target_count: int | None,
    source_counts: dict[str, int],
) -> tuple[PatternLabMacroResult, ...]:
    if target_count is None or not source_counts:
        return tuple(
            PatternLabMacroResult(
                candidate=candidate,
                can_generate=False,
                generated_macro_kinds=(),
                primitive_step_count=0,
            )
            for candidate in candidates
        )

    request = MacroInventorySearchRequestView(
        target_code=target_code,
        target_count=target_count,
        source_counts=source_counts,
    )
    state = InventoryState.from_counts(source_counts)
    actions = generator.generate(state, request)
    action_by_kind = {action.macro_kind: action for action in actions}
    return tuple(
        PatternLabMacroResult(
            candidate=candidate,
            can_generate=candidate.strategy_code in action_by_kind,
            generated_macro_kinds=tuple(action_by_kind),
            primitive_step_count=(
                len(action_by_kind[candidate.strategy_code].primitive_chain or ())
                if candidate.strategy_code in action_by_kind
                else 0
            ),
        )
        for candidate in candidates
    )


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
        inventory_goal_code="",
        signature="",
        inventory_signature="",
        symbol_map=(),
        rotation_variants=(),
        distinct_part_count=0,
        target_count=None,
        source_counts={},
        db_candidates=(),
        macro_results=(),
        warnings=warnings,
        error=error,
    )


__all__ = [
    "PatternLabAnalysis",
    "PatternLabMacroResult",
    "RotationVariant",
    "SymbolMapEntry",
    "analyze_pattern_lab_shape",
]
