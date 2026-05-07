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


def test_decode_accepts_trailing_non_base64_after_payload() -> None:
    data = {"V": 1, "BP": {}}
    code = _encode_copy(data) + "$"
    assert decode_shapez2_copy(code) == data
