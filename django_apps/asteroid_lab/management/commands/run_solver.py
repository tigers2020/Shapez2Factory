"""CLI entry for solver runtime stub (same service path as HTTP run-solver)."""

from __future__ import annotations

import json
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Invoke solver runtime entry for one Asteroid Lab project slug "
        "(PR-A/B stub: always SOLVER_NOT_AVAILABLE; mirrors POST run-solver)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--slug",
            required=True,
            help="AsteroidProject.slug (same as Lab URL slug).",
        )
        parser.add_argument(
            "--run-key",
            default=None,
            help="Optional stable SolverRun.run_key (ignored by stub).",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print full entry_result_to_json_dict JSON to stdout.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        slug = str(options["slug"]).strip()
        if not slug:
            raise CommandError("--slug is required.")

        project = m.AsteroidProject.objects.filter(slug=slug).first()
        if project is None:
            raise CommandError(f"Unknown project slug: {slug!r}")

        inp = (
            m.AsteroidMapInput.objects.filter(project_id=project.pk).order_by("-created_at").first()
        )
        if inp is None:
            raise CommandError(f"Project {slug!r} has no map input.")

        run_key = options.get("run_key")
        result = run_solver_runtime_for_project(
            int(project.pk),
            run_key=str(run_key).strip() if run_key else None,
        )
        body = entry_result_to_json_dict(result)

        if options["json"]:
            self.stdout.write(json.dumps(body, indent=2, sort_keys=True))
        else:
            self._print_human_summary(slug=slug, body=body)

        if result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE:
            raise CommandError(SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value)
        if result.error_code in (
            SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
            SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
            SolverRuntimeEntryErrorCode.DECODE_FAILED,
        ):
            raise CommandError(result.message or str(result.error_code))
        if not result.ok:
            if result.solver_run_id is not None:
                self.stderr.write(
                    self.style.WARNING(result.message or str(result.error_code or "run_failed"))
                    + "\n"
                )
                sys.exit(1)
            raise CommandError(result.message or f"run failed: {result.error_code}")

    def _print_human_summary(self, *, slug: str, body: dict[str, Any]) -> None:
        lines = [
            f"slug: {slug}",
            f"solver_run_id: {body.get('solver_run_id')}",
            f"ok: {body.get('ok')}",
            f"validation_passed: {body.get('validation_passed')}",
            f"lab_replay_frame_count: {body.get('lab_replay_frame_count')}",
        ]
        if body.get("error_code"):
            lines.append(f"error_code: {body['error_code']}")
        if body.get("message"):
            lines.append(f"message: {body['message']}")
        self.stdout.write("\n".join(lines))


__all__ = ["Command"]
