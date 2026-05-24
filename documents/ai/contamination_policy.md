# Contamination policy

Operational rules to prevent stale documents, removed package paths, and debug artifacts from becoming **implementation authority** for Asteroid Lab / RTTP work.

**Authority map (catalog):** [`../index/document_inventory.md`](../index/document_inventory.md) — use the **Asteroid Lab authority by topic** table when two documents disagree.

**Status enum:** [`../index/document_lifecycle.md`](../index/document_lifecycle.md)

---

## Read order (new session)

1. [`../../AGENTS.md`](../../AGENTS.md) and [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc)
2. [`../index/document_inventory.md`](../index/document_inventory.md) — topic row for your task
3. [`START_HERE.md`](START_HERE.md)
4. [`current_plan.md`](current_plan.md) — active runtime and queue
5. This file — forbidden patterns and PR playbook

---

## Conflict resolution

- **Do not merge** competing specs or plans.
- **Do not** treat `REPORT`, `documents/debug/`, or `documents/archive/` as design authority.
- When two sources conflict, use the **topic row** in `document_inventory.md`. If no row exists, add one in a governance PR before implementing.

---

## Authority precedence (summary)

Full stack: [`current_plan.md`](current_plan.md) § Authority precedence.

1. Code + tests under `django_apps/asteroid_lab/{reconstruction,optimization,contracts}/` and `tests/unit/asteroid_lab/`
2. `current_plan.md` — runtime pointer
3. Per-topic row in `document_inventory.md`
4. Row-designated `docs/superpowers/specs/*` or `documents/Algorithm/asteroid_lab_*.md`
5. `document_inventory.md` status routing
6. `documents/plans/asteroid_lab_optimization/` — **QUARANTINE** only
7. `documents/Algorithm/solver_runtime/` — historical unless `current_plan` promotes a subsection
8. Reports and archives — observation only

**Per-file marker:** Quarantine docs use YAML `do_not_use_as_authority: true` in their front matter. See [`document_lifecycle.md`](../index/document_lifecycle.md) § Operational label: QUARANTINE for the recommended header template.

---

## Stable invariants (never violate)

| Invariant | Meaning |
|-----------|---------|
| Placement ≠ Commit | Placement candidates are not commit order |
| Route probe at creation | Candidates enter normal pool only after route probe — not routing-later |
| Single route_domain builder | `RouteDomainSnapshotBuilder` only owner of route_domain snapshot |
| Validation read-only | No route creation, topology mutation, or repair in validation |
| Replay / artifacts output-only | `solver_summary`, NDJSON, replay frames are not optimization **input** |
| No coord-only transport kind | When catalog transport exists, do not infer belt/pipe from coordinates alone |

---

## Forbidden contamination patterns

Do not introduce or restore:

- `solver_summary` / `replay_events` / persisted replay driving search, commit, or validation decisions
- Placement-first, routing-later integrated pipeline
- Validation that creates routes or mutates placement/topology
- Candidate enumeration order as commit order
- Multiple patches to `route_domain` outside `RouteDomainSnapshotBuilder`
- Raw server coordinate paths inside optimization after `OptimizationInput` boundary

---

## Legacy path tokens (quarantine — not current targets)

Do **not** create or import for current Asteroid Lab work:

- `django_apps.shapez_asteroid` (app removed)
- `tests/unit/shapez_asteroid` (removed)
- `documents/Algorithm/mining_solver_cursor_sessions/` (git history only)

**Current targets:**

- `django_apps/asteroid_lab/optimization/`
- `tests/unit/asteroid_lab/`

---

## PR playbook

| PR | Scope |
|----|--------|
| **PR-A** | This policy + inventory / START_HERE / current_plan / README conflict fix |
| **PR-B** | Architecture import and forbidden-token gates on `optimization/` |
| **PR-C** | Replay input and validation read-only gates |
| **PR-D** | Quarantine moves (front matter first) |
| **PR-E** | Dead code after B/C green |

---

## AI agent rules (before editing)

1. Read the **topic row** in `document_inventory.md` for your task.
2. If authority is unclear, stop and fix inventory — do not guess by averaging docs.
3. Do not refactor adjacent legacy or quarantine code in the same PR as a feature fix.
4. Add or extend a regression gate before changing solver behavior (PR-B+).

---

## Spec reference

Design: [`docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md`](../../docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md)
