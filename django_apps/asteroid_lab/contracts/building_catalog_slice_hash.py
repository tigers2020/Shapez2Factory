"""Shim: relocated to core ``building_catalog_slice_hash`` (PR-CLI-2a).

Core module: ``shapez2_factory.domain.asteroid_lab.building_catalog_slice_hash``.
Re-exports the pure core catalog slice hash so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.building_catalog_slice_hash import (
    catalog_slice_hash,
)

__all__ = ["catalog_slice_hash"]
