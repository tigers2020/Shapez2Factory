"""Lazy bridge to ``solver_service.validate_final_mining_layout`` (single call site)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
)


def validate_final_mining_layout_bridge(
    mining_map: list[dict[str, Any]],
) -> FinalValidationReport:
    """Delegate to ``solver_service.validate_final_mining_layout``.

    Lazy-import keeps monkeypatch targets stable for Pass3, STEP4, and finalize.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
        solver_service,
    )

    return solver_service.validate_final_mining_layout(mining_map)
