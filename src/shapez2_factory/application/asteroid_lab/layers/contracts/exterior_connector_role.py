"""Layer 02 exterior connector role (required vs spare)."""

from __future__ import annotations

from enum import StrEnum


class ExteriorConnectorRole(StrEnum):
    REQUIRED = "required"
    SPARE = "spare"


__all__ = ["ExteriorConnectorRole"]
