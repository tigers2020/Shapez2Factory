"""Scan Lab slugs for RTTP T3 certification (Track B ops; same runtime as run_solver)."""

from __future__ import annotations

import json
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab.services.rttp_slug_certification_scan import (
    build_scan_report,
    resolve_scan_projects,
    run_slug_certification_scan,
)
from django_apps.game_data.snapshots.errors import SnapshotBuildError
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Scan Asteroid Lab project slugs with the RTTP run_solver runtime path "
        "and evaluate T3 certification tiers (output-only)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--project-id",
            type=int,
            default=None,
            help="Scan a single AsteroidProject by primary key.",
        )
        parser.add_argument(
            "--slug",
            default=None,
            help="Scan a single AsteroidProject.slug.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of slug candidates (ordered by slug).",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Print machine-readable scan report JSON to stdout.",
        )
        parser.add_argument(
            "--include-diagnostic",
            action="store_true",
            help="Include diagnostic canon slug(s); runtime is skipped for them.",
        )
        parser.add_argument(
            "--fail-on-pass",
            action="store_true",
            help=(
                "Exit 0 when at least one certified_pass is found; otherwise exit 1 "
                "(ops discovery gate)."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        slug_opt = options.get("slug")
        if slug_opt is not None and not str(slug_opt).strip():
            raise CommandError("--slug must be non-empty when provided.")

        projects = resolve_scan_projects(
            project_id=options.get("project_id"),
            slug=str(slug_opt).strip() if slug_opt else None,
            limit=options.get("limit"),
            include_diagnostic=bool(options.get("include_diagnostic")),
        )
        if not projects:
            if slug_opt or options.get("project_id") is not None:
                raise CommandError("No matching AsteroidProject for scan criteria.")
            report = build_scan_report([])
            self._emit_report(report, json_output=bool(options.get("json")))
            if options.get("fail_on_pass"):
                sys.exit(1)
            return

        try:
            game_data_build = build_asteroid_game_data_snapshot_with_provenance()
        except SnapshotBuildError as exc:
            raise CommandError(f"game_data snapshot failed: {exc.code.value}") from exc

        report = run_slug_certification_scan(
            projects=projects,
            game_data_snapshot=game_data_build.snapshot,
            game_data_provenance=game_data_build.provenance,
            catalog_slice=game_data_build.catalog_slice,
        )

        self._emit_report(report, json_output=bool(options.get("json")))

        if options.get("fail_on_pass"):
            if report.get("certified_pass_count", 0) > 0:
                sys.exit(0)
            sys.exit(1)

    def _emit_report(self, report: dict[str, Any], *, json_output: bool) -> None:
        if json_output:
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return

        self.stdout.write(f"schema_version: {report.get('schema_version')}")
        self.stdout.write(f"candidate_count: {report.get('candidate_count')}")
        self.stdout.write(f"certified_pass_count: {report.get('certified_pass_count')}")
        self.stdout.write(f"blocked_count: {report.get('blocked_count')}")
        for row in report.get("results") or []:
            self.stdout.write(
                f"  {row.get('slug')}: {row.get('cert_status')} "
                f"(run_id={row.get('solver_run_id')})"
            )


__all__ = ["Command"]
