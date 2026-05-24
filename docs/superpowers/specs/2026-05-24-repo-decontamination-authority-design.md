# Repository Decontamination — Authority Repair (PR-A)

**Status:** APPROVED (design)  
**Date:** 2026-05-24  
**Scope:** Documentation and governance only  
**Implementation plan:** [`../plans/2026-05-24-repo-decontamination-authority-pr-a.md`](../plans/2026-05-24-repo-decontamination-authority-pr-a.md)

---

## 1. Problem

The repository already has document governance (`document_inventory.md`, `document_lifecycle.md`, `START_HERE.md`) and architecture import tests, but **authority drift** causes AI agents and humans to implement against obsolete contracts.

### Documented contamination cases

| Case | Symptom | Risk |
|------|---------|------|
| **A — Opposite authority** | `documents/plans/asteroid_lab_optimization/README.md` states optimization/solver was removed; `documents/ai/current_plan.md` states `django_apps/asteroid_lab/optimization/` is active RTTP | Agents strip or ignore live runtime; resurrect strip-solver-only world |
| **B — Archived snapshots as canon** | `documents/plans/asteroid_lab_optimization/asteroid_lab_*.md` copied from pre-RTTP era | Wrong package paths, DTOs, sequences |
| **C — Removed package paths in prompts** | `django_apps.shapez_asteroid`, `tests/unit/shapez_asteroid` appear in old docs/drafts | Dead namespace revival, broken import gates |
| **D — Stale START_HERE pointer** | References inventory table **"채굴 레이아웃 솔버 정본 후보"** which no longer exists | Broken read order for every new session |
| **E — Historical solver_runtime series** | Front matter `ARCHIVED` with body implying optimization absent globally | Conflicts with RTTP Hybrid C on `master` |
| **F — Replay/artifact leakage (future)** | Not fixed in PR-A; needs PR-B/C gates | `solver_summary`, replay frames used as algorithm input |

**Root cause:** Multiple partial authority maps without a **topic-level conflict resolver** and without marking quarantine docs `do_not_use_as_authority`.

---

## 2. Goals

1. **Single authority map:** Extend `documents/index/document_inventory.md` (no parallel `authority_index.md`).
2. **Operational policy:** Add thin `documents/ai/contamination_policy.md` (gates, forbidden patterns, PR playbook — no duplicate catalog tables).
3. **Runtime pointer:** Add **Authority precedence** to `documents/ai/current_plan.md` aligned with live code.
4. **Fix broken AI entry:** Repair `documents/ai/START_HERE.md` for Asteroid Lab / RTTP (remove mining-solver table reference).
5. **Resolve conflict A:** Rewrite `documents/plans/asteroid_lab_optimization/README.md` to distinguish strip-solver (monolith removed) vs RTTP (active).
6. **Per-topic authority (Option 3):** Inventory table rows define which doc/spec wins per topic — no global "Algorithm vs superpowers" default.
7. **Quarantine marking:** Minimum set of historical docs get YAML `do_not_use_as_authority: true` and inventory QUARANTINE rows.

---

## 3. Non-goals (PR-A)

- No solver behavior, DTO, validation, or replay logic changes
- No Python source changes under `django_apps/` or `src/`
- No new or modified pytest files (PR-B/C)
- No `authority_index.md`
- No physical move to `documents/quarantine/` (PR-D)
- No dead code deletion (PR-E)
- No package rename or `legacy_quarantine/` directory
- No bulk edit of every `docs/superpowers/plans/*.md` body
- No global rule "superpowers always wins" or "Algorithm always wins"

---

## 4. Authority precedence

When documents disagree, **do not merge or average** them. Resolve in this order:

| Tier | Source | Role |
|------|--------|------|
| 1 | Code + tests: `django_apps/asteroid_lab/{reconstruction,optimization,contracts}/`, `tests/unit/asteroid_lab/` | Ground truth for what runs |
| 2 | `documents/ai/current_plan.md` | Active queue, runtime paths, CLOSED/PAUSE tracks |
| 3 | **Per-topic row** in `document_inventory.md` § Asteroid Lab authority by topic | **Conflict resolver (Option 3)** |
| 4 | Row-designated spec or Algorithm doc | Implementation contract for that topic |
| 5 | `document_inventory.md` (status enum) | Route REPORT vs CANON vs QUARANTINE |
| 6 | `documents/plans/asteroid_lab_optimization/` | **QUARANTINE** — historical snapshots only |
| 7 | `documents/Algorithm/solver_runtime/` | Historical Phase A–M unless `current_plan` promotes a subsection |
| 8 | `REPORT`, `documents/debug/`, `documents/archive/` | Observation and history only |

