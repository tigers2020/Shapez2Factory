"""
STEP 0: Shapez2 copy string or JSON fixture → normalized decoded document.

Uses ``shapez_core.services.shapez_copy_decode`` (pure; not v1 mining layout).
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

    Returns a shallow read-only view (``document``); use ``as_mutable_dict()`` for a copy.
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
