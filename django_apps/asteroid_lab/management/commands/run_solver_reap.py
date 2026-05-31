"""Reap RUNNING solver runs via artifact-first reconcile (PR-CLI-7)."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from django_apps.asteroid_lab.services.solver_run_reconcile import reconcile_running_solver_runs


class Command(BaseCommand):
    help = "Reconcile all RUNNING SolverRun rows (manifest ARTIFACT_WRITTEN → ingest)."

    def handle(self, *args: Any, **options: Any) -> None:
        del args, options
        results = reconcile_running_solver_runs()
        if not results:
            self.stdout.write("no running solver runs")
            return
        for item in results:
            self.stdout.write(
                f"run_id={item.solver_run_id} status={item.status} "
                f"lifecycle={item.lifecycle_status} ok={item.ok}"
            )
