"""Parse Core.Localization.LazyLocalizedText snapshots from game dumps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_BACKING_FIELD_SUFFIX = "k__BackingField"


@dataclass(frozen=True)
class LazyLocalizedReplacement:
    replacement_key: str
    value_kind: str
    nested_message_key: str
    value_preview: str


@dataclass(frozen=True)
class ParsedLazyLocalizedText:
    message_key: str
    lazy_text_type: str
    placeholder_resolver_type: str
    is_cycle_reference: bool
    cycle_reference: str
    replacements: tuple[LazyLocalizedReplacement, ...]
    unknown_top_level_keys: tuple[str, ...]


def _extract_message_key(id_block: Any) -> str:
    if id_block is None:
        return ""
    if isinstance(id_block, str):
        return id_block.strip()
    if not isinstance(id_block, dict):
        return ""
    for key, value in id_block.items():
        if _BACKING_FIELD_SUFFIX in key and isinstance(value, str):
            return value.strip()
    nested = id_block.get("Id")
    if nested is not None:
        return _extract_message_key(nested)
    return ""


def _parse_replacements(resolver: dict[str, Any]) -> tuple[LazyLocalizedReplacement, ...]:
    raw = resolver.get("Replacements")
    if not isinstance(raw, dict) or not raw:
        return ()
    out: list[LazyLocalizedReplacement] = []
    for key, value in raw.items():
        nested_key = ""
        preview = ""
        if isinstance(value, dict):
            nested_key = _extract_message_key(value.get("Id"))
            preview = repr(value)[:500]
        elif value is not None:
            preview = repr(value)[:500]
        out.append(
            LazyLocalizedReplacement(
                replacement_key=str(key),
                value_kind=type(value).__name__,
                nested_message_key=nested_key,
                value_preview=preview,
            )
        )
    return tuple(out)


def parse_lazy_localized_text(raw: Any) -> ParsedLazyLocalizedText | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        return ParsedLazyLocalizedText(
            message_key=text,
            lazy_text_type="",
            placeholder_resolver_type="",
            is_cycle_reference=False,
            cycle_reference="",
            replacements=(),
            unknown_top_level_keys=(),
        )
    if not isinstance(raw, dict):
        return None

    known = {"Id", "PlaceholderResolver", "$type", "$cycle"}
    unknown = tuple(sorted(k for k in raw if k not in known))

    if "$cycle" in raw and set(raw.keys()) <= {"$cycle"}:
        cycle_ref = str(raw["$cycle"])
        return ParsedLazyLocalizedText(
            message_key="",
            lazy_text_type="",
            placeholder_resolver_type="",
            is_cycle_reference=True,
            cycle_reference=cycle_ref,
            replacements=(),
            unknown_top_level_keys=unknown,
        )

    id_block = raw.get("Id")
    resolver = raw.get("PlaceholderResolver")
    resolver_dict = resolver if isinstance(resolver, dict) else {}
    replacements = _parse_replacements(resolver_dict)

    return ParsedLazyLocalizedText(
        message_key=_extract_message_key(id_block),
        lazy_text_type=str(raw.get("$type", "") or ""),
        placeholder_resolver_type=str(resolver_dict.get("$type", "") or ""),
        is_cycle_reference=False,
        cycle_reference="",
        replacements=replacements,
        unknown_top_level_keys=unknown,
    )
