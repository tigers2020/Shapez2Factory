# Decontamination PR-D — Quarantine & Stale Path Isolation (Design)

**Status:** CLOSED (merged to `master` `08320666`, PR #70, 2026-05-24)  
**Date:** 2026-05-24  
**Owner:** Release / Solver Architecture Lead  
**Track:** Decontamination PR-D (repo health; not RTTP algorithm)  
**Parent:** [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) §9 PR-D  
**Prerequisite:** PR-B **master CLOSED** (`e56ff048`, PR #69)  
**Implementation plan:** [`../plans/2026-05-24-decontamination-pr-d-quarantine.md`](../plans/2026-05-24-decontamination-pr-d-quarantine.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related:**

- [`2026-05-24-decontamination-pr-b-optimization-gates-design.md`](2026-05-24-decontamination-pr-b-optimization-gates-design.md) — optimization import canon (do not duplicate)
- [`documents/ai/contamination_policy.md`](../../../documents/ai/contamination_policy.md)
- [`documents/index/document_inventory.md`](../../../documents/index/document_inventory.md) — QUARANTINE rows

---

## Problem

PR-B locked **optimization/** import contamination. Stale authority and superseded paths can still re-enter the repo through:

| Gap | Risk |
|-----|------|
| Incomplete `do_not_use_as_authority` on historical plan snapshots | Agents implement against pre-RTTP `documents/plans/asteroid_lab_optimization/` |
| No machine-readable quarantine registry | “Suspicion” quarantine without evidence; PR-E deletion scope unclear |
| No gate on **active runtime entry** importing revival namespaces | `shapez_asteroid` / monolith paths could reappear outside `optimization/` |
| PR-E scheduled without explicit delete candidates | Unsafe bulk deletion |

PR-D is **isolation before deletion** — not PR-E.

---

## Goal

```text
PR-D = quarantine registry + architecture gates + doc front-matter sweep + PR-E candidate list
```

**No production solver behaviour change.** No physical file deletion (PR-E). No RTTP algorithm work.

**PR-D deletion policy:**

```text
PR-D may declare deletion candidates.
PR-D must not physically delete them.
PR-E owns deletion and deletion verification.
```

---

## Non-goals

- Dead code deletion (PR-E only — PR-D declares candidates only)
- RTTP algorithm changes (deferred commit retry, GA, etc.)
- Replay / validation semantics changes
- UI behaviour changes
- Duplicating PR-B `optimization/**` import rules (cross-reference only)
- Duplicating B-CS3/B-CS4 behavioural audits
- Moving trees to `documents/quarantine/` unless a file is already inventory-listed and move is zero-risk (optional sub-task; default = front matter + registry only)

---

## Precondition — Entry Gate (master baseline)

Recorded **2026-05-24** on `master` @ `9e70d169` (post PR-B docs):

| Gate | Command | Result |
|------|---------|--------|
| Reconstruction narrow | `scripts/test_reconstruction_narrow.ps1` | 55 passed |
| RTTP narrow | `pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map"` | 127 passed |
| PR-B standing | `scripts/test_optimization_contamination.ps1` | 4 passed |

Ops smoke (`run_solver --slug copy-import-495e552c`) remains **recommended, non-blocking** on env/DB failure.

---

## PR-D vs PR-B boundary

| Layer | Owner | Scope |
|-------|--------|--------|
| **PR-B** | `test_optimization_contamination_gates.py` | `django_apps/asteroid_lab/optimization/**` imports + decision-path tokens |
| **PR-D** | `test_quarantined_paths_do_not_leak.py` | Active runtime roots must not import **registry-listed** quarantined modules; doc quarantine paths cannot be cited as implementation authority from code |

---

## §1 — Quarantine registry (machine-readable)

**Source of truth file (new):**

```text
tests/unit/architecture/quarantine_registry.py
```

### 1.0 Two-tier registry (do not mix)

| Constant | Purpose | Test layer |
|----------|---------|------------|
| `QUARANTINED_MODULE_PREFIXES` | Revival / superseded **import module** strings | AST import graph from active runtime roots (§2) |
| `QUARANTINED_DOC_PATHS` | Stale **documentation trees** (repo-relative) | Front matter + disposition tests; not AST-importable |

```text
module prefix tier = AST import leakage checks
doc path tier       = document / roadmap stale reference checks
```

Do not store doc paths in the module-prefix tuple or vice versa.

### 1.1 Registry entry schema

Each entry is a dict with **required** keys:

| Field | Type | Meaning |
|-------|------|---------|
| `id` | `str` | Stable registry key (kebab-case) |
| `kind` | `"module_prefix"` \| `"module"` \| `"doc_tree"` | What is quarantined |
| `target` | `str` | Module prefix, full module, or repo-relative doc directory |
| `reason` | `str` | Evidence-based rationale (not “suspicious”) |
| `replacement` | `str` \| `None` | Active replacement path or `None` if N/A |
| `delete_candidate` | `bool` | PR-E may delete when `True` |
| `owner_next_step` | `"PR-E"` \| `"maintain"` \| `"none"` | Follow-up owner |

**Evidence rule:** Every entry must cite at least one of:

- Not imported by active runtime scan roots (see §2)
- Not a direct target of standing pytest gates
- Marked superseded in inventory / parent spec
- PR-B already forbids the dependency direction for optimization

### 1.2 Initial registry entries (v1 — evidence as of 2026-05-24)

#### Revival-blocked module prefixes (no package on `master`)

| id | target | reason | replacement |
|----|--------|--------|-------------|
| `revival-shapez-asteroid` | `django_apps.shapez_asteroid` | Package removed; inventory forbids revival | `django_apps.asteroid_lab` |
| `revival-shapez-asteroid-short` | `shapez_asteroid` | Legacy namespace token | same |
| `revival-solver-runtime-pipeline` | `solver_runtime_pipeline` | Monolith pipeline removed (strip-solver) | `django_apps.asteroid_lab.optimization.pipeline` |
| `revival-pass-first` | `pass_first` | Legacy pass-first path family | RTTP pipeline + commit |

#### Doc trees (QUARANTINE — not importable; enforced via front matter + optional code string scan)

| id | target | reason | replacement | delete_candidate |
|----|--------|--------|---------------|------------------|
| `doc-plans-asteroid-lab-optimization` | `documents/plans/asteroid_lab_optimization/` | Inventory QUARANTINE; pre-RTTP snapshots | `documents/Algorithm/asteroid_lab_*.md` + `docs/superpowers/specs/` | `False` (keep as history) |
| `doc-algorithm-solver-runtime-series` | `documents/Algorithm/solver_runtime/` | ARCHIVED Phase A–M orchestration series | `django_apps/asteroid_lab/optimization/` + RTTP specs | `False` |

#### Active modules that are **not** quarantined (explicit negatives — do not add)

These are used by current runtime and must **not** appear in the quarantine import block list:

- `django_apps.asteroid_lab.services.lab_optimization_milestone_payload` — used by `solver_runtime_entry`
- `django_apps.asteroid_lab.services.lab_rttp_snapshot_compose` — used by runtime entry / Lab (not optimization)
- `django_apps.asteroid_lab.genetic_sample` — admin / seed commands only; blocked from `optimization/` by PR-B

### 1.3 PR-E deletion candidate list (v1)

PR-D exposes `PR_E_DELETE_CANDIDATES` (repo-relative paths). **PR-D must not delete these files.**

| Candidate path | Notes |
|----------------|-------|
| `tests/unit/asteroid_lab/test_service_import_boundaries.py` | 0-byte; audit recommends delete in PR-E ([`docs/ai/test_cleanup_audit.md`](../../ai/test_cleanup_audit.md)) |

Revival namespaces have no on-disk modules — nothing for PR-E to delete.

PR-E must not delete quarantined **doc trees** without separate human approval.

---

## §2 — Active runtime scan roots and import policy

### 2.1 Direct roots (closed set)

```text
django_apps/asteroid_lab/services/solver_runtime_entry.py
django_apps/asteroid_lab/optimization/pipeline.py
django_apps/asteroid_lab/optimization/reconstruction_adapter.py
django_apps/asteroid_lab/management/commands/run_solver.py
django_apps/web/views/public_pages.py
```

### 2.2 Scan policy (v1 — bounded, not full-repo graph)

```text
1. Parse direct imports in each root file.
2. Follow only django_apps.asteroid_lab.* imports transitively.
3. Max transitive depth = 2 (package-internal).
4. Ignore third-party / stdlib imports.
5. No unbounded full-repo import graph.
6. No rglob of entire django_apps/**.
```

**Rule:** No collected import module string may match any entry in `QUARANTINED_MODULE_PREFIXES` (prefix or substring match per entry definition).

**Overlap with PR-B:** PR-B owns `optimization/**/*.py` rglob. PR-D owns **only** the closed roots above plus bounded transitive `django_apps.asteroid_lab.*` follow-up. Shared revival prefixes are intentional; PR-D does not re-scan all of `optimization/` as a substitute for PR-B.

---

## §3 — Architecture tests (new)

**File:** `tests/unit/architecture/test_quarantined_paths_do_not_leak.py`

| Test | Asserts |
|------|---------|
| `test_quarantined_modules_are_declared_in_registry` | `QUARANTINED_MODULE_PREFIXES` + `QUARANTINED_DOC_PATHS` well-formed; unique ids |
| `test_active_runtime_paths_do_not_import_quarantined_modules` | §2 bounded scan |
| `test_quarantined_doc_paths_have_disposition` | Every `QUARANTINED_DOC_PATHS` tree: `do_not_use_as_authority: true` on all `*.md` |
| `test_quarantine_registry_has_pr_e_disposition` | `PR_E_DELETE_CANDIDATES` explicit; paths exist; not deleted in this PR |
| `test_quarantine_gate_does_not_overlap_pr_b_scope` | PR-D scans closed roots only, not `optimization/**` rglob |

**Not in PR-D:**

- Scanning all of `django_apps/**` (use PR-B + `test_django_app_import_boundaries.py` for app matrix)
- Behavioural replay/validation audits (B-CS3/4)

---

## §4 — Documentation deliverables

| Artifact | Action |
|----------|--------|
| `documents/plans/asteroid_lab_optimization/*.md` | Add/complete YAML front matter template per [`document_lifecycle.md`](../../../documents/index/document_lifecycle.md) QUARANTINE |
| `documents/ai/current_plan.md` | PR-D **ACTIVE** → **CLOSED** with merge SHA |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Decontamination PR-D row |
| `documents/index/document_inventory.md` | Optional one-line pointer to `quarantine_registry.py` as machine registry (if not already) |

**Front matter template (minimum):**

```yaml
---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: pre-RTTP plan snapshot; see documents/Algorithm/ and docs/superpowers/specs/
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
---
```

---

## §5 — Gate inclusion policy

| Gate | PR-D tests included? |
|------|----------------------|
| `scripts/test_optimization_contamination.ps1` | **No** (PR-B only) |
| `scripts/test_reconstruction_narrow.ps1` | **No** |
| **New (optional):** `scripts/test_quarantine_registry.ps1` | **Yes** — thin wrapper for PR-D pytest + ruff on registry test files |
| `scripts/test_full.ps1` / CI | **Yes** via `tests/unit/architecture/` collection |

---

## §6 — Closure definition

**PR-D is CLOSED (master) when:**

1. `quarantine_registry.py` exists with v1 entries documented above (amendments allowed with evidence)
2. `test_quarantined_paths_do_not_leak.py` green on `master`
3. All `documents/plans/asteroid_lab_optimization/*.md` files have `do_not_use_as_authority: true`
4. PR-E candidate list explicit in registry + test
5. No production solver behaviour change (diff limited to tests, registry module, docs, optional script)
6. `current_plan.md` + roadmap updated with merge SHA

**Status vocabulary (same as PR-B):**

```text
branch-local CLOSED = implementation complete on feature branch
master CLOSED       = squash merge to master recorded
```

---

## §7 — Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Quarantine “suspicion” without evidence | Registry schema requires `reason` + evidence rule §1.2 |
| False positive on `legacy` in unrelated module names | PR-D uses **registry list**, not broad substring bans |
| Confusion with PR-B | § PR-D vs PR-B boundary table |
| PR-E deletes active code | `delete_candidate` + explicit negatives §1.2 |
| Doc-only PR dismissed as low value | Front matter + pytest doc-tree gate prevents agent authority drift |

---

## Self-review checklist

- [x] PR-D does not duplicate PR-B optimization import gate
- [x] PR-D does not duplicate B-CS3/4 behavioural audits
- [x] No dead code deletion in PR-D scope
- [x] PR-E candidate list explicit
- [x] Revival entries evidence-based (packages absent on master)
- [x] Active runtime modules explicitly excluded from quarantine

---

## Rollback

Revert PR-D merge. Registry and tests are additive; doc front matter can remain without runtime effect.
