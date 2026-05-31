"""``CopyDecodePort`` ??decode a shapez2 copy string into a pure payload.

The full decoded-map DTO lands in PR-CLI-2a; ``DecodedCopy`` below is a minimal placeholder so the
port type-checks while the use case is still a stub.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class DecodedCopy:
    """Placeholder decoded copy payload; full DTO lands in PR-CLI-2a."""

    raw: dict[str, Any] = field(default_factory=dict)


class CopyDecodePort(Protocol):
    def decode(self, copy_text: str) -> DecodedCopy: ...


__all__ = ["CopyDecodePort", "DecodedCopy"]
