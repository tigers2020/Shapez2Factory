# Decontamination PR-F — Aggressive Test Decontamination (Design)

**Status:** APPROVED (PR-F0 inventory implemented on branch `feat/decontamination-pr-f0-inventory`)  
**Date:** 2026-05-30  
**Owner:** Test Decontamination Release Architect  
**Track:** Decontamination PR-F (repo health; **not** RTTP algorithm, **not** coordinate island-local PR-F)  
**Parent:** [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) · PR-E CLOSED  
**Prerequisite:** PR-D **CLOSED**; PR-E **CLOSED** (`64a8fee9`, PR #71)  
**Implementation plan:** [`../plans/2026-05-30-test-cleanup-aggressive-decontamination-pr-f.md`](../plans/2026-05-30-test-cleanup-aggressive-decontamination-pr-f.md)  
**Evidence (non-authority):**

- [`../reports/2026-05-24-test-cleanup-audit.md`](../reports/2026-05-24-test-cleanup-audit.md) — PR-E applied rows
- [`../reports/2026-05-30-test-decontamination-inventory.md`](../reports/2026-05-30-test-decontamination-inventory.md) — PR-F0 inventory (created in F0)

**Naming:** **Decontamination PR-F** (this document) must not be confused with:

- **RTTP PR-E** — `OptimizationInput.coord_frame`, macro commit (coordinate-tagged-frames track)
- **Coordinate / island-local “PR-F”** — dense server removal, `lab_xy_from_replay_cell`, AST coord gates (see `2026-05-23-coordinate-tagged-frames-design.md`, `asteroid_coord_transform_spec.md`)

Use branch prefix `feat/decontamination-pr-f-*` and plan rows labelled **Decontamination PR-F**.

---

## §1 — Problem and goals

### Problem

After PR-E, `PR_E_DELETE_CANDIDATES` is empty and only three mechanical deletions were applied. The remaining `tests/` tree (~250+ Python modules under `unit/`, `integration/`, `support/`) still contains:

- Legacy product-path tests whose **production entry** was removed or superseded
- Duplicate assertion matrices
- Permanent `@pytest.mark.skip` / `xfail` markers that may be misclassified
- Unused fixtures and integration gates tied to obsolete flows

Aggressive cleanup is needed **without** weakening RTTP, validation, replay, reconstruction, or game_data import contract gates.

### Goals

1. **Wide scan** — classify every test artifact under `tests/` (unit, integration, fixtures, support).
2. **Registry authority** — extend `quarantine_registry.py` with PR-F tuples; no deletion without registry + evidence.
3. **Protected contracts** — explicit allowlist of coverage owners that must not be deleted in F2–F5 without same-PR replacement.
4. **Phased PRs** — F0 inventory only; F1–F5 deletion slices with package narrow gates.

### Non-goals

- Production solver / RTTP algorithm behaviour change
- Deleting quarantined **document** trees (`QUARANTINED_DOC_PATHS`)
- Bulk removal of environment-guarded `pytest.skip` (missing game_data dump, etc.)
- Removing `strict=True` xfail gates without spec amendment (e.g. G3 coordinate equivalence)
- Renaming coordinate island-local work already labelled “PR-F” in Algorithm docs

---

## §2 — Principles

```text
Audit is evidence, not authority.
Registry is the mechanical source of truth for deletion.
Aggressive means scan breadth and classification rigor, not uncontrolled deletion.
```

| Principle | Rule |
|-----------|------|
| Deletion authority | Only `PR_F_APPROVED_DELETIONS` → applied in same PR → `PR_F_APPLIED_DELETIONS` |
| Inventory | `PR_F_AGGRESSIVE_AUDIT_CANDIDATES` holds graded rows; grades ≠ permission to delete |
| Protected | `PR_F_PROTECTED_TESTS` and `PROTECTED_*` grades block promotion to approved |
| Age / aesthetics | Insufficient alone |
| Replacement | Every approved deletion lists `replacements: tuple[str, ...]` (file path or pytest nodeid) |
| Helper vs product path | Obsolete **product path** may delete integration tests; **helper unit contract** may remain |

### Deletion authority (normative)

A test may be deleted only when its contract ownership is either:

1. **Obsolete** — no longer reachable from production or supported experimental paths (documented), or  
2. **Duplicated** — a stronger, more explicit test names the same contract (replacement nodeid required), or  
3. **Mechanically dead** — 0-byte file, uncollectable import, duplicate pytest node, unused fixture with zero consumers.

**Forbidden:** deleting because of low line-coverage value, legacy wording in docstrings, or audit report rows without registry promotion.

---

## §3 — Inventory taxonomy

Every audited artifact receives exactly one **grade**:

| Grade | Meaning | Default action |
|-------|---------|----------------|
| `PROTECTED_CONTRACT` | RTTP / validation / replay / catalog / game_data import invariant | No delete |
| `PROTECTED_REGRESSION` | Named bug or ops-smoke recurrence guard | No delete |
| `DUPLICATE_COVERAGE` | Same contract asserted elsewhere (stronger or equal) | Delete candidate (F1/F2+) |
| `OBSOLETE_PRODUCT_PATH` | Product entry removed or superseded; no helper contract | Delete candidate (F2+) |
| `PLACEHOLDER_SKIP` | Permanent skip / deferred feature marker | Registry + human slice (F2/F3); not auto-delete |
| `DEFERRED_FEATURE_TEST` | Skip documents future RTTP/macro work (e.g. PR-B macro 4×4) | Keep until feature lands or spec cancels track |
| `INTENT_UNKNOWN` | Cannot prove obsolete or duplicate | Report only; no delete |
| `BROKEN_OR_DEAD` | 0-byte, import dead, duplicate collect node | Delete candidate (F1) |
| `ENV_GUARD_SKIP` | Conditional skip on fixture/dump presence | No delete |

Promotion to `PR_F_APPROVED_DELETIONS` requires grade ∈ `{DUPLICATE_COVERAGE, OBSOLETE_PRODUCT_PATH, BROKEN_OR_DEAD}` **and** explicit replacement or `replacements=()` with reason `mechanical_no_contract`.

---

## §4 — Registry schema (PR-F extension)

**File:** `tests/unit/architecture/quarantine_registry.py`

Reuse `PrEDeleteCandidate` shape (PR-E) for approved/applied deletions. Add PR-F-specific types:

```python
InventoryGrade = Literal[
    "PROTECTED_CONTRACT",
    "PROTECTED_REGRESSION",
    "DUPLICATE_COVERAGE",
    "OBSOLETE_PRODUCT_PATH",
    "PLACEHOLDER_SKIP",
    "DEFERRED_FEATURE_TEST",
    "INTENT_UNKNOWN",
    "BROKEN_OR_DEAD",
    "ENV_GUARD_SKIP",
]

PrFSlice = Literal["F0", "F1", "F2", "F3", "F4", "F5"]


@dataclass(frozen=True, slots=True)
class PrFAuditEntry:
    """PR-F0 inventory row — evidence only until promoted."""

    id: str  # stable slug, e.g. f2-lab-unified-replay-append-01
    path: str  # repo-relative file, pytest nodeid, or fixture path
    kind: Literal["file", "pytest_node", "fixture_path"]
    grade: InventoryGrade
    package: str  # e.g. unit/asteroid_lab
    reason: str
    replacement: str | None  # primary coverage owner if deleted
    target_slice: PrFSlice | None  # F1..F5 when delete candidate
    evidence: str  # one-line machine or human verifiable fact


# PR-F0: populated by inventory script/report; never deletes.
PR_F_AGGRESSIVE_AUDIT_CANDIDATES: tuple[PrFAuditEntry, ...] = ()

# Approved for next deletion PR; must be empty at end of each F1..F5 PR before merge.
PR_F_APPROVED_DELETIONS: tuple[PrEDeleteCandidate, ...] = ()

# Historical record (same schema as PR_E_APPLIED_DELETIONS).
PR_F_APPLIED_DELETIONS: tuple[PrEDeleteCandidate, ...] = ()

# Explicit protection — pytest nodeids and/or file prefixes; architecture tests enforce no overlap with APPROVED.
PR_F_PROTECTED_TESTS: tuple[str, ...] = ()
```

**Lifecycle per deletion PR (F1–F5):**

```text
1. Promote rows from PR_F_AGGRESSIVE_AUDIT_CANDIDATES into PR_F_APPROVED_DELETIONS (human + spec sign-off).
2. Verify replacements exist; run package narrow gate + standing gates.
3. Apply physical deletion / node removal.
4. Move rows to PR_F_APPLIED_DELETIONS; clear PR_F_APPROVED_DELETIONS.
5. Update inventory report + architecture tests.
```

PR-E tuples (`PR_E_*`) remain **immutable history**; do not reuse for PR-F deletions.

---

## §5 — Protected contract classes

Tests matching these patterns default to `PROTECTED_CONTRACT` unless a **same-PR** replacement is added:

### RTTP / optimization

- Candidate generate → route probe → reachable pool (no commit in generator)
- Commit-time latest `route_domain` reprobe; survivability / deferred retry (B-CS, PR-1–4)
- Validation read-only; D+ fail-closed; `failure_reason` / `event_type` / `issue_code` enums
- Catalog-native generator / placement / transport policy
- RTTP replay sink, milestone event types, throughput policy diagnostic (T2 canon)
- Macro track: **paused** — skip tests stay `DEFERRED_FEATURE_TEST`, not deleted until roadmap cancels or unskips

### Reconstruction / replay

- Replay / NDJSON / artifacts **output-only** (not algorithm input)
- Reconstruction complete-map SoT; B-CS3/B-CS4 boundaries
- `test_reconstruction_narrow.ps1` module set (seven modules per `current_plan.md`)

### game_data

- Import idempotency, provenance, catalog slice, pinned dump contracts
- Conditional skips when dump missing (`ENV_GUARD_SKIP`)

### web / Lab

- Lab page context, replay timeline wiring, island-local projection (coordinate PR-F behaviour)
- Template/JS smoke for active Lab routes

### architecture (always protected)

- `test_quarantined_paths_do_not_leak.py`
- `test_optimization_contamination_gates.py`
- `test_capacity_complete_map_sot_gates.py`

`PR_F_PROTECTED_TESTS` shall list **concrete nodeids or file globs** derived from this section during PR-F0 (not empty at F0 merge).

---

## §6 — Package scan scope and ownership

| Package | ~`.py` files (2026-05-30) | F slice | Narrow gate owner |
|---------|---------------------------|---------|-------------------|
| `tests/unit/asteroid_lab/` | 156 | F2 | `pytest tests/unit/asteroid_lab/ -k rttp` + reconstruction narrow (subset) |
| `tests/unit/game_data/` | 31 | F3 | `pytest tests/unit/game_data/` |
| `tests/unit/web/` | 10 | F4 | `pytest tests/unit/web/` |
| `tests/integration/` | 15 | F5 | `pytest tests/integration/` |
| `tests/support/` | 8 | F5 | importers + consumer grep |
| `tests/fixtures/` (non-py) | JSON/binary | F5 | fixture consumer graph |
| `tests/unit/architecture/` | 8 | — | **Protected**; extend registry only in F0/F1 |
| `tests/unit/shapez_solver/` | 20 | F5 (optional) | `pytest tests/unit/shapez_solver/` |
| `tests/unit/shapez_core/` | 11 | F5 (optional) | `pytest tests/unit/shapez_core/` |

**F1 (mechanical):** any package — 0-byte, duplicate node, dead import, unused fixture.

**Out of F2–F5 unless inventoried:** `tests/unit/config/`, `tests/unit/test_build_locale_ko_strict.py` — classify in F0; delete only if mechanical.

---

## §7 — Deletion PR slices

| PR | Scope | Max risk | Deletes? |
|----|-------|----------|----------|
| **PR-F0** | Inventory + registry schema + report + gates + `current_plan` ACTIVE | None | **No** |
| **PR-F1** | Mechanical dead tests (all packages) | Low | Yes |
| **PR-F2** | `asteroid_lab` obsolete/duplicate (excl. protected) | Medium | Yes |
| **PR-F3** | `game_data` fixture/test shrink | Medium | Yes |
| **PR-F4** | `web` / Lab obsolete tests | Medium | Yes |
| **PR-F5** | `integration/`, `fixtures/`, `support/`, optional solver/core | High | Yes |

**One PR must not mix slices** (e.g. F2 + F3 files in one merge).

### Per-PR gate checklist (F1–F5)

All must pass before merge:

1. `PR_F_APPROVED_DELETIONS` non-empty on branch tip → empty after move to applied  
2. No approved path overlaps `PR_F_PROTECTED_TESTS`  
3. Every `replacements` entry resolves (file exists or AST `def`)  
4. Package narrow pytest (table §6)  
5. Standing: `scripts/test_quarantine_registry.ps1`, `scripts/test_optimization_contamination.ps1`  
6. F2 additionally: `scripts/test_reconstruction_narrow.ps1` when reconstruction files touched  
7. F2 RTTP touch: `pytest tests/unit/asteroid_lab/ -k rttp`  
8. Record `pytest --collect-only tests` delta in PR body  

---

## §8 — Priority rubric (seed candidates for F0 report)

### Tier 1 — Mechanical (F1)

- 0-byte `test_*.py`
- Duplicate pytest function (same assertion loop as sibling — PR-E E-3 pattern)
- Module failing import in isolation with no `conftest` rescue
- Fixture file with zero referencing tests (ripgrep + collect-only consumer script)

### Tier 2 — Obsolete product path (F2/F4)

- Tests whose module docstring says superseded **and** no production import of tested entry (grep `django_apps/`)
- Example **review** (not pre-approved): `test_lab_unified_replay_append.py` — product path uses `lab_rttp_snapshot_compose`; **keep** if helper `last_renderable_map_frame_index` remains in services

### Tier 3 — Skip / xfail (human promotion)

| Pattern | Default grade |
|---------|----------------|
| `@pytest.mark.skip(reason="PR-B: macro…")` | `DEFERRED_FEATURE_TEST` |
| `@pytest.mark.xfail(strict=True)` + gate doc | `PROTECTED_CONTRACT` or `DEFERRED_FEATURE_TEST` |
| `pytest.skip("taxonomy not seeded")` | `ENV_GUARD_SKIP` |
| Skip reason references removed module | `OBSOLETE_PRODUCT_PATH` candidate |

---

## §9 — Architecture tests (PR-F0 deliverable)

Extend `tests/unit/architecture/test_quarantined_paths_do_not_leak.py`:

| Test | Asserts |
|------|---------|
| `test_pr_f_audit_candidates_have_valid_grades` | Every `PrFAuditEntry.grade` ∈ allowed literals |
| `test_pr_f_approved_deletions_empty_on_f0` | `PR_F_APPROVED_DELETIONS == ()` until F1+ |
| `test_pr_f_protected_tests_non_empty_after_f0` | `PR_F_PROTECTED_TESTS` populated |
| `test_pr_f_approved_never_overlaps_protected` | When approved non-empty, disjoint from protected set |
| `test_pr_f_applied_replacements_exist` | Same pattern as PR-E for `PR_F_APPLIED_DELETIONS` |

Optional F0 script: `scripts/audit_test_inventory.ps1` → writes/updates `docs/superpowers/reports/2026-05-30-test-decontamination-inventory.md`.

---

## §10 — Approaches considered

| Approach | Summary | Verdict |
|----------|---------|---------|
| **A — PR-E minimal** | Only mechanical deletes | Rejected — leaves legacy debt |
| **B — Audit + ad hoc PRs** | Report without registry | Rejected — repeats PR-E near-miss risk |
| **C — Aggressive scan + registry slices (this spec)** | F0 inventory; F1–F5 gated deletes | **Selected** |

---

## §11 — Success criteria

| Milestone | Done when |
|-----------|-----------|
| PR-F0 merged | Inventory report exists; registry types + empty approved; protected list populated; gates green; **zero** test files deleted |
| PR-F1 merged | ≥1 mechanical deletion applied; `PR_F_APPLIED_DELETIONS` extended; collect delta documented |
| Track complete | F2–F5 each merged or explicitly PAUSED in `current_plan.md` with reason |
| Regression | No standing gate regression vs pre-F0 `master` without documented exception |

---

## §12 — Rollback

Each F1–F5 PR is revertible independently via `git revert <merge-sha>`. Restoring deleted tests requires re-adding files from `PR_F_APPLIED_DELETIONS` records in the same revert commit.

---

## References

- [`2026-05-24-decontamination-pr-e-dead-code-design.md`](2026-05-24-decontamination-pr-e-dead-code-design.md)
- [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md)
- [`documents/ai/contamination_policy.md`](../../../documents/ai/contamination_policy.md)
- [`docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)
