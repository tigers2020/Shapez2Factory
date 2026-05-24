# Repository Decontamination Authority Repair (PR-A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair document authority for Asteroid Lab / RTTP so agents use `document_inventory.md` topic rows and `contamination_policy.md` instead of quarantined plan snapshots—without changing solver code or tests.

**Architecture:** Extend existing governance (`document_inventory`, `document_lifecycle`, `START_HERE`, `current_plan`); add thin operational policy; fix the `asteroid_lab_optimization/README.md` vs `current_plan.md` conflict; mark minimum historical docs `do_not_use_as_authority`. No parallel `authority_index.md`.

**Tech Stack:** Markdown/YAML front matter, `rg` acceptance checks, optional `pytest tests/unit/architecture/` smoke.

**Spec:** [`../specs/2026-05-24-repo-decontamination-authority-design.md`](../specs/2026-05-24-repo-decontamination-authority-design.md)

---

## File map (PR-A)

| File | Responsibility |
|------|----------------|
| `documents/ai/contamination_policy.md` | Forbidden patterns, PR playbook, AI rules |
| `documents/index/document_inventory.md` | Hot path + per-topic authority table |
| `documents/index/document_lifecycle.md` | `do_not_use_as_authority`, QUARANTINE label |
| `documents/ai/current_plan.md` | Authority precedence section |
| `documents/ai/START_HERE.md` | Fixed read order for RTTP |
| `documents/plans/asteroid_lab_optimization/README.md` | Strip vs RTTP conflict fix |
| `documents/Algorithm/solver_runtime/README.md` | Historical vs RTTP banner |
| `documents/plans/asteroid_lab_optimization/asteroid_lab_*.md` (minimum 6) | Quarantine YAML |

---

### Task 1: Create `contamination_policy.md`

**Files:**
- Create: `documents/ai/contamination_policy.md`

- [ ] **Step 1: Create the policy file**

Create `documents/ai/contamination_policy.md` with this content:

```markdown
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
```

- [ ] **Step 2: Verify file exists**

Run:

```powershell
Test-Path documents/ai/contamination_policy.md
```

Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add documents/ai/contamination_policy.md
git commit -m "docs: add contamination policy for authority repair"
```

**Rollback:** `git revert HEAD`

---

### Task 2: Patch `document_inventory.md`

**Files:**
- Modify: `documents/index/document_inventory.md`

- [ ] **Step 1: Update header and add hot path**

At top after the scope paragraph, set `Reference date: 2026-05-24` and add section:

```markdown
## Hot path (Asteroid Lab / RTTP)

1. Code + tests → [`documents/ai/current_plan.md`](../ai/current_plan.md)
2. **Topic row** in § Asteroid Lab authority by topic (below) — **conflict resolver**
3. Row-designated spec or Algorithm doc
4. [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md)

**QUARANTINE (never implementation authority):** [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/)

There is no separate `authority_index.md`; this file is the sole authority map.
```

- [ ] **Step 2: Add per-topic table**

Insert section **「Asteroid Lab authority by topic」** with the full table from spec §5 (copy all rows from [`2026-05-24-repo-decontamination-authority-design.md`](../specs/2026-05-24-repo-decontamination-authority-design.md)).

- [ ] **Step 3: Fix existing rows**

In **Active work · backlog** table:

- Change `documents/Algorithm/solver_runtime/` status note to **HISTORICAL** — RTTP runtime is `current_plan` + `optimization/`, not Phase A–M series.
- Add row for `documents/ai/contamination_policy.md` — `CANON`, governance.
- Add subsection or rows for merged `docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`, B2-T2/T3 specs (CLOSED), Track D parent spec (ACTIVE).

Under `documents/plans/` row, add footnote: **except** `plans/asteroid_lab_optimization/` = QUARANTINE.

- [ ] **Step 4: Grep acceptance**

Run:

```powershell
rg "Asteroid Lab authority by topic" documents/index/document_inventory.md
rg "contamination_policy" documents/index/document_inventory.md
```

Expected: at least one match each.

- [ ] **Step 5: Commit**

```bash
git add documents/index/document_inventory.md
git commit -m "docs: extend inventory with RTTP topic authority table"
```

**Rollback:** `git revert HEAD`

---

### Task 3: Patch `document_lifecycle.md`

**Files:**
- Modify: `documents/index/document_lifecycle.md`

- [ ] **Step 1: Extend recommended header template**

In § recommended document header YAML example, add:

```yaml
do_not_use_as_authority: false
```

- [ ] **Step 2: Add operational QUARANTINE note**

After § status enum table, add:

```markdown
### Operational label: QUARANTINE

