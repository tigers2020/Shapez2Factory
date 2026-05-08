from __future__ import annotations

import base64
import gzip
import json
from typing import Any, cast

import pytest

from django_apps.shapez_core.services.shapez_copy_decode import (
    SHAPEZ2_COPY_PREFIX_V4,
    ShapezCopyDecodeError,
    decode_shapez2_copy,
    decode_shapez2_copy_trace,
)


def _encode_copy(obj: object) -> str:
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(body)
    b64 = base64.b64encode(compressed).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


def test_decode_round_trip_minimal_island_like() -> None:
    data = {"V": 1137, "BP": {"$type": "Island", "Icon": "x", "Entries": []}}
    code = _encode_copy(data)
    assert decode_shapez2_copy(code) == data


def test_decode_whitespace_in_string() -> None:
    data = {"V": 1, "BP": {}}
    inner = _encode_copy(data)
    b64_part = inner.removeprefix(SHAPEZ2_COPY_PREFIX_V4)
    chunks = [b64_part[:10], b64_part[10:20], b64_part[20:]]
    messy = f"  \n {SHAPEZ2_COPY_PREFIX_V4}  \t " + " \n ".join(chunks) + "  "
    assert decode_shapez2_copy(messy) == data


def test_rejects_non_string() -> None:
    with pytest.raises(ShapezCopyDecodeError, match="must be a string"):
        decode_shapez2_copy(cast(Any, None))


def test_rejects_wrong_prefix() -> None:
    with pytest.raises(ShapezCopyDecodeError, match="must start with"):
        decode_shapez2_copy("OTHER-xxx")


def test_rejects_invalid_base64() -> None:
    with pytest.raises(ShapezCopyDecodeError, match="invalid base64"):
        decode_shapez2_copy(f"{SHAPEZ2_COPY_PREFIX_V4}@@@@")


def test_rejects_non_gzip_after_base64() -> None:
    raw = b"not gzip"
    b64 = base64.b64encode(raw).decode("ascii")
    with pytest.raises(ShapezCopyDecodeError, match="not gzip payload"):
        decode_shapez2_copy(f"{SHAPEZ2_COPY_PREFIX_V4}{b64}")


def test_rejects_gzip_but_not_json() -> None:
    compressed = gzip.compress(b"not json {")
    b64 = base64.b64encode(compressed).decode("ascii")
    with pytest.raises(ShapezCopyDecodeError, match="invalid json"):
        decode_shapez2_copy(f"{SHAPEZ2_COPY_PREFIX_V4}{b64}")


def test_rejects_json_array_top_level() -> None:
    compressed = gzip.compress(b"[1,2]")
    b64 = base64.b64encode(compressed).decode("ascii")
    with pytest.raises(ShapezCopyDecodeError, match="expected JSON object"):
        decode_shapez2_copy(f"{SHAPEZ2_COPY_PREFIX_V4}{b64}")


def test_decode_trace_success_step_ids() -> None:
    data = {"V": 1137, "BP": {"$type": "Island", "Icon": "x", "Entries": []}}
    code = _encode_copy(data)
    trace = decode_shapez2_copy_trace(code)
    assert trace.success is True
    assert trace.data == data
    ids = [s["id"] for s in trace.steps]
    assert ids[0] == "normalize_whitespace"
    assert ids[-1] == "validate_top_level_object"
    assert all(s.get("ok") is True for s in trace.steps)


def test_decode_trace_invalid_base64_partial_steps() -> None:
    trace = decode_shapez2_copy_trace(f"{SHAPEZ2_COPY_PREFIX_V4}@@@@YYYY")
    assert trace.success is False
    assert trace.error == "invalid base64 payload"
    assert trace.steps[-1]["id"] == "base64_decode"
    assert trace.steps[-1]["ok"] is False
