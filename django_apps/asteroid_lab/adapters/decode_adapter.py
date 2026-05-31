"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.copy_decode`` (PR-CLI-2f)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.copy_decode import (
    SHAPEZ2_COPY_PREFIX_V4,
    AsteroidLabCopyDecodeError,
    decode_copy_string,
    encode_copy_string,
)

__all__ = [
    "SHAPEZ2_COPY_PREFIX_V4",
    "AsteroidLabCopyDecodeError",
    "decode_copy_string",
    "encode_copy_string",
]
