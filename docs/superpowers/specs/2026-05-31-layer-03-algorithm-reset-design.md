# Layer 03 Algorithm Reset (CLI-first stub) — Normative Design

**Status:** APPROVED (2026-05-31; §1–§6 + blocking amendments)
**Date:** 2026-05-31
**Owner:** `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/`
**Supersedes:** [`2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](2026-05-30-layer-03-boundary-m-repack-greedy-design.md) (algorithm body only; retained as historical reference)
**Invariants:** [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)

This document is the single source of truth for removing the current Layer 03 rim greedy algorithm
while preserving stack slot, CLI/core authority, DTO compatibility, and minimal replay placeholders.
A future Layer 03 design MUST replace this stub; it MUST NOT extend PR-B greedy/pass/append behavior.

---

## Decision record

| Choice | Value |
|--------|--------|
| Scope | **A** — remove algorithm; keep L3 stack slot |
| Runtime authority | **CLI-first** — `src/shapez2_factory/` only; no Django algorithm copies |
| Replay | **R3** — keep phase/event scaffolding; empty observability; delete greedy-assumption tests |
| Stub id | `reset_stub_v1` (post-summary field `algorithm_stub`) |

---

## Goal

Remove all current Layer 03 placement algorithm code (PR-B greedy, pass1/pass2, variants, append
implementation) so a new algorithm can be authored without inheriting stale structure. The solver stack
(L2 → L3 → L5 → L6), CLI subprocess path, artifact ingest, and Lab replay phase identity MUST keep
working with a **deterministic empty** Layer 03 result.

## Non-goals

- Changing Layer 02 exterior transport behavior or contracts
- Changing Layer 04 disabled shim
- Changing Layer 05 / Layer 06 algorithms
- Designing or implementing the replacement Layer 03 algorithm (separate spec)
- Removing Layer 03 from `stack_runner` layer index or renumbering phases
- Using replay artifacts or solver_summary fields as algorithm inputs (forbidden shortcut)

## Work classification

`contract change` + `implementation change` (deletion + stub). Tests: delete greedy-assumption
suites; add reset-contract tests before stub lands (red-green).

---

## Behavior contract (normative)

### R1 — Layer entry (`run_layer_03_rim_greedy_placement`)

| ID | Rule |
|----|------|
| S1 | **Authority:** Implementation exists only under `src/shapez2_factory/.../layer_03_rim_greedy_placement/run.py`. |
| S2 | `django_apps/.../layer_03_rim_greedy_placement/` MUST NOT contain algorithm modules; at most `__init__.py` + `run.py` re-exporting the core entrypoint. |
| S3 | `django_apps/asteroid_lab/layers/stack_runner.py` and CLI `run_stack` MUST call the core entrypoint (direct import or thin re-export). |
| S4 | When `exterior_plan is None`, return `build_empty_integrated_rim_greedy_result(layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN, ...)` — same as today. |
| S5 | When budget is exhausted before start, preserve existing skip behavior. |
| S6 | For all other valid inputs, return immediately: `build_empty_integrated_rim_greedy_result(layer_skip_reason=Layer03SkipReason.ALGORITHM_RESET, observability_events=begin/complete pair, rim_anchor_count=0)`. No route goals, anchors, pass1/pass2, or append mutation. |
| S7 | Post-summary metrics MUST include `algorithm_stub: "reset_stub_v1"` and `layer_skip_reason: "algorithm_reset"` (enum value). |

### R2 — `Layer03SkipReason` enum

Add to `Layer03SkipReason` in `contracts/candidates.py`:

```python
ALGORITHM_RESET = "algorithm_reset"
```

Free-form skip strings are forbidden for the reset path.

### R3 — Legacy DTO compatibility (`pass2_report.hard_fail`)

`build_empty_integrated_rim_greedy_result` continues to set `pass2_report.hard_fail=True` for legacy
DTO shape compatibility only.

**Consumers MUST NOT** treat `hard_fail=True` as a solver failure when
`metrics.layer_skip_reason == Layer03SkipReason.ALGORITHM_RESET`. In that case the layer completed
intentionally empty (reset/no-op), not a hard algorithm failure.

Future UI/L5/L6 logic that branches on `hard_fail` MUST gate on `layer_skip_reason != ALGORITHM_RESET`
or use explicit reset detection via `algorithm_stub`.

### R4 — Replay (R3 stub)

| ID | Rule |
|----|------|
| P1 | Keep `layer03_*` replay modules and registered `ReplayEventType` values. |
| P2 | For reset results, emit frames only from `observability_events` (typically `RIM_GREEDY_BEGIN` + `RIM_GREEDY_COMPLETE`). No pass1, seed-committed, or pool-window frames. |
| P3 | `layer03_pool_windowing` and greedy-specific segment branches MUST no-op or early-return on empty `committed_placements`. |
| P4 | Replay/metrics remain **output-only**; MUST NOT feed back into placement or routing decisions. |

### R5 — Preserved stack surface

MUST remain stable across reset:

- `LAYER_03_RIM_GREEDY_PLACEMENT` slug and layer index `3`
- `IntegratedRimGreedyResult`, `RimGreedyMetrics`, `Layer03AppendResult` DTOs
- `build_empty_integrated_rim_greedy_result`, `build_empty_layer03_append_result`
- `rim_greedy_append` contract module (DTO + empty builder only)
- `stack_runner` / `run_stack` runner registration for L3

### R6 — Removed code (inventory baseline)

Delete from **core** (and mirror deletes in Django shims):

```
layer_03_rim_greedy_placement/greedy_pass1.py
layer_03_rim_greedy_placement/greedy_pass2.py
layer_03_rim_greedy_placement/traversal_variants.py
layer_03_rim_greedy_placement/rim_anchors.py
layer_03_rim_greedy_placement/append.py          # implementation only
layer_03_rim_greedy_placement/greedy_seed.py
layer_03_rim_greedy_placement/seed_orient.py
layer_03_rim_greedy_placement/cardinal_map.py
layer_03_rim_greedy_placement/local_window.py
layer_03_rim_greedy_placement/dps_policy.py
layer_03_rim_mining_bundles/                     # deprecated delegate package
```

`run.py` is replaced by the stub described in R1.

### R7 — `shared/route_probe.py` deletion gate (blocking amendment)

`shared/route_probe.py` MUST NOT be deleted in the initial reset PR without import inventory proof.

**Pre-delete evidence required:**

```bash
git grep -n "route_probe" -- "*.py"
git grep -n "shared.route_probe" -- "*.py"
python -m pytest tests/unit/asteroid_lab/ --collect-only
```

**Current inventory (2026-05-31):** only `greedy_pass1.py` imports
`weighted_route_probe` from `shared.route_probe`. Layer 04 tests and `candidates.py` use
`RouteProbeStatus` / path **types** from contracts, not the probe implementation module.

**Default for reset PR:** **RETAIN** `shared/route_probe.py` for the next L3 implementation.
Optional deletion MAY follow in a separate change only after inventory shows zero non-test consumers
outside deleted L3 modules.

---

## Test contract (blocking amendment: classification, not glob-only)

Tests MUST NOT be removed by filename glob alone. Each candidate file is classified before deletion:

| Class | Action | Examples |
|-------|--------|----------|
| **1 — Greedy algorithm assumption** | DELETE | `test_layer_03_boundary_m_repack_acceptance.py`, `test_layer_03_rim_greedy_pass2.py`, `test_layer_03_rim_greedy_variants.py`, `test_layer03_rim_greedy_segment.py`, `test_layer03_append_replay_parity.py`, `test_layer03_pool_windowing.py`, `test_lab_replay_timeline_layer03_runtime.py` |
| **2 — DTO empty contract** | KEEP | `test_rim_greedy_contracts.py`, `test_rim_greedy_append_contracts.py` (update if `ALGORITHM_RESET` added) |
| **3 — Stack boundary** | KEEP / ADD | `test_stack_runner_core_boundary.py`; new `test_stack_runner_accepts_empty_l3.py` |
| **4 — L2 overlay persistence** | KEEP | `test_layer03_exterior_connector_overlay_persistence.py` (adjust fixtures if needed for empty L3) |
| **5 — L4 disabled boundary** | KEEP | `test_layer_03_l4_boundary.py`, `test_layer_04_disabled_shim.py` |

**DELETE** `test_layer_03_04_skeleton.py` (asserts `len(committed_placements) >= 1`).

**ADD** (minimum):

1. `test_layer_03_reset_stub_contract.py` — stub returns empty placements,
   `Layer03SkipReason.ALGORITHM_RESET`, BEGIN/COMPLETE observability.
2. `test_stack_runner_accepts_empty_l3.py` — L2 complete → L3 reset → stack continues.
3. `test_no_django_l3_algorithm_authority.py` — no `greedy_pass*` under `django_apps/.../layer_03`.

Greedy-only fixtures (`layer_03_deep_rim_map.py`, `layer_03_candidate_set_factory.py`) DELETE when
no remaining class-2/3/4/5 test imports them.

---

## Documentation

| Document | New status |
|----------|------------|
| `2026-05-30-layer-03-boundary-m-repack-greedy-design.md` | **SUPERSEDED** — pointer to this spec |
| `plans/2026-05-30-layer-03-boundary-m-repack-greedy/` | **CLOSED / SUPERSEDED** |
| `2026-05-31-rim-directional-segment-packing-design.md` (if present) | **SUPERSEDED** — never implemented |
| `documents/ai/current_plan.md` | L3 reset **ACTIVE**; PR-B and segment-packing entries marked superseded |

---

## Observability example (non-normative)

```json
{
  "layer": "layer_03_rim_greedy_placement",
  "algorithm_stub": "reset_stub_v1",
  "layer_skip_reason": "algorithm_reset",
  "committed_placement_count": 0,
  "append_placement_count": 0,
  "winning_variant_id": ""
}
```

---

## Acceptance matrix

| ID | Check |
|----|--------|
| A1 | `pytest tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py` passes |
| A2 | `pytest tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py` passes |
| A3 | `pytest tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py` passes |
| A4 | `pytest tests/unit/asteroid_lab/layers/` — no deleted test modules referenced |
| A5 | `pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py` passes |
| A6 | `ruff check` on touched paths clean |
| A7 | `shared/route_probe.py` still present OR deletion PR includes inventory evidence per R7 |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Lab UI treats `hard_fail=True` as failure | R3 + consumer note in R3 |
| Accidental deletion of DTO contract tests | Classification table (mandatory) |
| Premature `route_probe` removal | R7 inventory gate; default RETAIN |
| L5 assumes L3 committed cells | Stack acceptance test A2 |

---

## Next step

Invoke **writing-plans** to produce
`docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/` with file-level deletion checklist
and verification commands. **No production code changes until the plan is approved.**
