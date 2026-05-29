"""Idempotent CANON MiningExtractionRule rows for solver/runtime unit tests."""

from __future__ import annotations

from decimal import Decimal

from django_apps.game_data.models.mining import MiningExtractionRule

_CANON_ROWS: tuple[dict[str, object], ...] = (
    {
        "resource_kind": "shape",
        "transport_kind": "shape_belt",
        "mini_unit_output_per_min": Decimal("30.0000"),
        "output_unit": "shapes_per_min",
        "base_mini_units_per_miner": 4,
        "mini_units_per_extension": 4,
        "max_extension_count": 3,
        "source_kind": "CANON_MANUAL",
        "source_note": "test fixture (mirrors migration 0026 seed)",
        "is_active": True,
    },
    {
        "resource_kind": "fluid",
        "transport_kind": "fluid_pipe",
        "mini_unit_output_per_min": Decimal("300.0000"),
        "output_unit": "liters_per_min",
        "base_mini_units_per_miner": 4,
        "mini_units_per_extension": 4,
        "max_extension_count": 3,
        "source_kind": "CANON_MANUAL",
        "source_note": "test fixture (mirrors migration 0026 seed)",
        "is_active": True,
    },
)


def ensure_mining_extraction_canon_rules() -> None:
    """Restore active shape/fluid rules after parallel xdist or partial DB reuse."""

    for row in _CANON_ROWS:
        resource_kind = str(row["resource_kind"])
        MiningExtractionRule.objects.update_or_create(
            resource_kind=resource_kind,
            is_active=True,
            defaults={
                "transport_kind": row["transport_kind"],
                "mini_unit_output_per_min": row["mini_unit_output_per_min"],
                "output_unit": row["output_unit"],
                "base_mini_units_per_miner": row["base_mini_units_per_miner"],
                "mini_units_per_extension": row["mini_units_per_extension"],
                "max_extension_count": row["max_extension_count"],
                "source_kind": row["source_kind"],
                "source_note": row["source_note"],
            },
        )
