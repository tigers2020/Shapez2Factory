"""CLI probe for T1b canon slug (default DB; investigation-only).

Usage:
    python manage.py shell -c "exec(open('harness/investigation/run_canon_slug_probe.py').read())"
Or:
    python -m harness.investigation.run_canon_slug_probe
"""

from __future__ import annotations

import json
import os
import sys
from unittest.mock import patch


def run_canon_probe(*, throughput_target_percent: int = 10) -> dict[str, object]:
    from django.test.utils import override_settings

    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
        validate_pipeline_layout,
    )
    from harness.investigation.rttp_final_layout_assert_probe import diagnose_final_layout
    from harness.investigation.rttp_t1b_step_forensics import extract_t1b_forensics
    from tests.unit.asteroid_lab._runtime_game_data import run_solver_runtime_with_pinned_game_data

    canon_slug = "copy-import-495e552c"
    project = m.AsteroidProject.objects.filter(slug=canon_slug).first()
    if project is None:
        msg = f"Canon slug {canon_slug!r} not found in database"
        raise SystemExit(msg)

    captured: dict[str, object] = {}

    def _capture_validate_pipeline_layout(**kwargs: object) -> tuple[bool, object | None]:
        captured.update(kwargs)
        return validate_pipeline_layout(**kwargs)  # type: ignore[arg-type]

    with (
        override_settings(ASTEROID_LAB_RTTP_ENABLED=True),
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.validate_pipeline_layout",
            side_effect=_capture_validate_pipeline_layout,
        ),
    ):
        result = run_solver_runtime_with_pinned_game_data(
            int(project.pk),
            config={"throughput_target_percent": throughput_target_percent},
        )

    if not captured:
        msg = "validate_pipeline_layout was not invoked"
        raise RuntimeError(msg)

    code, detail = diagnose_final_layout(
        captured["committed_ids"],  # type: ignore[arg-type]
        captured["reserved_route_cells"],  # type: ignore[arg-type]
        captured["candidates_by_id"],  # type: ignore[arg-type]
        captured["inp"],  # type: ignore[arg-type]
    )
    steps = result.solver_summary.get("algorithm_steps") or []
    forensics = extract_t1b_forensics(steps)

    return {
        "primary_fl_xx": str(code.value),
        "primary_fl_detail": detail,
        "forensics": forensics,
        "solver_run_id": result.solver_run_id,
        "validation_passed": result.validation_passed,
        "issue_codes": list(result.solver_summary.get("issue_codes") or []),
    }


def main() -> None:
    payload = run_canon_probe()
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    main()