**Invariant contracts** (stable across topics; cited in `contamination_policy.md`):

- Placement ≠ Commit
- Route probe at candidate creation (not routing-later)
- `RouteDomainSnapshotBuilder` single owner for route_domain snapshot
- Validation read-only (no route creation, topology mutation, repair)
- Replay / NDJSON / `solver_summary` / artifacts **output-only** (not optimization input)

---

## 5. Per-topic inventory authority table

Add to `documents/index/document_inventory.md` as section **「Asteroid Lab authority by topic」**.

| Topic | `authority_for_implementation` | Inventory status | Notes |
|-------|-------------------------------|------------------|-------|
| Runtime entry / config gate | `current_plan.md` + `django_apps/asteroid_lab/services/solver_runtime_entry.py` | CANON → code | `ASTEROID_LAB_RTTP_ENABLED`; strip removed monolith only |
| RTTP Hybrid C pipeline | `docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md` + `optimization/` | ACTIVE spec | Merged baseline on `master` |
| Macro bundle T3 | `docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md` | ACTIVE spec | **PAUSE** per `current_plan` — no new macro work |
| B2 catalog slice / transport T2 | `docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md` | CLOSED | PR #62; tests ground truth |
| B2 transport-aware route domain T3 | `docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md` | CLOSED | PR #61 |
| Track D footprint/connector | `docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md` (+ Track D plan when exists) | ACTIVE | Design parent; plan TBD |
| OptimizationInput / adapter | `documents/Algorithm/asteroid_lab_01_optimization_input.md` | CANON | **Not** `plans/asteroid_lab_optimization/01` |
| Route probe / candidate pool | `documents/Algorithm/asteroid_lab_04_route_probe.md` | CANON | Probe at creation |
| Validation read-only | `documents/Algorithm/asteroid_lab_08_validation.md` + `documents/adr/ADR-003-final-validation-assertion-gate.md` | CANON | |
| Replay timeline / 3B-S | `documents/Algorithm/asteroid_lab_09_replay_timeline.md` + `docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md` | CANON + ACTIVE spec | Output-only product replay |
| Development sequence | `documents/Algorithm/asteroid_lab_10_development_sequence.md` + `current_plan` RTTP gate sync | ACTIVE doc | Checkbox state may lag; gate sync note wins |
| Pre-RTTP plans tree | `documents/plans/asteroid_lab_optimization/` | **QUARANTINE** (`ARCHIVED`) | `do_not_use_as_authority: true` |
| Solver runtime Phase A–M | `documents/Algorithm/solver_runtime/` | **HISTORICAL** | Orchestration archive; RTTP ≠ this series |
| Mining layout solver (removed) | git history only | **REMOVED** | No START_HERE table |
| Lab replay wiring | `documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md` | CANON | Distinct from optimization search |

**Operational label QUARANTINE:** Maps to lifecycle enum `ARCHIVED` or `SUPERSEDED` plus `do_not_use_as_authority: true` in front matter.

---

## 6. Contamination policy contract

New file: `documents/ai/contamination_policy.md`.

### Must contain

1. **Purpose** — prevent stale docs/paths/artifacts from becoming implementation authority  
2. **Read order** — AGENTS → inventory (topic table) → START_HERE → current_plan → this policy  
3. **Global precedence** — summary + link to `current_plan.md` § Authority precedence  
4. **Conflict rule** — use topic row; never merge competing specs  
5. **Forbidden contamination patterns** — list from §4 invariants + legacy path tokens  
6. **Legacy path tokens (quarantine)** — `django_apps.shapez_asteroid`, `tests/unit/shapez_asteroid`, `mining_solver_cursor_sessions` (git only)  
7. **Current code paths** — `django_apps/asteroid_lab/...`, `tests/unit/asteroid_lab/`  
8. **PR playbook** — PR-A (this), PR-B (import gate), PR-C (replay/validation gate), PR-D (move), PR-E (dead code)  
9. **AI agent rules** — read topic row; no adjacent legacy refactor; regression gate before behavior change  
10. **Link** — `document_lifecycle.md` for status enum  

### Must not contain

- Duplicate full inventory tables (link only)  
- Solver implementation details  

---

## 7. Files touched

