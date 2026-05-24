---
status: ARCHIVED
do_not_use_as_authority: true
archived_date: 2026-05-22
archived_reason: pre-RTTP plan snapshots; strip-solver removed monolith/shadow/RD only — not current RTTP package
authority_for_implementation: documents/index/document_inventory.md
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
  - docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
last_reviewed: 2026-05-24
---

# asteroid_lab_optimization plans (QUARANTINE)

> **QUARANTINE:** `do_not_use_as_authority: true`. Historical plan **snapshots** only.

- **Strip-solver (2026-05-22):** removed pre-RTTP **monolith / shadow / RD** pipeline — not the current RTTP package.
- **Current runtime (2026-05-24):** `django_apps/asteroid_lab/optimization/` — RTTP Hybrid C when `ASTEROID_LAB_RTTP_ENABLED=True` — see [`documents/ai/current_plan.md`](../../ai/current_plan.md).
- **Stable contracts:** prefer [`documents/Algorithm/asteroid_lab_*.md`](../../Algorithm/) and merged [`docs/superpowers/specs/`](../../../docs/superpowers/specs/) per [`document_inventory.md`](../../index/document_inventory.md) topic rows (**§ Asteroid Lab authority by topic**).
- **This directory:** do not edit for new features; do not cite as implementation authority.

## Doc sweep (2026-05-23)

Each `asteroid_lab_*.md` file has a top-of-file banner pointing at **`documents/Algorithm/`** when a matching CANON doc exists.

- **PR-F:** Product code uses **island-local** `(x, y)` only; dense server HUD removed.
