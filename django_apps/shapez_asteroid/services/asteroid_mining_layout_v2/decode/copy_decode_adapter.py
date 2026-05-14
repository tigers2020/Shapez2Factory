"""
STEP 0 — Shapez2 copy decode (``04_step0_decode.md`` §5).

Pipeline for string payloads (implemented in ``shapez_core.services.shapez_copy_decode``,
pure I/O + parse; **not** v1 ``asteroid_mining_layout``):

  ``SHAPEZ2-4-`` → Base64 → gzip → JSON object

This adapter only wraps that utility and ``DecodedBlueprintDocument``. It does **not**
run placement, routing, reconstruction, or existing-layout analysis (those are later steps).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedBlueprintDocument,
)
from django_apps.shapez_core.services.shapez_copy_decode import (
    ShapezCopyDecodeError,
    decode_shapez2_copy,
)


def decode_copy_payload(payload: str | Mapping[str, Any]) -> DecodedBlueprintDocument:
    """Decode a ``SHAPEZ2-4-`` copy string or wrap an already-decoded blueprint ``dict``.

    Mapping payloads skip Base64/gzip (caller-supplied JSON root). Returns a shallow
    read-only view via ``document``; use ``as_mutable_dict()`` for an owned copy.
    """

    if isinstance(payload, str):
        data = decode_shapez2_copy(payload)
    elif isinstance(payload, Mapping):
        data = dict(payload)
    else:
        msg = "payload must be str or a mapping of blueprint JSON"
        raise TypeError(msg)
    if not isinstance(data, dict):
        msg = "decoded top-level JSON must be an object"
        raise TypeError(msg)
    return DecodedBlueprintDocument(_root=data)


__all__ = ["ShapezCopyDecodeError", "decode_copy_payload"]