Inventory may label paths **QUARANTINE** for AI routing. Map to lifecycle `ARCHIVED` or `SUPERSEDED` and set `do_not_use_as_authority: true` in front matter. QUARANTINE docs are historical context only — not implementation authority.
```

- [ ] **Step 3: Commit**

```bash
git add documents/index/document_lifecycle.md
git commit -m "docs: document QUARANTINE label and do_not_use_as_authority"
```

---

### Task 4: Patch `current_plan.md`

**Files:**
- Modify: `documents/ai/current_plan.md` (after **Runtime (code canonical reference):** block)

- [ ] **Step 1: Insert Authority precedence section**

```markdown
## Authority precedence

On document conflict between Algorithm and superpowers there is **no global precedence rule** — follow the [`document_inventory.md`](../index/document_inventory.md) **§ Asteroid Lab authority by topic** row.

1. Code + tests: `django_apps/asteroid_lab/{reconstruction,optimization,contracts}/`, `tests/unit/asteroid_lab/`
2. This file — active queue and runtime pointer
3. `docs/superpowers/specs/` — merged RTTP/B2 specs (per topic row)
4. `documents/Algorithm/asteroid_lab_*.md` — stable DTO / route / validation / replay semantics
5. `document_inventory.md` — doc status and topic routing
6. `documents/plans/asteroid_lab_optimization/` — **QUARANTINE** (historical snapshots only; `do_not_use_as_authority`)
7. `documents/Algorithm/solver_runtime/` — historical Phase A–M unless this file promotes a subsection
8. `REPORT`, `documents/debug/`, `documents/archive/` — observation only

Operational rules: [`contamination_policy.md`](contamination_policy.md). Design: [`docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md`](../../docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md).
```

- [ ] **Step 2: Commit**

```bash
git add documents/ai/current_plan.md
git commit -m "docs: add authority precedence to current_plan"
```

---

### Task 5: Patch `START_HERE.md`

**Files:**
- Modify: `documents/ai/START_HERE.md`

- [ ] **Step 1: Update read order**

After item 3 (`document_inventory.md`), insert:

```markdown
3.5. [`contamination_policy.md`](contamination_policy.md) — forbidden patterns (on conflict, inventory topic row wins)
```

- [ ] **Step 2: Replace § Solver work default canon**

Delete lines referencing **mining layout solver canonical candidate**. Replace entire section with:

```markdown
## Asteroid Lab / RTTP work

1. [`current_plan.md`](current_plan.md) — active runtime paths and queue
2. [`../index/document_inventory.md`](../index/document_inventory.md) — **§ Asteroid Lab authority by topic**
3. [`contamination_policy.md`](contamination_policy.md) — forbidden patterns and PR playbook
4. Topic authority from inventory row (`docs/superpowers/specs/` or `documents/Algorithm/asteroid_lab_*.md`)
5. Code: `django_apps/asteroid_lab/` + `tests/unit/asteroid_lab/`

The following contracts take precedence over older plans/reports (if the topic row is more specific, **row wins**):

- Placement ≠ Commit; route probe at candidate creation
- validation read-only; replay/artifacts output-only
- single `RouteDomainSnapshotBuilder` owner