| File | Action |
|------|--------|
| `docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md` | Create (this spec) |
| `documents/ai/contamination_policy.md` | **Create** |
| `documents/index/document_inventory.md` | Extend (hot path, topic table, row fixes) |
| `documents/index/document_lifecycle.md` | Add `do_not_use_as_authority`, QUARANTINE note |
| `documents/ai/current_plan.md` | Add § Authority precedence |
| `documents/ai/START_HERE.md` | Replace mining-solver § with Asteroid Lab / RTTP |
| `documents/plans/asteroid_lab_optimization/README.md` | **Authority conflict fix** |
| `documents/Algorithm/solver_runtime/README.md` | Clarify historical vs RTTP runtime (short banner) |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md` | Front matter REPORT + quarantine |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_00_overview.md` | YAML quarantine block |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_01_optimization_input.md` | YAML quarantine block |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_04_route_probe.md` | YAML quarantine block |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` | YAML quarantine block |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_10_development_sequence.md` | YAML quarantine block |
| `documents/ai/checklist.md` | Optional one-line pointer to contamination_policy |
| `AGENTS.md` | Optional single Manual routing link |

**Optional same PR (same front matter template):** `asteroid_lab_02`–`07`, `09`, `11`–`14`, rollback baselines.

---

## 8. Acceptance criteria

### Grep (required before merge)

```powershell
# From repo root
rg "채굴 레이아웃 솔버 정본 후보" documents/
# Expected: 0 matches

rg "do_not_use_as_authority" documents/ai/contamination_policy.md documents/index/document_inventory.md
# Expected: ≥1 match each

rg "output-only" documents/ai/contamination_policy.md
# Expected: ≥1 match

rg "read-only" documents/ai/contamination_policy.md
# Expected: ≥1 match (validation)

rg "Asteroid Lab authority by topic" documents/index/document_inventory.md
# Expected: ≥1 match

rg "QUARANTINE" documents/plans/asteroid_lab_optimization/README.md documents/index/document_inventory.md
# Expected: matches with RTTP-active wording in README

rg "django_apps/asteroid_lab/optimization" documents/plans/asteroid_lab_optimization/README.md documents/ai/current_plan.md
# Expected: both describe active RTTP path
```

### Human review

- Side-by-side: `plans/asteroid_lab_optimization/README.md` vs `current_plan.md` — no contradictory "optimization removed globally" vs "RTTP active"
- `START_HERE.md` read order includes `contamination_policy.md` and topic table, not mining-solver table

### Tests (optional, should stay green)

```bash
python -m pytest tests/unit/architecture/ -v
```

No test file changes in PR-A.

---

## 9. PR-B / PR-C follow-up gates (outline)

### PR-B — Legacy import and path token gate

- **New:** `tests/unit/architecture/test_optimization_contamination_gates.py`
- **Scope:** `django_apps/asteroid_lab/optimization/**/*.py`
- **Forbidden imports:** `shapez_asteroid`, monolith `solver_runtime_pipeline`, `legacy`, `pass_first`, `lab_rttp_snapshot_compose` (except allowlist)
- **Forbidden tokens:** `solver_summary` as decision input inside search/commit/validation
- **Allowlist:** `replay/`, `services/solver_runtime_entry.py`, `services/lab_rttp_snapshot_compose.py`, `tests/`, `management/commands/`

### PR-C — Replay and validation boundary gate

- Consolidate existing `test_persistence_does_not_read_replay_frames`, `test_replay_*_import_boundary`
- Assert validation modules do not import replay ORM paths or mutate route_domain
- Reference `contamination_policy.md` + `asteroid_lab_08_validation.md`

### PR-D / PR-E

- PR-D: physical quarantine moves only after front matter + inventory stable  
- PR-E: dead code removal only after PR-B/C pass and import graph clean  

---

## 10. Rollback plan

PR-A is documentation-only. Rollback = revert the merge commit or PR.

| Risk | Mitigation |
|------|------------|
| Wrong topic row authority | Fix single inventory row; no code revert needed |
| Over-aggressive quarantine marking | Remove `do_not_use_as_authority` from specific file front matter |
| Broken relative links | Grep `](../` from edited files; fix in follow-up commit |

**Rollback command:**

```bash
git revert <pr-a-merge-commit-sha>
```

No database migration, no feature flag, no runtime dependency.

---

## References

- [`documents/index/document_lifecycle.md`](../../../documents/index/document_lifecycle.md)
- [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
- [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](2026-05-22-strip-solver-keep-recon-complete-design.md)
- [`docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md)
- [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)
