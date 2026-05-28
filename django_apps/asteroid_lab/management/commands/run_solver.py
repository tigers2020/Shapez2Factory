"""CLI entry for solver runtime stub (same service path as HTTP run-solver)."""

from __future__ import annotations

import json
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.placement_goal import parse_max_placement_goal_count
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from django_apps.asteroid_lab.services.throughput_target import parse_throughput_target_percent


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Invoke solver runtime entry for one Asteroid Lab project slug "
        "(PR-A stub: always SOLVER_NOT_AVAILABLE; mirrors POST run-solver)."
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
            help="Optional stable SolverRun.run_key (default: generated).",
        )
        parser.add_argument(
            "--macro-only",
            action="store_true",
            help="Set config_json macro_only_mode=true (MacroBundleT3 track).",
        )
        parser.add_argument(
            "--no-replay",
            action="store_true",
            help="Set rttp_record_replay=false (skip :rttp DB replay sink).",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print full entry_result_to_json_dict JSON to stdout.",
        )
        parser.add_argument(
            "--deferred-retry-execute",
            action="store_true",
            help=(
                "Set config_json deferred_retry_shadow to enabled=true, "
                "observe_only=false (PR-4 normative ops entrypoint)."
            ),
        )
        parser.add_argument(
            "--throughput-target-percent",
            type=int,
            default=None,
            help="Throughput target as percent of reconstruction max (10-80).",
        )
        parser.add_argument(
            "--max-placement-goal-count",
            type=int,
            default=None,
            help=(
                "Optional max placement override; must be >= placement_target_percent "
                "of field cells (no default 32 cap)."
            ),
        )
        parser.add_argument(
            "--selection-mode",
            choices=("greedy_regret", "evolution"),
            default=None,
            help="Set config_json selection.mode (PR-GA-2 normative ops entrypoint).",
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

        config: dict[str, Any] = {}
        selection_mode = options.get("selection_mode")
        if options["macro_only"] and options["deferred_retry_execute"]:
            raise CommandError(
                "Cannot combine --macro-only with --deferred-retry-execute "
                "(v0.1 normal RTTP path only)."
            )
        if options["macro_only"] and selection_mode == "evolution":
            raise CommandError("Cannot combine --macro-only with --selection-mode=evolution.")
        if options["macro_only"]:
            config[SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY] = True
        if options["no_replay"]:
            config[SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY] = False
        if options["deferred_retry_execute"]:
            config[SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY] = {
                "enabled": True,
                "observe_only": False,
            }
        if selection_mode is not None:
            config[SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY] = {"mode": selection_mode}
            if selection_mode == "evolution":
                config[SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY] = {
                    "enabled": True,
                    "generations": 4,
                    "population_size": 24,
                    "random_seed": 0,
                }
        if options["throughput_target_percent"] is not None:
            try:
                config[SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY] = (
                    parse_throughput_target_percent(
                        {
                            SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY: options[
                                "throughput_target_percent"
                            ]
                        }
                    )
                )
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
        if options["max_placement_goal_count"] is not None:
            try:
                config[SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY] = (
                    parse_max_placement_goal_count(
                        {
                            SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY: options[
                                "max_placement_goal_count"
                            ]
                        }
                    )
                )
            except ValueError as exc:
                raise CommandError(str(exc)) from exc

        run_key = options.get("run_key")
        result = run_solver_runtime_for_project(
            int(project.pk),
            run_key=str(run_key).strip() if run_key else None,
            config=config or None,
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
        run_id = body.get("solver_run_id")
        validation = body.get("validation_passed")
        summary = body.get("solver_summary") or {}
        macro_mode = summary.get("macro_only_mode")
        macro_hud = summary.get("macro_commit_summary")
        lines = [
            f"slug: {slug}",
            f"solver_run_id: {run_id}",
            f"ok: {body.get('ok')}",
            f"validation_passed: {validation}",
            f"macro_only_mode: {macro_mode}",
            f"lab_replay_frame_count: {body.get('lab_replay_frame_count')}",
        ]
        if isinstance(macro_hud, dict) and macro_hud:
            lines.append(
                "macro_commit_summary: "
                f"macros={len(macro_hud.get('committed_macro_ids') or [])} "
                f"children={len(macro_hud.get('committed_child_ids') or [])} "
                f"domain_version={macro_hud.get('domain_version')} "
                f"conflicts={macro_hud.get('conflict_count')}"
            )
        issue_codes = summary.get("issue_codes") or []
        if issue_codes:
            lines.append(f"issue_codes: {', '.join(str(c) for c in issue_codes)}")
        if summary.get("diagnostic_expected_shortfall"):
            lines.append(
                "t2_policy: expected_diagnostic_shortfall "
                "(diagnostic canon; T3 ops not applicable)"
            )
        slug_class = summary.get("rttp_ops_slug_class")
        if slug_class == "pass_capable":
            lines.append("rttp_ops_slug_class: pass_capable (T3 reference slug)")
        elif slug_class:
            lines.append(f"rttp_ops_slug_class: {slug_class}")
        if body.get("error_code"):
            lines.append(f"error_code: {body['error_code']}")
        if body.get("message"):
            lines.append(f"message: {body['message']}")
        self.stdout.write("\n".join(lines))


__all__ = ["Command"]
