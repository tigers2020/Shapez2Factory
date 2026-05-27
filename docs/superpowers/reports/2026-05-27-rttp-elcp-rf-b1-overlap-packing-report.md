# P1-ELCP-RF-B1 — Overlap Packing Selection — Report

**Date:** 2026-05-27  
**Status:** **CLOSED** (2026-05-27)  
**Slug / config:** Gate A primary slugs — `rttp-core-recovery-test-map` (parity RF.1), `rttp-cert-candidate-recon-l0` (recon fixture L0)  
**Spec:** [`2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md`](../specs/2026-05-27-rttp-elcp-rf-b1-overlap-packing-design.md)  
**Plan:** [`2026-05-27-rttp-elcp-rf-b1-overlap-packing.md`](../plans/2026-05-27-rttp-elcp-rf-b1-overlap-packing.md)

---

## Phase 0 — Overlap graph bounds (`rttp-core-recovery-test-map`)

| Field | Value |
|-------|------:|
| `vertex_count` | 356 |
| `edge_count` | 1434 |
| `connected_component_count` | 19 |
| `greedy_regret_baseline` | 59 |
| `best_known_independent_set_size` | 67 |
| `exact_mis_size` | null (3 components > 40 vertices use heuristic MIS) |
| `upper_bound` | 308 |
| `upper_bound_method` | **mixed** (16 exact + 3 heuristic; not `component_exact`) |
| `chromatic_upper_bound_sum` | 88 (diagnostic; bounds χ, not \|MIS\|) |
| `target_floor` | **67** |
| `fot_conflict_edge_count` | 0 |
| **Verdict** | **GO** |

**Frozen constants:** `tests/support/rttp_b1_gate_a_frozen_bounds.py`

---

## Phase 1 — Selection implementation (Gate A recovery map)

| Check | Result |
|-------|--------|
| Mode | `GREEDY_REGRET_OVERLAP_PACK` (opt-in) |
| `commit_order_len` | **67** (`>= target_floor=67`) |
| Default `GREEDY_REGRET` | **59** unchanged |
| A2 trace parity | PASS |

**Task 10:** **SKIPPED** — B1-B-lite met `target_floor`; B1-A/C not required.

---

## Phase C — Slug regression guards

| Slug | `GREEDY_REGRET` | `GREEDY_REGRET_OVERLAP_PACK` | Guard |
|------|----------------:|-----------------------------:|-------|
| `rttp-core-recovery-test-map` | 59 (frozen) | 67 (`>= target_floor`) | PASS |
| `rttp-cert-candidate-recon-l0` | 59 (frozen `CERT_SLUG_GREEDY_REGRET_BASELINE`) | 67 (`>= 59`) | PASS |

**Tests:** `tests/unit/asteroid_lab/test_rttp_b1_slug_regression_guards.py`

---

## Validation (Task 11)

| Gate | Result |
|------|--------|
| `tests/unit/asteroid_lab/test_overlap_graph.py` | PASS |
| `tests/investigation/test_rttp_overlap_graph_packing_bounds.py` | PASS |
| `tests/unit/asteroid_lab/test_rttp_b1_overlap_pack_selection.py` | PASS |
| `tests/unit/asteroid_lab/test_rttp_b1_slug_regression_guards.py` | PASS |
| `tests/investigation/test_rttp_greedy_regret_selection_attrition.py` (A2 parity) | PASS |
| `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py` (mode contract) | PASS |
| `ruff check` (B1 paths) | PASS |

**mypy narrow:** Attempted on B1 selection modules; failed due to pre-existing Django typing debt through import chain (141 errors in `models.py` et al.). No B1-specific type error isolated. **Not a B1 blocker** per program gate; CI full `mypy django_apps config src` remains PR responsibility.

---

## Program notes

- **P1-ELCP-RF** remains **REOPENED** (Layer 2 commit forensics).
- **`lane_capacity_shortfall` B-spec** remains **BLOCKED**.

```text
B1 CLOSED: overlap-pack selection improves Gate A commit_order 59→67;
default greedy_regret unchanged; cert slug guards PASS.
```
