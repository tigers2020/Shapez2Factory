"""Decode Shapez 2 in-game copy strings (blueprint / island payload).

Pipeline: ``SHAPEZ2-4-`` prefix removal → Base64 → gzip → JSON object.

Decoded ``BP.Entries`` ``X``/``Y``/``R`` are island-local (omitted → ``0``). Not
asteroid world coordinates — see
``documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md``.
"""

from __future__ import annotations

import base64
import binascii
import gzip
import json
from dataclasses import dataclass
from typing import Any

SHAPEZ2_COPY_PREFIX_V4 = "SHAPEZ2-4-"
_GZIP_MAGIC = b"\x1f\x8b"
_BASE64_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")


class ShapezCopyDecodeError(ValueError):
    """Invalid copy string, payload, compression, or JSON."""


@dataclass(frozen=True)
class DecodeTraceResult:
    """Result of :func:`decode_shapez2_copy_trace` (success or failure with partial steps)."""

    success: bool
    data: dict[str, Any] | None
    steps: list[dict[str, Any]]
    error: str | None


def decode_shapez2_copy_trace(
    code: str,
    *,
    prefix: str = SHAPEZ2_COPY_PREFIX_V4,
) -> DecodeTraceResult:
    """Decode like :func:`decode_shapez2_copy` but record pipeline steps for UI playback."""

    steps: list[dict[str, Any]] = []

    def push(
        step_id: str,
        ok: bool = True,
        *,
        detail: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        row: dict[str, Any] = {"id": step_id, "ok": ok}
        if detail is not None:
            row["detail"] = detail
        if error is not None:
            row["error"] = error
        steps.append(row)

    def fail(message: str, step_id: str) -> DecodeTraceResult:
        push(step_id, ok=False, error=message)
        return DecodeTraceResult(False, None, steps, message)

    if not isinstance(code, str):
        return fail("copy code must be a string", "validate_input_type")

    normalized = "".join(code.split())
    push(
        "normalize_whitespace",
        detail={"chars_in": len(code), "chars_out": len(normalized)},
    )

    if not normalized:
        return fail("copy code is empty", "check_non_empty")

    if not normalized.startswith(prefix):
        return fail(f"copy code must start with {prefix!r}", "check_prefix")

    push("check_prefix", detail={"prefix": prefix})

    payload = normalized.removeprefix(prefix)
    if not payload:
        return fail("missing payload after prefix", "extract_payload")

    push("extract_payload", detail={"payload_chars": len(payload)})

    payload = _trim_trailing_non_base64(payload)
    if not payload:
        return fail("invalid base64 payload", "trim_base64")

    push("trim_base64", detail={"payload_chars": len(payload)})

    padded = _pad_base64(payload)
    push("pad_base64", detail={"padded_chars": len(padded)})

    try:
        raw = base64.b64decode(padded, validate=True)
    except binascii.Error:
        return fail("invalid base64 payload", "base64_decode")

    push("base64_decode", detail={"bytes": len(raw)})

    if not raw.startswith(_GZIP_MAGIC):
        return fail("not gzip payload", "verify_gzip_magic")

    push("verify_gzip_magic", detail={"magic_ok": True})

    try:
        decompressed = gzip.decompress(raw)
    except (OSError, EOFError):
        return fail("gzip decompress failed", "gzip_decompress")

    push(
        "gzip_decompress",
        detail={"compressed_bytes": len(raw), "decompressed_bytes": len(decompressed)},
    )

    try:
        text = decompressed.decode("utf-8")
    except UnicodeDecodeError:
        return fail("gzip payload is not valid utf-8", "utf8_decode")

    push("utf8_decode", detail={"chars": len(text)})

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return fail("invalid json", "json_parse")

    push("json_parse", detail={"value_type": type(data).__name__})

    if not isinstance(data, dict):
        return fail("expected JSON object at top level", "validate_top_level_object")

    keys_sample = list(data.keys())[:12]
    push("validate_top_level_object", detail={"keys": keys_sample, "key_count": len(data)})
    return DecodeTraceResult(True, data, steps, None)


def decode_shapez2_copy(code: str, *, prefix: str = SHAPEZ2_COPY_PREFIX_V4) -> dict[str, Any]:
    """Decode a Shapez 2 copy code into a JSON object (``dict``).

    Whitespace anywhere in the input is ignored. Only a top-level JSON object is accepted.
    """

    trace = decode_shapez2_copy_trace(code, prefix=prefix)
    if not trace.success:
        raise ShapezCopyDecodeError(trace.error or "decode failed")
    assert trace.data is not None
    return trace.data


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
