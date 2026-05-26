"""Capture RTTP core recovery A0 evidence (read-only ops; no solver semantics change)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.contracts.rttp_recovery_evidence import (
    RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
)
from django_apps.asteroid_lab.services.rttp_recovery_evidence import (
    build_recovery_evidence_report,
    build_recovery_evidence_row,
    load_replay_overlay_connectivity,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    run_solver_runtime_for_project,
)
from django_apps.game_data.snapshots.errors import SnapshotBuildError
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Run RTTP solver on recovery slugs and write A0 evidence JSON "
        "(output-only; does not change solver semantics)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--slug",
            action="append",
            default=None,
            help="AsteroidProject.slug (repeatable). Defaults to Gate A primary slugs.",
        )
        parser.add_argument(
            "--import-test-map",
            action="store_true",
            help=(
                "Import tests/fixtures/asteroid_lab/test_map.txt as "
                f"{RTTP_CORE_RECOVERY_TEST_MAP_SLUG}."
            ),
        )
        parser.add_argument(
            "--include-diagnostic",
            action="store_true",
            help="Include copy-import-495e552c (diagnostic policy row; runtime skipped).",
        )
        parser.add_argument(
            "--include-tiny-smoke",
            action="store_true",
            help="Include rttp-cert-candidate-tiny-passable-v2 smoke row.",
        )
        parser.add_argument(
            "--output",
            default="docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-baseline.json",
            help="Path for evidence JSON report.",
        )
        parser.add_argument(
            "--markdown",
            default="docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-baseline.md",
            help="Path for human-readable summary.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options.get("import_test_map"):
            from django_apps.asteroid_lab.management.commands import (
                import_rttp_core_recovery_test_map as import_test_map_cmd,
            )

            import_test_map_cmd.import_core_recovery_test_map(replace=True)

        slugs: list[str] = list(options.get("slug") or [])
        if not slugs:
            slugs = [
                RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
                "rttp-cert-candidate-recon-l0",
            ]
        if options.get("include_diagnostic"):
            slugs.append("copy-import-495e552c")
        if options.get("include_tiny_smoke"):
            slugs.append("rttp-cert-candidate-tiny-passable-v2")

        try:
            game_data_build = build_asteroid_game_data_snapshot_with_provenance()
        except SnapshotBuildError as exc:
            raise CommandError(f"game_data snapshot failed: {exc.code.value}") from exc

        results: list[dict[str, Any]] = []
        for slug in slugs:
            project = m.AsteroidProject.objects.filter(slug=str(slug).strip()).first()
            if project is None:
                raise CommandError(f"Unknown slug: {slug}")
            row = self._capture_slug(
                project,
                game_data_snapshot=game_data_build.snapshot,
                game_data_provenance=game_data_build.provenance,
                catalog_slice=game_data_build.catalog_slice,
            )
            results.append(row)
            self.stdout.write(
                f"{slug}: gate_a_passed={row.get('gate_a_passed')} "
                f"extractors={row.get('committed_extractor_count')} "
                f"fot={row.get('committed_output_transport_cells')} "
                f"route={row.get('committed_route_cell_count')} "
                f"exterior={row.get('exterior_connected_route_count')}"
            )

        notes = [
            (
                "Task A4: placement_goal_count from ReconstructionCompleteMap "
                "asteroid_field_cell_count × placement_target_percent."
            ),
            (
                "Task A5: output_stub outside traversable envelope reserved when FOT is "
                "outside mineable (FL-06); placement_goal_shortfall not goal cap."
            ),
            (
                "committed_extractor_count below placement_goal_count is expected "
                "shortfall, not placement goal failure."
            ),
            (
                "Task A6: validation fail-closed on missing_output_transport / "
                "missing_exterior_route; shortfall does not set validation_passed false."
            ),
        ]
        report = build_recovery_evidence_report(results, notes=notes)
        output_path = Path(str(options["output"]))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        md_path = Path(str(options["markdown"]))
        md_path.write_text(self._markdown_report(report), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {output_path}"))
        self.stdout.write(self.style.SUCCESS(f"Wrote {md_path}"))

    def _capture_slug(
        self,
        project: m.AsteroidProject,
        *,
        game_data_snapshot: Any,
        game_data_provenance: Any,
        catalog_slice: Any,
    ) -> dict[str, Any]:
        slug = str(project.slug)
        if slug == "copy-import-495e552c":
            return build_recovery_evidence_row(
                slug=slug,
                project_id=int(project.pk),
                solver_run_id=None,
                run_key=None,
                solver_summary={},
                trunk_mask_cells=frozenset(),
                replay_overlay_metrics=None,
            )

        if not m.AsteroidMapInput.objects.filter(project_id=project.pk).exists():
            raise CommandError(f"Slug {slug} has no map input")

        config = {SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY: True}
        result = run_solver_runtime_for_project(
            int(project.pk),
            config=config,
            game_data_snapshot=game_data_snapshot,
            game_data_provenance=game_data_provenance,
            catalog_slice=catalog_slice,
        )
        if result.error_code in {
            SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE,
            SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
            SolverRuntimeEntryErrorCode.DECODE_FAILED,
        }:
            raise CommandError(f"{slug}: runtime error {result.error_code}")

        summary = dict(result.solver_summary or {})
        run_key: str | None = None
        if result.solver_run_id is not None:
            run = m.SolverRun.objects.filter(pk=int(result.solver_run_id)).first()
            if run is not None:
                run_key = str(run.run_key)

        overlay_metrics = None
        if result.solver_run_id is not None and run_key is not None:
            overlay_metrics = load_replay_overlay_connectivity(
                project_id=int(project.pk),
                run_key=run_key,
            )

        return build_recovery_evidence_row(
            slug=slug,
            project_id=int(project.pk),
            solver_run_id=result.solver_run_id,
            run_key=run_key,
            solver_summary=summary,
            trunk_mask_cells=frozenset(),
            replay_overlay_metrics=overlay_metrics,
        )

    def _markdown_report(self, report: dict[str, Any]) -> str:
        lines = [
            "# RTTP Core Recovery — A0 Evidence Baseline",
            "",
            f"**Schema:** `{report.get('schema_version')}`  ",
            f"**Captured:** `{report.get('captured_at')}`  ",
            f"**Gate A primary pass count:** {report.get('gate_a_primary_pass_count')}",
            "",
            "## Solver semantics",
            "",
        ]
        for note in report.get("notes") or []:
            lines.append(f"- {note}")
        lines.extend(["", "## Results", ""])
        lines.append(
            "| Slug | Run ID | Ext | Route | Ext-route | T1b | Val | Gate A | "
            "1st stage | Primary symptom |"
        )
        lines.append(
            "|------|--------|-----|-------|-----------|-----|-----|--------|"
            "-----------|-----------------|"
        )
        for row in report.get("results") or []:
            lines.append(
                f"| `{row.get('slug')}` | {row.get('solver_run_id')} | "
                f"{row.get('visible_extension_cell_count')} | "
                f"{row.get('committed_route_cell_count')} | "
                f"{row.get('exterior_connected_route_count')} | "
                f"{row.get('t1b_passed')} | {row.get('validation_passed')} | "
                f"{row.get('gate_a_passed')} | "
                f"`{row.get('first_failing_stage')}` | "
                f"`{row.get('primary_symptom')}` |"
            )
        lines.extend(["", "### Placement goal (Task A4, per slug)", ""])
        for row in report.get("results") or []:
            lines.append(
                f"- **{row.get('slug')}**: "
                f"asteroid_fields={row.get('asteroid_field_cell_count')} "
                f"percent={row.get('placement_target_percent')} "
                f"goal={row.get('placement_goal_count')} "
                f"committed={row.get('committed_extractor_count')} "
                f"route_cap={row.get('route_feasible_candidate_cap')} "
                f"anchor_cap={row.get('non_overlapping_anchor_cap')}"
            )
        lines.extend(["", "### Diagnostic flags (per slug)", ""])
        for row in report.get("results") or []:
            lines.append(
                f"- **{row.get('slug')}**: blocking={row.get('blocking_stages')} "
                f"flags={row.get('diagnostic_flags')}"
            )
        lines.append("")
        return "\n".join(lines)


__all__ = ["Command"]
