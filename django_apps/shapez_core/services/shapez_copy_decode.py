"""Decode Shapez 2 in-game copy strings (blueprint / island payload).

Pipeline: ``SHAPEZ2-4-`` prefix removal → Base64 → gzip → JSON object.
"""

from __future__ import annotations

import base64
import binascii
import gzip
import json
from typing import Any

SHAPEZ2_COPY_PREFIX_V4 = "SHAPEZ2-4-"
_GZIP_MAGIC = b"\x1f\x8b"
_BASE64_ALPHABET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
)


class ShapezCopyDecodeError(ValueError):
    """Invalid copy string, payload, compression, or JSON."""


def decode_shapez2_copy(code: str, *, prefix: str = SHAPEZ2_COPY_PREFIX_V4) -> dict[str, Any]:
    """Decode a Shapez 2 copy code into a JSON object (``dict``).

    Whitespace anywhere in the input is ignored. Only a top-level JSON object is accepted.
    """

    if not isinstance(code, str):
        raise ShapezCopyDecodeError("copy code must be a string")

    normalized = "".join(code.split())
    if not normalized:
        raise ShapezCopyDecodeError("copy code is empty")

    if not normalized.startswith(prefix):
        raise ShapezCopyDecodeError(f"copy code must start with {prefix!r}")

    payload = normalized.removeprefix(prefix)
    if not payload:
        raise ShapezCopyDecodeError("missing payload after prefix")

    payload = _trim_trailing_non_base64(payload)
    if not payload:
        raise ShapezCopyDecodeError("invalid base64 payload")

    padded = _pad_base64(payload)
    try:
        raw = base64.b64decode(padded, validate=True)
    except binascii.Error as exc:
        raise ShapezCopyDecodeError("invalid base64 payload") from exc

    if not raw.startswith(_GZIP_MAGIC):
        raise ShapezCopyDecodeError("not gzip payload")

    try:
        decompressed = gzip.decompress(raw)
    except (OSError, EOFError) as exc:
        raise ShapezCopyDecodeError("gzip decompress failed") from exc

    try:
        text = decompressed.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ShapezCopyDecodeError("gzip payload is not valid utf-8") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ShapezCopyDecodeError("invalid json") from exc

    if not isinstance(data, dict):
        raise ShapezCopyDecodeError("expected JSON object at top level")

    return data


def _trim_trailing_non_base64(payload: str) -> str:
    """Drop trailing characters outside standard Base64 (e.g. shell/editor ``$``)."""

    end = len(payload)
    while end > 0 and payload[end - 1] not in _BASE64_ALPHABET:
        end -= 1
    return payload[:end]


def _pad_base64(data: str) -> str:
    """Pad standard Base64 so length is a multiple of four."""

    missing = (-len(data)) % 4
    return data + ("=" * missing)
