"""Deterministic IVVD release seal (pure; no I/O)."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

SEAL_ALGORITHM = "shapez-ivvd-seal-v1"


def canonical_seal_payload_v1(
    *,
    game_version: int,
    documents: Sequence[tuple[str, str, int]],
) -> tuple[str, str]:
    """Return (canonical_json_utf8_string, sha256_hex).

    ``documents`` items are ``(source_relative_path, sha256_hex, byte_size)``.
    Sorted by ``source_relative_path`` ascending; duplicate paths must not occur.
    """

    sorted_docs = sorted(documents, key=lambda t: t[0])
    payload: dict[str, object] = {
        "algorithm_version": SEAL_ALGORITHM,
        "document_count": len(sorted_docs),
        "documents": [
            {"byte_size": sz, "sha256": h, "source_relative_path": p} for p, h, sz in sorted_docs
        ],
        "game_version": game_version,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return canonical, digest
