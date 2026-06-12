"""CLI entry for the solver runtime path used by HTTP run-solver."""

from __future__ import annotations

import json
import sys
import time
from contextlib import nullcontext
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from django_apps.game_data.services.game_data_snapshot_export import (
    build_game_data_snapshot_payload,
)
from shapez2_factory.adapters.asteroid_lab.cli_console import emit_cli_line


def _console_token(value: object) -> str:
    """Return a single-token value for BA-9 access-log fields."""
    return str(value).strip().replace(" ", "_")


class Command(BaseCommand):
    help = (
        "Invoke solver runtime entry for one Asteroid Lab project slug "
        "(mirrors POST run-solver)."
    )

    def add_arguments(self, parser: object) -> None:
        parser.add_argument(
            "--slug",
            required=True,
            help="AsteroidProject.slug (same as Lab URL slug).",
        )
        parser.add_argument(
            "--run-key",
            default=None,
            help="Optional stable SolverRun.run_key.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print full entry_result_to_json_dict JSON to stdout.",
        )
        parser.add_argument(
            "--subprocess",
            dest="use_subprocess",
            action="store_true",
            help="Accepted for compatibility; Django run-solver is subprocess-only.",
        )
        parser.add_argument(
            "--artifact-root",
            default=None,
            help="Artifact root used with --subprocess (defaults to settings var/runs).",
        )
        parser.add_argument(
            "--cli-verbose",
            action="store_true",
            help="Forward verbose layer logging to the pure CLI subprocess.",
        )

    def handle(self, *args: object, **options: object) -> None:
        slug = str(options["slug"]).strip()
        emit_cli_line("run_solver start", surface="django_management", slug=slug)
        started = time.monotonic()
        exit_code = 1
        error_code: str | None = None
        ok = False
        solver_run_id: int | None = None
        try:
            result = self._handle_logged(slug=slug, options=options)
            solver_run_id = result.solver_run_id
            exit_code = 0
            ok = True
        except CommandError as exc:
            error_code = _console_token(exc)
            raise
        except SystemExit as exc:
            code = exc.code
            exit_code = int(code) if isinstance(code, int) else 1
            raise
        finally:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            emit_cli_line(
                "run_solver end",
                surface="django_management",
                slug=slug,
                exit=exit_code,
                elapsed_ms=elapsed_ms,
                solver_run_id=solver_run_id,
                error_code=error_code,
                ok=ok,
            )

    def _handle_logged(
        self,
        *,
        slug: str,
        options: dict[str, object],
    ) -> SolverRuntimeEntryResult:
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
        overrides: dict[str, object] = {}
        if options.get("use_subprocess"):
            overrides["ASTEROID_LAB_SOLVER_MODE"] = "subprocess_only"
        artifact_root = options.get("artifact_root")
        if artifact_root:
            overrides["ASTEROID_LAB_ARTIFACT_ROOT"] = Path(str(artifact_root))
        settings_context = override_settings(**overrides) if overrides else nullcontext()
        with settings_context:
            result = run_solver_runtime_for_project(
                int(project.pk),
                run_key=str(run_key).strip() if run_key else None,
                config={"cli_verbose": True} if options.get("cli_verbose") else None,
                game_data_snapshot=build_game_data_snapshot_payload(),
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
        return result

    def _print_human_summary(self, *, slug: str, body: dict[str, object]) -> None:
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
