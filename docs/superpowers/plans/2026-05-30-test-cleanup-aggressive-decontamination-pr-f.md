# Decontamination PR-F — Aggressive Test Decontamination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or subagent-driven-development for F1–F5. **PR-F0 deletes no tests.**

**Goal:** Establish PR-F registry schema, full-package inventory, protected-contract map, and standing gates — then execute mechanical and package-scoped deletions in F1–F5 without weakening RTTP/replay/validation contracts.

**Architecture:** Extend `quarantine_registry.py` with `PrFAuditEntry` + `PR_F_*` tuples; evidence in `docs/superpowers/reports/2026-05-30-test-decontamination-inventory.md`; deletions only via `PR_F_APPROVED_DELETIONS` lifecycle (PR-E pattern).

**Tech Stack:** Python 3.12+, dataclasses, pytest `--collect-only`, ripgrep, PowerShell standing scripts.

**Spec:** [`../specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md`](../specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md)

**Branch (F0):** `feat/decontamination-pr-f0-inventory` from current `master`.

---

## File map (PR-F0 only)

| File | Action |
|------|--------|
| `tests/unit/architecture/quarantine_registry.py` | Modify — add `PrFAuditEntry`, `PR_F_*` tuples (empty approved) |
| `tests/unit/architecture/test_quarantined_paths_do_not_leak.py` | Modify — PR-F0 architecture tests |
| `docs/superpowers/reports/2026-05-30-test-decontamination-inventory.md` | Create — graded inventory |
| `docs/superpowers/specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md` | Exists — Status APPROVED after F0 merge |
| `documents/ai/current_plan.md` | Modify — PR-F0 ACTIVE → CLOSED after merge |
| `scripts/audit_test_inventory.ps1` | Create (optional) — helper to refresh inventory markdown |

**Do not modify in F0:** Any `test_*.py` under `tests/` except architecture registry tests. No `django_apps/**` production code.

---

## PR-F0 — Inventory + registry (no deletion)

### Task 0: Baseline

- [ ] **Step 1:** Sync `master`, create branch `feat/decontamination-pr-f0-inventory`
- [ ] **Step 2:** Record collection count

```powershell
python -m pytest --collect-only tests 2>&1 | Tee-Object -FilePath var/log/pr_f0_collect_before.txt
```

- [ ] **Step 3:** Green standing gates

```powershell
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
powershell -File scripts/test_reconstruction_narrow.ps1
```

### Task 1: Registry schema

- [ ] Add `InventoryGrade`, `PrFSlice`, `PrFAuditEntry` to `quarantine_registry.py`
- [ ] Initialize:
  - `PR_F_AGGRESSIVE_AUDIT_CANDIDATES = ()` (placeholder until Task 2)
  - `PR_F_APPROVED_DELETIONS = ()`
  - `PR_F_APPLIED_DELETIONS = ()`
  - `PR_F_PROTECTED_TESTS` — populate from spec §5 (concrete nodeids / file paths)

**Protected seed list (minimum — extend during inventory):**

```text
tests/unit/architecture/test_quarantined_paths_do_not_leak.py
tests/unit/architecture/test_optimization_contamination_gates.py
tests/unit/architecture/test_capacity_complete_map_sot_gates.py
tests/unit/asteroid_lab/test_rttp_commit_survivability.py
tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py
tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py
tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
tests/unit/asteroid_lab/test_final_validation_route_disjoint.py
tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py
```

(Add RTTP `-k rttp` critical modules per inventory pass.)

### Task 2: Package inventory passes

For each package, classify **every** `test_*.py` (and integration modules) into one grade (spec §3). Append `PrFAuditEntry` rows to registry **or** generate report first then paste into registry.

| Pass | Directory | Owner focus |
|------|-----------|-------------|
| 2a | `tests/unit/asteroid_lab/` | RTTP vs reconstruction vs Lab legacy |
| 2b | `tests/unit/game_data/` | dump guards vs obsolete importers |
| 2c | `tests/unit/web/` | Lab template / replay JS |
| 2d | `tests/integration/` | HTTP smoke vs dead routes |
| 2e | `tests/support/`, `tests/fixtures/` | consumer graph |
| 2f | `tests/unit/shapez_solver/`, `shapez_core/` | optional F5 backlog |

**Mechanical scans (feed F1 candidates):**

```powershell
# 0-byte test files
Get-ChildItem -Recurse tests -Filter test_*.py | Where-Object { $_.Length -eq 0 }

# Permanent skip markers
rg "@pytest\.mark\.skip" tests --glob "*.py" -n

# Legacy / superseded docstrings
rg "superseded|Legacy|obsolete|deprecated" tests --glob "*.py" -i -n
```

- [ ] Write [`../reports/2026-05-30-test-decontamination-inventory.md`](../reports/2026-05-30-test-decontamination-inventory.md) with tables per package (grade, path, reason, replacement, target_slice)
- [ ] Copy delete-candidate rows into `PR_F_AGGRESSIVE_AUDIT_CANDIDATES` (F1/F2 targets tagged)

