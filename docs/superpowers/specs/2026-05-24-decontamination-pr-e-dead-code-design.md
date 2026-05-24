# Decontamination PR-E — Dead Code Deletion (Design)

**Status:** branch-local CLOSED (implementation on `feat/decontamination-pr-e-dead-code`; merge pending)  
**Date:** 2026-05-24  
**Owner:** Release / Solver Architecture Lead  
**Track:** Decontamination PR-E (repo health; not RTTP algorithm)  
**Parent:** [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) §9 PR-E  
**Prerequisite:** PR-D **master CLOSED** (`08320666`, PR #70); PR-B **master CLOSED** (`e56ff048`, PR #69)  
**Implementation plan:** [`../plans/2026-05-24-decontamination-pr-e-dead-code.md`](../plans/2026-05-24-decontamination-pr-e-dead-code.md)  
**Related:**

- [`2026-05-24-decontamination-pr-d-quarantine-design.md`](2026-05-24-decontamination-pr-d-quarantine-design.md) — quarantine registry; PR-D declared candidates only
- [`2026-05-24-decontamination-pr-b-optimization-gates-design.md`](2026-05-24-decontamination-pr-b-optimization-gates-design.md) — optimization import canon
- Evidence report (non-authority): [`../reports/2026-05-24-test-cleanup-audit.md`](../reports/2026-05-24-test-cleanup-audit.md)

**Naming:** **Decontamination PR-E** (this document) is **not** RTTP PR-E (`OptimizationInput.coord_frame`, macro commit, coordinate-tagged-frames). Do not mix tracks in branch names, commits, or plan rows.

---

## §1 — Identity and principles

PR-E only deletes artifacts already declared by PR-D or **first promoted into** `PR_E_DELETE_CANDIDATES` with machine-checkable evidence. No speculative deletion. No production runtime, solver, replay semantics, validation behaviour, or RTTP algorithm change.

```text
Audit is evidence, not authority.
Registry is the mechanical source of truth for deletion.
No file or pytest node may be deleted unless it is first listed in
PR_E_DELETE_CANDIDATES with reason, evidence, replacements (tuple), and kind.
```

**Forbidden:**

- Deleting because `test_cleanup_audit.md` (or any audit report) says so **without** a registry record
- Deleting quarantined doc trees (`QUARANTINED_DOC_PATHS` with `delete_candidate=False`)
- Deleting revival namespace markers when no on-disk module exists
- RTTP / coord_frame / macro commit work under the “PR-E” label

---

## §2 — Registry schema (final committed state)

**File:** `tests/unit/architecture/quarantine_registry.py`

PR-D v1 used `tuple[str, ...]`. PR-E replaces pending candidates with typed records and leaves the branch in **applied-only** state (no before/after dual-mode tests).

```python
@dataclass(frozen=True, slots=True)
class PrEDeleteCandidate:
    path: str  # repo-relative file path OR pytest nodeid
    kind: Literal["file", "pytest_node"]
    reason: str
    evidence: str
    replacements: tuple[str, ...]  # empty () when N/A; each entry machine-verifiable
```

**Final state of the PR-E branch (single committed end state, before merge):**

```python
PR_E_DELETE_CANDIDATES: tuple[PrEDeleteCandidate, ...] = ()

PR_E_APPLIED_DELETIONS: tuple[PrEDeleteCandidate, ...] = (
    # three records — see §3
)
```

**Lifecycle rule:**

```text
PR_E_APPLIED_DELETIONS is populated in the final committed state of PR-E, before merge.
After PR-E implementation, PR_E_DELETE_CANDIDATES must be empty.
```

Do **not** model “fill `PR_E_APPLIED_DELETIONS` only after merge” — reviewers and gates must see applied-only state on the feature branch tip.

**Promotion workflow (implementation order):**

1. Expand `PR_E_DELETE_CANDIDATES` with all §3 records (from PR-D v1 path + audit-backed promotions).
2. Verify every entry in each record’s `replacements` tuple exists (§3 table).
3. Apply deletions (files removed; pytest function removed from module).
4. Move every record to `PR_E_APPLIED_DELETIONS`; set `PR_E_DELETE_CANDIDATES = ()`.
5. Update architecture tests to assert applied-only state (§4).

---

## §3 — Deletion inventory (v2)

All rows must exist in `PR_E_DELETE_CANDIDATES` **before** physical deletion. After deletion, the same rows appear only in `PR_E_APPLIED_DELETIONS`.

| id | path | kind | reason | evidence | replacements (verified on master pre-PR-E) |
|----|------|------|--------|----------|---------------------------------------------|
| E-1 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | `file` | `zero_byte_test_file` | 0-byte file; collects zero tests | `tests/unit/architecture/test_django_app_import_boundaries.py`, `tests/unit/architecture/test_optimization_contamination_gates.py` |
| E-2 | `tests/test_smoke.py` | `file` | `meaningless_placeholder` | sole test is `assert True`; CI and pytest collection already cover test discovery | `tests/integration/api/test_health.py` |
| E-3 | `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py::test_lab_adapter_members_are_valid_replay_event_types` | `pytest_node` | `duplicate_coverage` | loops `SUPPORTED_BY_9B_LAB_ADAPTER` with `member in ReplayEventType` only | `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py::test_unified_replay_event_type_adapter_coverage_matrix_is_explicit` |

**E-3 contract:** The parent file **remains**. Only the named function is removed.

**Explicit exclusions (out of scope):** quarantined doc trees; revival prefixes with no on-disk modules; audit rows marked `NEEDS_HUMAN_DECISION`; fixture-shrink / slow-gate items.

---

## §4 — Gate and architecture tests (applied-only)

**File:** `tests/unit/architecture/test_quarantined_paths_do_not_leak.py`

Replace PR-D disposition test `test_quarantine_registry_has_pr_e_disposition` (pending paths must exist) with **applied-only** checks on the PR-E branch tip:

| Test | Asserts |
|------|---------|
| `test_pr_e_delete_candidates_empty` | `PR_E_DELETE_CANDIDATES == ()` |
| `test_pr_e_applied_deletions_recorded` | `PR_E_APPLIED_DELETIONS` non-empty; ids/paths unique; kinds valid |
| `test_pr_e_applied_files_absent` | For each `kind=="file"` entry, `path` is not a file under repo root |
| `test_pr_e_applied_pytest_nodes_absent` | For each `kind=="pytest_node"` entry, function name absent from module AST (or node not in `pytest --collect-only` output) |
| `test_pr_e_replacement_targets_exist` | For every `replacement` in each record’s `replacements` tuple: file path is an on-disk file, or pytest nodeid resolves via module AST (`def name`) |

Retain PR-D tests unchanged where still valid:

- `test_quarantined_modules_are_declared_in_registry`
- `test_active_runtime_paths_do_not_import_quarantined_modules`
- `test_quarantined_doc_paths_have_disposition`
- `test_quarantine_gate_does_not_overlap_pr_b_scope`

**Optional (recommended):** `test_pr_e_no_runtime_import_of_deleted_paths` — no `django_apps` / `tests` Python import of deleted file basenames (archive markdown mentions allowed).

**Standing gate:** `scripts/test_quarantine_registry.ps1` — unchanged wrapper; must stay green.

**Not in PR-E:** PR-B optimization gate implementation changes (only run standing script).

---

## §5 — Evidence report (non-authority)

| Artifact | Action |
|----------|--------|
| [`docs/superpowers/reports/2026-05-24-test-cleanup-audit.md`](../reports/2026-05-24-test-cleanup-audit.md) | Add/move from draft `docs/ai/test_cleanup_audit.md`; fix stale references (e.g. removed `test_optimization_milestone_import_boundary.py`); mark PR-E applied rows |

```text
test_cleanup_audit.md is evidence-only.
It is not a source of deletion authority.
Only PR_E_DELETE_CANDIDATES / PR_E_APPLIED_DELETIONS are mechanical authority.
```

Roadmap may link the report as **evidence report** only.

---

## §6 — Verification

### Blocking

```powershell
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
python -m pytest tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py -v --tb=short
python -m pytest --collect-only tests
```

### Recommended (non-blocking unless CI policy changes)

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

### Collection delta (document in PR body and plan evidence)

```text
Expected collection delta:
- one 0-byte file removed: no collected test delta
- tests/test_smoke.py removed: -1 test
- one replay pytest node removed: -1 test
Total expected test item delta: -2
```

Record actual before/after counts from `pytest --collect-only tests` on the PR branch tip.

---

## §7 — Documentation deliverables

| Artifact | Action |
|----------|--------|
| `documents/ai/current_plan.md` | PR-E ACTIVE → CLOSED with merge SHA |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Decontamination PR-E row CLOSED |
| [`2026-05-24-decontamination-pr-d-quarantine-design.md`](2026-05-24-decontamination-pr-d-quarantine-design.md) | Optional cross-link: PR-E executed §1.3 candidates |
| This spec | Status → CLOSED after merge |

---

## §8 — PR-E closure definition

**PR-E is CLOSED when:**

```text
- PR_E_DELETE_CANDIDATES is empty
- PR_E_APPLIED_DELETIONS records all applied file / pytest_node deletions
- deleted files are absent
- deleted pytest nodes are absent
- all `replacements` targets are present on disk / in AST
- quarantine registry gate is green
- optimization contamination gate is green
- collect-only delta is documented
- no runtime / solver / RTTP algorithm behavior changed
```

**Status vocabulary:**

```text
branch-local CLOSED = implementation complete on feature branch (applied-only registry)
master CLOSED       = squash merge to master recorded
```

---

## §9 — Out of scope

- RTTP algorithm, deferred commit retry, coord_frame / macro commit (RTTP PR-E/F)
- `QUARANTINED_DOC_PATHS` physical deletion
- Revival namespace on-disk modules (none listed)
- Registry structure redesign beyond `PrEDeleteCandidate` + applied tuples
- Audit-only deletion without registry promotion
- Runtime behaviour, replay semantics, validation behaviour changes

---

## §10 — Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Audit treated as delete authority | §1 principles; evidence report disclaimer §5 |
| Accidental deletion of active test file | `kind=pytest_node` for E-3; parent file retained |
| Replacement path drift | `test_pr_e_replacement_targets_exist` iterates every `replacements` entry |
| Confusion with RTTP PR-E | § naming banner |
| PR-D gate broken mid-branch | Implement registry promotion + deletion in one logical commit series; tests target **final** applied-only state only |
| Stale audit references | Rewrite report on move to `docs/superpowers/reports/` |

---

## §11 — Rollback

Revert PR-E merge. Restore deleted files/tests from git history. Reset registry tuples to PR-D v1 (`PR_E_DELETE_CANDIDATES` with E-1 only, empty applied). No DB or feature-flag impact.

---

## Self-review (2026-05-24)

1. **Placeholders:** None; all three deletion ids specified with kinds and replacements.
2. **Consistency:** Applied-only final state in §2 matches §4 tests and §8 closure; no before/after dual-mode.
3. **Scope:** Single PR; B-guarded-full; three deletions only.
4. **Ambiguity:** E-3 deletes function only; E-1/E-2 delete whole files. `replacements` tuples are machine-verifiable only (no “CI full suite” strings). Paths verified on master: django import boundaries, optimization contamination gates, health API test, replay matrix explicit node.
5. **Authority:** Audit demoted to evidence in §5; registry is SoT.
