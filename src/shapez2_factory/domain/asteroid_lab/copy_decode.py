"""Shapez 2 v4 copy-string decode — pure bytes/JSON only (A3 boundary).

Pipeline matches the public Shapez 2 copy pipeline (whitespace strip, prefix,
base64, gzip, UTF-8 JSON object) implemented elsewhere in this repo, but **no**
decode module is imported here so the core pipeline stays decoupled.

``BP.Entries`` coordinates are island-local blueprint cells (omitted ``X``/``Y``/``R`` → ``0``).
"""

from __future__ import annotations

import base64
import binascii
import gzip
import json

from shapez2_factory.domain.asteroid_lab.service_dtos import RawDecodedBlueprintDTO
from shapez2_factory.domain.asteroid_lab.wire_coerce import wire_dict, wire_list

SHAPEZ2_COPY_PREFIX_V4 = "SHAPEZ2-4-"
_GZIP_MAGIC = b"\x1f\x8b"
_BASE64_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")


class AsteroidLabCopyDecodeError(ValueError):
    """Invalid copy string, payload, compression, JSON, or blueprint shape."""


def decode_copy_string(copy_code: str) -> RawDecodedBlueprintDTO:
    """Decode a ``SHAPEZ2-4-`` copy string into a validated blueprint root dict."""

    if not isinstance(copy_code, str):
        raise AsteroidLabCopyDecodeError("copy code must be a string")

    normalized = "".join(copy_code.split())
    if not normalized:
        raise AsteroidLabCopyDecodeError("copy code is empty")

    if not normalized.startswith(SHAPEZ2_COPY_PREFIX_V4):
        raise AsteroidLabCopyDecodeError(f"copy code must start with {SHAPEZ2_COPY_PREFIX_V4!r}")

    payload = normalized.removeprefix(SHAPEZ2_COPY_PREFIX_V4)
    if not payload:
        raise AsteroidLabCopyDecodeError("missing payload after prefix")

    payload = _trim_trailing_non_base64(payload)
    if not payload:
        raise AsteroidLabCopyDecodeError("invalid base64 payload")

    padded = _pad_base64(payload)
    try:
        raw = base64.b64decode(padded, validate=True)
    except binascii.Error as exc:
        raise AsteroidLabCopyDecodeError("invalid base64 payload") from exc

    if not raw.startswith(_GZIP_MAGIC):
        raise AsteroidLabCopyDecodeError("not gzip payload")

    try:
        decompressed = gzip.decompress(raw)
    except (OSError, EOFError) as exc:
        raise AsteroidLabCopyDecodeError("gzip decompress failed") from exc

    try:
        text = decompressed.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AsteroidLabCopyDecodeError("gzip payload is not valid utf-8") from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AsteroidLabCopyDecodeError("invalid json") from exc

    if not isinstance(data, dict):
        raise AsteroidLabCopyDecodeError("expected JSON object at top level")

    _validate_blueprint_shape(data)
    return RawDecodedBlueprintDTO(root=data)


def _validate_blueprint_shape(data: dict[str, object]) -> None:
    if "V" not in data:
        raise AsteroidLabCopyDecodeError("missing top-level key 'V'")
    if not isinstance(data.get("BP"), dict):
        raise AsteroidLabCopyDecodeError("missing or invalid 'BP' object")
    bp = wire_dict(data.get("BP"), field="BP")
    if "$type" not in bp:
        raise AsteroidLabCopyDecodeError("missing BP['$type']")
    if not isinstance(bp.get("$type"), str):
        raise AsteroidLabCopyDecodeError("BP['$type'] must be a string")
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        raise AsteroidLabCopyDecodeError("missing or invalid BP['Entries'] list")
    _ = wire_list(entries, field="BP.Entries")


def _trim_trailing_non_base64(payload: str) -> str:
    end = len(payload)
    while end > 0 and payload[end - 1] not in _BASE64_ALPHABET:
        end -= 1
    return payload[:end]


def _pad_base64(data: str) -> str:
    missing = (-len(data)) % 4
    return data + ("=" * missing)


def encode_copy_string(root: dict[str, object]) -> str:
    """Encode a blueprint root dict to a ``SHAPEZ2-4-`` copy string (gzip + base64)."""

    _validate_blueprint_shape(root)
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


__all__ = [
    "SHAPEZ2_COPY_PREFIX_V4",
    "AsteroidLabCopyDecodeError",
    "decode_copy_string",
    "encode_copy_string",
]
