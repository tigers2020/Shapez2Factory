# `documents/archive/`

Completed, deprecated, superseded, and retained documents live here. For current implementation decisions, prefer [`documents/index/document_inventory.md`](../index/document_inventory.md) and `CANON` documents over archive.

## Archive buckets

| Subpath | Status | Description |
|------|------|------|
| [`2026-05-completed/`](2026-05-completed/README.md) | `COMPLETED` | Bundle of Python cleanup and Recipe Graph Editor documents marked complete in 2026-05. |
| [`completed-implementation/`](completed-implementation/README.md) | `COMPLETED` | Archived 1:1 `plan_*` / `research_*` pairs grouped by stem after implementation landed. |
| [`obsolete-src-shapez2-solver-plans-2026-05-01/`](obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | Stale plan drafts based on pre–Django-first `src/shapez2_solver`. |
| [`2026-05-orphan-mining-layout-plans-after-app-removal/`](2026-05-orphan-mining-layout-plans-after-app-removal/README.md) | `ARCHIVED` | Three placement-related plans left without backing code after mining solver removal. Do not use as implementation authority. |
| [`refactor_audit_pre_mining_solver_removal_2026-05/`](refactor_audit_pre_mining_solver_removal_2026-05/README.md) | `ARCHIVED` | Audit report bundle citing the removed `mining_solver_cursor_sessions` canon. Historical use only. |

## 2026-05-15 archive decisions

- `django_apps.shapez_asteroid`, mining layout v2 implementation, canonical step specs, and the old mining archive tree were removed from the repository. Consult **git history** for past bodies.
- Documents under `documents/plans/` with unclear completion status stay active/backlog. Move to archive only stems with verification results or completion reports.
- **2026-05-16**: Three orphan mining layout plans moved to [`2026-05-orphan-mining-layout-plans-after-app-removal/`](2026-05-orphan-mining-layout-plans-after-app-removal/README.md); `documents/refactor_audit/` moved to [`refactor_audit_pre_mining_solver_removal_2026-05/`](refactor_audit_pre_mining_solver_removal_2026-05/README.md).

Prefer the parent map at [`../README.md`](../README.md).
