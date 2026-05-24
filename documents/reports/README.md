# Reports Document Index

This directory holds execution observations, audits, and debug analyses. `REPORT` documents are evidence of current state but not canonical contracts. To promote to canonical, reflect separately in ADR, `documents/game_rules/`, or `documents/index/document_inventory.md`.

## Current Report Bundles

Add subdirectories only when needed. Some past bundles such as `documentation_audit/`, `2026-05/` may have been removed during cleanup — if a path is missing, check archive or git history.

### Asteroid Lab (REPORT in plan tree)

- [`../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`](../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md) — 2026-05-17 progress snapshot (`REPORT`). Branch baseline `quality/repository-gate-cleanup`. Index: [`../index/document_inventory.md`](../index/document_inventory.md) Research·Report table.

## Usage Rules

- For implementation decisions, read `CANON` documents in [`../index/document_inventory.md`](../index/document_inventory.md) first.
- Do not apply drift confirmed in reports directly as implementation contracts; move to ADR or domain spec when needed.
- For archive candidacy, see [`../archive/README.md`](../archive/README.md).
