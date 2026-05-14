"""
Bridge to Shapez2 copy-code decode (STEP 0).

Implementation will call existing **non-solver** decode utilities after review.
This module must not import v1 ``asteroid_mining_layout`` packages.
"""

from __future__ import annotations

from typing import Any


def decode_copy_payload(_copy_string: str) -> dict[str, Any]:
    """Decode copy string to a JSON-like dict of blueprint entities (not implemented)."""
    msg = "decode_copy_payload is not implemented (skeleton only)"
    raise NotImplementedError(msg)