**Forbidden:** Do not use `documents/plans/asteroid_lab_optimization/` as implementation authority.

**Forbidden:** Do not use `django_apps.shapez_asteroid`, `tests/unit/shapez_asteroid` as current work paths.
```

- [ ] **Step 3: Grep — no stale pointer**

Run:

```powershell
rg "mining layout solver canonical candidate" documents/
```

Expected: **0 matches**

- [ ] **Step 4: Commit**

```bash
git add documents/ai/START_HERE.md
git commit -m "docs: fix START_HERE for RTTP authority routing"
```

---

### Task 6: Fix `plans/asteroid_lab_optimization/README.md`

**Files:**
- Modify: `documents/plans/asteroid_lab_optimization/README.md`

- [ ] **Step 1: Replace YAML front matter**

```yaml
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
```

- [ ] **Step 2: Replace body bullets (lines ~10–16)**

```markdown
# asteroid_lab_optimization plans (QUARANTINE)

> **QUARANTINE:** `do_not_use_as_authority: true`. Historical plan **snapshots** only.

- **Strip-solver (2026-05-22):** removed pre-RTTP **monolith / shadow / RD** pipeline — not the current RTTP package.
- **Current runtime (2026-05-24):** `django_apps/asteroid_lab/optimization/` — RTTP Hybrid C when `ASTEROID_LAB_RTTP_ENABLED=True` — see [`documents/ai/current_plan.md`](../../ai/current_plan.md).
- **Stable contracts:** prefer [`documents/Algorithm/asteroid_lab_*.md`](../../Algorithm/) and merged [`docs/superpowers/specs/`](../../../docs/superpowers/specs/) per [`document_inventory.md`](../../index/document_inventory.md) topic rows.
- **This directory:** do not edit for new features; do not cite as implementation authority.

## Doc sweep (2026-05-23)

Each `asteroid_lab_*.md` file has a top-of-file banner pointing at **`documents/Algorithm/`** when a matching CANON doc exists.

