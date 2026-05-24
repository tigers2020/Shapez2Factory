# Test Cleanup Audit (Evidence Report)

**Date:** 2026-05-24  
**Authority:** None — evidence only. Deletions are authorized only by `PR_E_APPLIED_DELETIONS` in `tests/unit/architecture/quarantine_registry.py`.

```text
test_cleanup_audit.md is evidence-only.
It is not a source of deletion authority.
Only PR_E_DELETE_CANDIDATES / PR_E_APPLIED_DELETIONS are mechanical authority.
```

## PR-E applied (Decontamination)

| id | path | disposition |
|----|------|-------------|
| E-1 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | file deleted (0-byte) |
| E-2 | `tests/test_smoke.py` | file deleted (`assert True` placeholder) |
| E-3 | `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py::test_lab_adapter_members_are_valid_replay_event_types` | pytest function removed |

**Replacements (machine registry):**

- E-1 → `test_django_app_import_boundaries.py`, `test_optimization_contamination_gates.py`
- E-2 → `tests/integration/api/test_health.py`
- E-3 → `test_replay_event_coverage_matrix.py::test_unified_replay_event_type_adapter_coverage_matrix_is_explicit`

## PR-E verification

| Metric | Value |
|--------|------:|
| collect-before (master) | 1493 |
| collect-after (PR-E branch) | 1495 |
| net delta | +2 |

```text
Deletion-only delta (expected -2):
- E-1 0-byte file: no collected test delta
- E-2 smoke file: -1 test
- E-3 replay pytest node: -1 test

Architecture gate delta (+4 on test_quarantined_paths_do_not_leak.py):
- removed test_quarantine_registry_has_pr_e_disposition (-1)
- added 5 PR-E applied-only tests (+5)
- net on that module: +4

Net collect delta: -2 + 4 = +2 (matches 1493 → 1495)
```

## Inventory (historical audit rows)

| Test file | Nodeid / test group | Problem type | PR-E action |
| --------- | ------------------- | ------------ | ----------- |
| `tests/test_smoke.py` | `test_smoke` | MEANINGLESS_DELETE | **Applied (E-2)** |
| `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py` | `test_lab_adapter_members_are_valid_replay_event_types` | DUPLICATE_DELETE | **Applied (E-3)** |
| `tests/unit/asteroid_lab/test_service_import_boundaries.py` | file | MEANINGLESS_DELETE | **Applied (E-1)** |

Rows marked `NEEDS_HUMAN_DECISION`, `KEEP_CONTRACT`, `SLOW_*` were not deleted in PR-E.

## Deferred (not PR-E)

- Coordinate generator raw-`X==0` policy clarification
- RTTP milestone event SoT consolidation
- Game-data / Node subprocess / macro DB fixture shrink passes