**Known review rows (not pre-approved — verify in F0):**

| path | Initial grade | Notes |
|------|---------------|-------|
| `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` | `PROTECTED_CONTRACT` or `OBSOLETE_PRODUCT_PATH` | Product path superseded; helper may survive |
| `tests/unit/asteroid_lab/test_coordinate_frame_equivalence.py` | `DEFERRED_FEATURE_TEST` | G3 xfail gate — do not delete |
| `tests/unit/asteroid_lab/test_rttp_*macro*` (4 skips) | `DEFERRED_FEATURE_TEST` | PR-B macro pause |
| `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` | `INTENT_UNKNOWN` | verify shadow still in runtime |

### Task 3: Architecture tests (F0)

- [ ] Add tests from spec §9
- [ ] Run:

```powershell
python -m pytest tests/unit/architecture/test_quarantined_paths_do_not_leak.py -v --tb=short
python -m ruff check tests/unit/architecture/quarantine_registry.py tests/unit/architecture/test_quarantined_paths_do_not_leak.py
```

### Task 4: Docs and plan

- [ ] Set spec Status → APPROVED (if not already)
- [ ] `current_plan.md`: add **Decontamination PR-F0** ACTIVE; link spec + plan
- [ ] PR body: collection count, gate outputs, inventory summary counts by grade

### Task 5: F0 merge criteria

- [ ] `PR_F_APPROVED_DELETIONS == ()`
- [ ] `PR_F_AGGRESSIVE_AUDIT_CANDIDATES` non-empty (or documented why zero with follow-up issue)
- [ ] `PR_F_PROTECTED_TESTS` non-empty
- [ ] No test files deleted (git diff `tests/` only architecture + report)
- [ ] Standing gates green

---

## PR-F1 — Mechanical deletion (outline)

**F0 outcome (2026-05-30):** Inventory has **0** `BROKEN_OR_DEAD` and **0** `DUPLICATE_COVERAGE` rows → **F1 SKIP**; do not open an empty-delete PR. Proceed to **F2** (`asteroid_lab` human review).

**Branch:** `feat/decontamination-pr-f1-mechanical` — **not required** unless new F1 candidates appear after inventory refresh.

- [ ] Promote only `BROKEN_OR_DEAD` / `DUPLICATE_COVERAGE` rows with `target_slice="F1"` into `PR_F_APPROVED_DELETIONS`
- [ ] Apply deletions; move to `PR_F_APPLIED_DELETIONS`
- [ ] Gates: quarantine + collect delta (expect ≤10 items)

---

## PR-F2 — asteroid_lab (outline)

**Branch:** `feat/decontamination-pr-f2-asteroid-lab`

**F2 outcome (2026-05-30):** Human review of 2 `INTENT_UNKNOWN` rows → **both KEEP** (promoted to `PROTECTED_CONTRACT` in registry). **0** test file deletions. Next slice: **F3** (`game_data`).

- [x] Exclude any path matching `PR_F_PROTECTED_TESTS`
- [x] Review `test_lab_unified_replay_append.py` — keep (legacy helper contract)
- [x] Review `test_ga_evolution_shadow.py` — keep (PR-GA-2 import surface)
- [x] `test_pr_f_no_intent_unknown_after_f2` architecture gate
- [x] Narrow: `python -m pytest tests/unit/architecture/test_quarantined_paths_do_not_leak.py` + `tests/unit/asteroid_lab/ -k rttp`
- [x] `PR_F_APPROVED_DELETIONS` / `PR_F_APPLIED_DELETIONS` remain empty

---

## PR-F3 — game_data (outline)

**Branch:** `feat/decontamination-pr-f3-game-data`

- [ ] Narrow: `python -m pytest tests/unit/game_data/`
- [ ] Do not remove pinned-dump contract tests

---

## PR-F4 — web (outline)

**Branch:** `feat/decontamination-pr-f4-web`

- [ ] Narrow: `python -m pytest tests/unit/web/`

---

## PR-F5 — integration / fixtures / support (outline)

**Branch:** `feat/decontamination-pr-f5-integration`

- [ ] Fixture consumer graph required before fixture delete
- [ ] `python -m pytest tests/integration/`

---

## Verification matrix

| Slice | Narrow pytest | Standing scripts |
|-------|---------------|------------------|
| F0 | architecture only | all three |
| F1 | affected packages | quarantine |
| F2 | asteroid_lab `-k rttp` + recon narrow if needed | + contamination |
| F3 | game_data | quarantine |
| F4 | web | quarantine |
| F5 | integration | quarantine + full gate before final F5 merge |

**PR full gate** (final F5 or quarterly): `scripts/test_full.ps1` → ruff → mypy → black → `pytest`

---

## PR checklist template (F1–F5)

```markdown
## Decontamination PR-F{n}

- [ ] Approved deletions listed in registry before edit
- [ ] Replacements verified on disk
- [ ] No overlap with PR_F_PROTECTED_TESTS
- [ ] Package narrow gate PASS
- [ ] collect-only delta: before ___ after ___
- [ ] No production code change (or N/A with justification)
```
