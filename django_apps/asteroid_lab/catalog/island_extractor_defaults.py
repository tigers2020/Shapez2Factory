"""Canonical in-game island blueprints for shape/fluid extractor variants.

Source: player-provided ``SHAPEZ2-4-`` copy strings (2026-05-23).
Both shape variants use top-level ``Layout_ShapeMiner``; behavior differs in nested
``B.Entries`` (balance: 12-line belt distribution; omni: fragment reassembly chain).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy

# Game paste convention: trailing ``$`` is optional in storage.
_COPY_BALANCE_SHAPE = (
    "SHAPEZ2-4-H4sIAM3VEWoA/6xaW2vbMBT+L2KPeYhsy5bzGNpBIYWSdmVjlGESpzPz7KA460rpf5"
    "/T2IlvcnQ+jUJL23w696v0xh7ZjHM3mLD5HZu9sU/F6zZmM3azS6NszSbsZpVnh39cRUXEZt9ZUv4"
    "+u0ujYpOr3zs2yfZpevzGdj+jbTxb7o9f7Ol9wq6zQiXxrgS+sYfy2EX0mu+LH/eHT94mWaxKCvMm3"
    "fk+SddJ9vxfKX8tZSwl/HYQdfLBxzxOi7tcFfdxto7VTVbEKovSx0glUVaw90kTI+mQA5lF+QMih"
    "gErkg5KEgCGAJdTiAyokimKDFGVVCQpSP9kvmULeBVvon1aLOJN0UHeJkrlKl53Tph+nOAeT1gkm8"
    "L5sjVAaySuyH/O1Uuk1hredUJTwF6T7eu/hYpWRa6qEzTQsKmzjn2X8SpO/ugN5Wsi1IjnNtrB0N"
    "KGtMQoO0e+yTheEz3byFTR3MJIDu4bNV13iOfRSAxhWf06hs6S6gOwDZLmcV8DZbcsmaeK0Drm6G"
    "qVFrYUJ6KLlmb5Vf6SzaPVrzHf9ZocUz1fDoj7QdkoqYYDfJvVEW8EaRg1hjwPBMyR5BIqYCPwC3"
    "wL7QGmpg4GBL+N1XOsnIecL8YZ95oUDR3zLDPJqcQAxcpARhKKZoYxZPXoyAEUBJVHBRgM4bZyRn"
    "+oaBgkb4RkCFKUuJCiJglnNd8iqfndOjWeH8I+s5RU5uOZzJDRbvI9+5BFPvMt05lvm81awuuT2f"
    "AwIOCc5mMdIhQGrm2awJoK1x5rWGl6nulSTNuvbiePovRfncUCvZH3TvoCWjePUuUapKDQDS/CL"
    "8gqRw8gjrUjRxjP5cGw2S4PCX4P7kCFRiBWFxSji37GMgOeUh21MHE90CwWhJV/Ckv3FNbeKajO"
    "2StNJzgnZ6Lz6oW8FwhOW4yhA8xj61x5FnYnoJqo6wiuivoEsi66udaButAz9W4ddMtKdnEuQPZf"
    "vDHIuBZ7Ug9NGMNI81UWIrQ7jh6zr2vXNlR4i77BxSpYL9S89jmAnwb9hmvMTf3BuwqzxXJIA4ke"
    "KYJihGbDauAcosusMUbilpTD9zlGkRBaYKXmOohAGARLmwsSv5/hsb0YLUsHTa+qQPfbNCnKT/O"
    "H3L14F4QsTGWTU3BXS4qAkFpNen05IaMEjcjhRI2GtG2N7IMotwpt+0GXC45FXzbVpKULVXKqy6"
    "KmoY2lIqR/CYG+YwpgHKAo+Lo4Mr2ZRKyGpfSGyfFeEnhZ4OuBhvehU5ToMNK4K1lQh802WQcRFn"
    "hHwdF3FNLiHUNogW25sWPTXDhWMQDe7QD3zxWSeN1dteKgkj0bsBgFG7W8RyQ8wrhIKW8JzW2E5"
    "rDQ9nObtMACbcx5bCX1WvWYbrGwrY8A32HV8/rUJkBQtBhH04bRU6xA+wpwgGgrgFspgNsrgOMKo"
    "A5eteTQ9g9q958mbJ5kkXp9jNUuObzSPTwhftf+/Z8AAwBWt5RIZiwAAA=="
)
_COPY_OMNI_SHAPE = (
    "SHAPEZ2-4-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"
)
_COPY_FLUID = (
    "SHAPEZ2-4-H4sIAG/WEWoA/6yXX2uDMBTFv8tljz4saozzsWyFjhakG2VjlBFqugVsLDEySul3"
    "n9bqbOkfcxmCoObn9eTcHMkWZhAR4jEHBjFEW7gzm7WACEZ5ylUCDowWmaoePHLDIfoAWV5Hc"
    "crNMtOrHBxVpGl9gvybr0U0LeoD5jsHnpTRUuQluIXX8rVjvskK8zlMC5lMpBK6rDDo1h0UMk"
    "2k+vrXym+VRgfeIaIOTCHynP3HxMVq/SiWvEjNSBmhFU9nXEuuDOycmnJRlIeifBRV6/KPKLk"
    "WY7E8RSZS60yL5ERcjZI/9LlQCyMzdV2dNebjMNpgDTDM9A/XyaXxwen4PjMRdKaeWJYKUBRD"
    "UeEpdUZci7AGqQbvV1ycafMiVCL0dZPIsUt9G94ac3EYwWEHbQSnjeC0EZw2HBai0i1EpVuIS"
    "rcQlW4Mn24Ml24Ml24Ml27MThk9nwU3EqSmHmwSJGiQniVYd3zPxDk0vGvzXW6X8Wy9ted8JE"
    "dbro8q2l36nqWv5B6zRoKWtXK4AewspgiLKdJiirSYIi2mlj/yLnB7BRLfsicOmIfDXBxGMB3"
    "IWrZPQ83L3YJUXG9mQuey2h5Ue5fdxfu/AgwAQY60Kd8MAAA="
)


class IslandExtractorVariantKey(StrEnum):
    """Stable keys for DB seed and application lookup."""

    SHAPE_BALANCE = "shape_balance"
    SHAPE_OMNI = "shape_omni"
    FLUID_DEFAULT = "fluid_default"


class IslandExtractorCarrierKind(StrEnum):
    SHAPE = "shape"
    FLUID = "fluid"


@dataclass(frozen=True, slots=True)
class IslandExtractorDefaultRecord:
    variant_key: IslandExtractorVariantKey
    carrier_kind: IslandExtractorCarrierKind
    display_name: str
    summary_ko: str
    layout_t: str
    copy_code: str
    metadata_json: dict[str, Any]


def _inner_entries(copy_code: str) -> list[dict[str, Any]]:
    root = decode_shapez2_copy(copy_code.strip().rstrip("$"))
    top = root["BP"]["Entries"][0]
    block = top.get("B")
    if not isinstance(block, dict):
        msg = "expected nested Building block on island extractor blueprint"
        raise ValueError(msg)
    entries = block.get("Entries")
    if not isinstance(entries, list):
        msg = "expected B.Entries list"
        raise ValueError(msg)
    return [e for e in entries if isinstance(e, dict)]


def inner_building_type_counts(copy_code: str) -> dict[str, int]:
    """Count internal ``T`` strings (nested island building layout)."""

    counts = Counter(str(e.get("T", "")) for e in _inner_entries(copy_code))
    return dict(sorted(counts.items()))


def inner_entry_fingerprint(copy_code: str) -> str:
    """Stable SHA-256 hex digest of sorted internal type counts (regression guard)."""

    payload = json.dumps(inner_building_type_counts(copy_code), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def default_record(key: IslandExtractorVariantKey) -> IslandExtractorDefaultRecord:
    for row in ISLAND_EXTRACTOR_DEFAULTS:
        if row.variant_key == key:
            return row
    msg = f"unknown island extractor variant: {key}"
    raise KeyError(msg)


ISLAND_EXTRACTOR_DEFAULTS: Final[tuple[IslandExtractorDefaultRecord, ...]] = (
    IslandExtractorDefaultRecord(
        variant_key=IslandExtractorVariantKey.SHAPE_BALANCE,
        carrier_kind=IslandExtractorCarrierKind.SHAPE,
        display_name="Shape balance extractor",
        summary_ko="12개 라인에 도형을 균등 분배하는 벨런스 추출기.",
        layout_t="Layout_ShapeMiner",
        copy_code=_COPY_BALANCE_SHAPE,
        metadata_json={
            "output_line_count": 12,
            "discriminator": "belt_port_sender_heavy",
        },
    ),
    IslandExtractorDefaultRecord(
        variant_key=IslandExtractorVariantKey.SHAPE_OMNI,
        carrier_kind=IslandExtractorCarrierKind.SHAPE,
        display_name="Shape omni extractor",
        summary_ko="조각난 도형을 본 형태로 복원해보내는 옴니 추출기.",
        layout_t="Layout_ShapeMiner",
        copy_code=_COPY_OMNI_SHAPE,
        metadata_json={
            "discriminator": "processing_chain_heavy",
        },
    ),
    IslandExtractorDefaultRecord(
        variant_key=IslandExtractorVariantKey.FLUID_DEFAULT,
        carrier_kind=IslandExtractorCarrierKind.FLUID,
        display_name="Fluid extractor",
        summary_ko="액체(펌프) 추출기 기본 단일 버전.",
        layout_t="Layout_FluidMiner",
        copy_code=_COPY_FLUID,
        metadata_json={},
    ),
)

# Regression fingerprints (computed once at import; tied to copy strings above).
EXPECTED_INNER_FINGERPRINTS: Final[dict[IslandExtractorVariantKey, str]] = {
    row.variant_key: inner_entry_fingerprint(row.copy_code) for row in ISLAND_EXTRACTOR_DEFAULTS
}
