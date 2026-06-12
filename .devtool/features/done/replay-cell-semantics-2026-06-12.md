---
id: "replay-cell-semantics-2026-06-12"
status: "done"
priority: "medium"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T00:00:00.000Z"
modified: "2026-06-12T23:30:00.000Z"
completedAt: "2026-06-12T23:30:00.000Z"
labels: ["asteroid-lab", "replay", "architecture"]
order: "a1"
---
# Replay cell semantics (Steps 1–4)

## Scope

Asteroid Lab replay cell semantics boundary. Detail: [spec.md](../../docs/architecture/replay-cell-semantics/spec.md).

## Acceptance

- [x] Architecture report + Steps 1–4 sequence locked
- [x] **Step 1:** resolver → `replay_frame_cell_resolver.py`
- [x] **Step 2:** `replay_cell_semantics.py`
- [x] **Step 3:** wire tests; remove flat shim + `replay_frame_cell_lookup.py`
- [ ] **Step 4 (optional):** server-canonical compare; overlay bucket registry — deferred, separate approval

## Artifacts

| Kind | Path | Updated |
|------|------|---------|
| report | docs/architecture/replay-cell-semantics/report.md | 2026-06-12 |
| spec | docs/architecture/replay-cell-semantics/spec.md | 2026-06-12 |
| plan | docs/architecture/replay-cell-semantics/plan.md | 2026-06-12 |

## Archive summary

Replay cell semantics boundary Steps 1–3 complete.

Canonical server lookup now lives in `replay_frame_cell_resolver` and returns `EffectiveCellWire`.
Read-side semantic policy is centralized in `replay_cell_semantics.py`.
Deprecated flat web shim was removed.
Step 4 server/client compare + overlay bucket registry remains optional and requires separate approval.

## Progress

- 2026-06-12 — **align** — `/improve-codebase-architecture`; scope locked
- 2026-06-12 — **contract** — Steps 1–4 sequence locked
- 2026-06-12 — **implement** — Step 1: resolver layer fix
- 2026-06-12 — **implement** — Step 2: `replay_cell_semantics.py`
- 2026-06-12 — **implement** — Step 3: flat shim removal + wire tests
- 2026-06-12 — **verify** — combined gate 73 passed; grep django_apps/tests 0 shim refs; ruff clean
- 2026-06-12 — **done** — required epic closed; Step 4 optional deferred