- **PR-F:** Product code uses **island-local** `(x, y)` only; dense server HUD removed.
```

- [ ] **Step 3: Grep — RTTP active in README**

Run:

```powershell
rg "django_apps/asteroid_lab/optimization" documents/plans/asteroid_lab_optimization/README.md
rg "QUARANTINE" documents/plans/asteroid_lab_optimization/README.md
```

Expected: matches for both.

- [ ] **Step 4: Commit**

```bash
git add documents/plans/asteroid_lab_optimization/README.md
git commit -m "docs: fix optimization plans README RTTP vs strip conflict"
```

---

### Task 7: Patch `solver_runtime/README.md` banner

**Files:**
- Modify: `documents/Algorithm/solver_runtime/README.md`

- [ ] **Step 1: Add banner after existing front matter block (before H1)**

Insert after line 7 (`---` if present) or immediately after YAML:

```markdown
> **Runtime authority (2026-05-24):** Active solver is **RTTP Hybrid C** in `django_apps/asteroid_lab/optimization/` when `ASTEROID_LAB_RTTP_ENABLED=True` — see [`documents/ai/current_plan.md`](../../ai/current_plan.md). This directory documents the **historical Solver-button Phase A–M** orchestration series, not the RTTP implementation contract.
```

- [ ] **Step 2: Commit**

```bash
git add documents/Algorithm/solver_runtime/README.md
git commit -m "docs: clarify solver_runtime historical vs RTTP runtime"
```

---

### Task 8: Quarantine front matter (minimum set)

**Files:**
- Modify:
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_00_overview.md`
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_01_optimization_input.md`
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_04_route_probe.md`
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md`
  - `documents/plans/asteroid_lab_optimization/asteroid_lab_10_development_sequence.md`

- [ ] **Step 1: Prepend YAML to each file (keep existing markdown banner below)**

For `asteroid_lab_01`, `04`, `08`, `10`, `00` — prepend:

```yaml
---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/<same_stem>.md
authority_for_implementation: documents/Algorithm/<STEM>.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---
```

Replace `<STEM>` with matching filename stem (e.g. `asteroid_lab_01_optimization_input`).

For `asteroid_lab_progress_report_2026-05-17.md`:

```yaml
---
status: REPORT
do_not_use_as_authority: true
last_reviewed: 2026-05-24
---
```

- [ ] **Step 2: Count quarantine markers**

Run:

```powershell
rg -l "do_not_use_as_authority: true" documents/plans/asteroid_lab_optimization/
```

Expected: **≥ 6** files (README + 5 minimum, or more if optional batch done).

- [ ] **Step 3: Commit**

```bash
git add documents/plans/asteroid_lab_optimization/
git commit -m "docs: quarantine front matter on historical optimization plans"
```

---

### Task 9: Optional — `checklist.md` and `AGENTS.md` links

**Files:**
- Modify: `documents/ai/checklist.md` (optional)
- Modify: `AGENTS.md` (optional)

- [ ] **Step 1: Add one line to checklist under shapez_asteroid removal**

```markdown
- Authority repair: [`contamination_policy.md`](contamination_policy.md) + [`document_inventory.md`](../index/document_inventory.md) topic table (2026-05-24).
```

- [ ] **Step 2: Add to AGENTS.md Manual routing table footnote**

Under `asteroid_lab` or `solver` row, add: `documents/ai/contamination_policy.md` for stale-doc rules.

- [ ] **Step 3: Commit (if edited)**

```bash
git add documents/ai/checklist.md AGENTS.md
git commit -m "docs: link contamination policy from checklist and AGENTS"
```

Skip commit if YAGNI — not required for PR-A acceptance.

---

### Task 10: Final grep acceptance and architecture smoke

**Files:** none (verification only)

- [ ] **Step 1: Run full grep suite from spec §8**

```powershell
cd f:\Python_Projects\shapez2Factory
rg "mining layout solver canonical candidate" documents/
rg "do_not_use_as_authority" documents/ai/contamination_policy.md documents/index/document_inventory.md
rg "output-only" documents/ai/contamination_policy.md
rg "read-only" documents/ai/contamination_policy.md
rg "Asteroid Lab authority by topic" documents/index/document_inventory.md
```

All expected outcomes per spec §8.

- [ ] **Step 2: Optional architecture pytest**

```bash
python -m pytest tests/unit/architecture/ -v
```

Expected: all passed (no test changes in PR-A).

- [ ] **Step 3: Human diff review**

Confirm `README.md` (plans) and `current_plan.md` both mention `django_apps/asteroid_lab/optimization/` as active RTTP without global "optimization deleted" wording.

- [ ] **Step 4: Squash or final commit message (if using single PR)**

```bash
# If squashing locally before PR:
git log --oneline -10
```

PR title suggestion: `docs: establish authority repair and contamination policy (PR-A)`

**Rollback:** Revert entire PR branch; no runtime impact.

---

## Plan self-review

| Spec § | Task |
|--------|------|
| §1 Problem | Motivation in spec; Task 6 fixes case A |
| §2 Goals | Tasks 1–8 |
| §3 Non-goals | No code tasks |
| §4 Precedence | Tasks 4, 1 |
| §5 Topic table | Task 2 |
| §6 Policy contract | Task 1 |
| §7 Files | File map + tasks |
| §8 Acceptance | Task 10 |
| §9 PR-B/C | Spec only; not in PR-A tasks |
| §10 Rollback | Per-task rollback notes |

**Placeholder scan:** None — all steps have concrete paths and content.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-repo-decontamination-authority-pr-a.md`.

**Spec for review:** `docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — one subagent per task (1–10), review between tasks  
2. **Inline Execution** — run tasks 1–10 in this session with checkpoints after Tasks 2, 6, and 10  

Which approach do you want for PR-A implementation?
