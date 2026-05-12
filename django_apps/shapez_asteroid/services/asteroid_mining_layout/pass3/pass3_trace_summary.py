"""Pass3 trace summary helpers."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded import (
    p3e2_pass3_summary_placeholder,
    p3e3_pass3_summary_placeholder,
)


def pass3_skip_summary(
    *,
    skip_reason: str,
    rejected_reason: str,
) -> dict[str, Any]:
    return {
        "pass3_skipped": True,
        "pass3_skip_reason": skip_reason,
        "pass3_greedy_committed": None,
        **p3e2_pass3_summary_placeholder(rejected_reason=rejected_reason),
        **p3e3_pass3_summary_placeholder(rejected_reason=rejected_reason),
    }
