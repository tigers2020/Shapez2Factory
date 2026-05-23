---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-20
phase: I
pr: 4
related_docs:
  - documents/Algorithm/solver_runtime/open_decisions.md
  - documents/Algorithm/asteroid_lab_06_evolutionary_search.md
---

# Phase I ??Candidate Selection v0

## ëª©ì 

**Solver Button v0 ?•ë³¸ ? íƒê¸?* ??capacity-aware **greedy** only. Candidate pool?ì„œ **commit ?œë„ ?œì„œ**ë¥?ë§Œë“ ?? ?„ì§ ?•ì • ë°°ì¹˜ê°€ ?„ë‹ˆ??

> **GA ë¯¸ì‚¬??** [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md) Â· `Genome`/`Gene.commit_order` ??**legacy reference** ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§3).

## RD-GATE lab reference (2026-05-23)

Reference `copy-import-e954a2cb` passes RD-GATE with **lab** `run_config`:

| Key | Value |
|-----|-------|
| `mode` | `lab` |
| `selection_shadow_policy` | `shadow_domain_parity` |
| `selection_commit_order_strategy` | `off` (Phase J `CommitOrderPolicy` overlay) |
| `route_probe_max_expansions` | **512** (256 alone stalls selection ??0) |

Script: `python scripts/confirm_rd_gate_lab_config.py` ??`var/rd_gate_confirm.json`.

Interactive **runtime** (`mode=runtime`, 55s deadline, beam selection, summary-only replay) is separate from this lab gate.

## ?…ë ¥

```text
CandidatePool (normal)
PlannedRouteGoals / capacity_plan
OptimizationInput
```

## ?°ì¶œë¬?

```text
SelectedCandidatePlan
ordered candidate ids
```

## ?‘ì—…

### Phase I inlet mirror (Tier 1.2b)

Hard filter: `fixed_output_transport ??selected_route_cells`. Accumulated cells use the **full** generation probe path (`selection_mirror_route_cells`), not only the normalized tail (`planned_route_cells`), so prefix trunk coords are not dropped before commit reprobe.

### Phase I??shadow domain parity (reprobe drift)

Pipeline default: `SelectionShadowPolicy.SHADOW_DOMAIN_PARITY`. Greedy selection maintains in-memory `SelectionShadowState` and calls `shadow_try_confirm` (same `RouteDomainSnapshotBuilder` + reprobe budget as Phase J) before ordering each pick. Inlet hard-filter uses shadow **reprobed** `committed_route_cells`, not generation paths. `OFF` restores Tier 1.2b mirror-only behavior (tests / rollback). See [`2026-05-22-reprobe-drift-shadow-domain-design.md`](../../../docs/superpowers/specs/2026-05-22-reprobe-drift-shadow-domain-design.md).

### Phase I??R shadow stuck recovery

When the primary eligible pool exhausts without a `shadow_try_confirm` success, selection widens to a **recovery pool** (`build_shadow_recovery_pool`): remaining candidates with hard footprint / anchor-slot / inlet-on-committed-route checks only (trunk `goal_load` cap relaxed). Recovery tries candidates in **ascending** score order (lower-ranked survivors first). Hard filters and `shadow_try_confirm` are unchanged. Summary keys: `selection_shadow_stuck_count`, `selection_shadow_recovery_*`, probe-failure reason breakdowns.

### Phase I??O start-preserving shadow-aware ordering

Primary and recovery pools sort via `shadow_aware_sort_key` (`selection_shadow_ordering.py`): minimize `candidate_future_start_blocker_pressure` (sum of `build_future_start_pressure` over blocked future `route_probe_start` / `fixed_output_transport`), then blocker count, route-cell count, Phase I score. Pick impact is classified as `blocks_future_output_start` > `blocks_future_equipment` > `blocks_future_route_only` for diagnostics. `OFF` keeps legacy `_selection_sort_key`. Diagnostics: `selection_shadow_future_start_blocker_*`, pressure totals, `selection_shadow_start_blocker_kind_counts`, `selection_shadow_blocked_start_pressure_top`.

### Phase M2 ??start-preserving commit order (fixed selection set)

After Phase I??selects candidates, `selection_commit_ordering.py` may reorder **commit attempts only** (`SelectionCommitOrderStrategy.START_PRESERVING_GREEDY` default). Multiset of `ordered_candidate_ids` is preserved; `shadow_try_confirm` simulates each pick. Sort defers `is_start_blocked_now` and future start pressure before score. `OFF` leaves selection order and applies legacy `CommitOrderPolicy`. Optional `START_PRESERVING_BEAM` (`beam_width=4`). Summary: `selection_commit_order_*` keys including `original_prefix` / `planned_prefix`.

### v0 Score

```text
score =
    + throughput_factor * 100
    - route_cost * 5
    - goal_priority * 20
    - estimated_corridor_pressure
    - trunk_load_pressure
    - shared_path_pressure (selected planned route overlap; Tier 1)
    - route_fragility_penalty (v0 = 0 until narrow segments on candidate)
```

### Capacity-aware trunk load

Shape:

```text
trunk capacity = 12 fully boosted platforms
```

Fluid:

```text
trunk capacity = 72 fully boosted platforms
```

```python
load_ratio = assigned_platform_count / capacity_by_transport_kind
```

`goal_assigned_platforms` ê°’ì? **?Œë«??ê°œìˆ˜** (+1 per bundle). `base_throughput` ?©ì‚°?€ ?¬ìš©?˜ì? ?ŠëŠ”??(fully boosted Ã—16??1 platform).

### Bundle selection budget (route slot vs miner count)

```text
route_out_count = len(route_goals)
target_miner_bundle_count = sum per goal (
  shape belt goals Ã— miners_per_shape_route (default 12, env ASTEROID_LAB_MINERS_PER_ROUTE_OUT)
  fluid pipe goals Ã— 72 (FLUID_PLATFORMS_PER_GOAL)
)
```

`route_out_count`???¸ë? route slot ?? `target_miner_bundle_count`??? íƒÂ·commit **?œë„** ?í•œ(?•ì • ???„ë‹˜). êµ¬í˜„: `bundle_selection_targets.py` Â· `solver_summary` / replay inspector.

**? íƒ ?ˆì‚° ì¢…ë£Œ(v0):** `target_miner_bundle_count`???„ë‹¬?˜ë©´ `len(ordered_candidate_ids)` ê¸°ì??¼ë¡œ ì¢…ë£Œ?œë‹¤. `base_throughput` ?©ì? `selected_throughput_at_stop` ì§„ë‹¨?©ë§Œ ?°ë©°, ?ˆì‚° ë¹„êµ???¬ìš©?˜ì? ?ŠëŠ”??

**Footprint ë¹„ì¤‘ë³?v0):** greedy ? íƒ ???´ë? ê³ ë¥¸ ?„ë³´??`occupied_cells`?€ êµì°¨?˜ëŠ” ë²ˆë“¤?€ commit order???£ì? ?ŠëŠ”??(Phase J `occupied_cell_conflict`?€ ?™ì¼ ì§‘í•© ê³„ì•½).

**Shared transport inlet(v0):** [`shared-transport-inlet`](../../../docs/superpowers/specs/2026-05-22-shared-transport-inlet-design.md) ??`fixed_output_transport` ê°€ ?´ë? ? íƒ/committed route cell ?„ì´ë©??œì™¸; same-kind path cell sharing?€ ?ˆìš©.

?¬í™”??ê°€ê¹Œìš´ goal?€ penalty ì¦ê?. **v1 (OD-3):** per-goal platform cap(12/72) ì´ˆê³¼ ??alternate `GoalLoadKey` ?°ì„ ; ?„ë? overflowë©?penalty pool fallback ([OD-3](open_decisions.md)).

### ?•ì±…

- capacity-aware **greedy** selector (v0)
- GA??v1 ([OD-4](open_decisions.md))

## ê¸ˆì?

- selection ?¨ê³„?ì„œ layout commit
- candidate ?ì„± enumeration ?œì„œë¥?commit orderë¡??¬ìš©

## ?„ë£Œ ì¡°ê±´

- [x] ?™ì¼ poolÂ·plan?ì„œ ? íƒ ?œì„œ deterministic
- [x] ê³?throughputÂ·?€ route cost ?„ë³´ê°€ ?°ì„ 
- [x] saturated goal??penalty ë°˜ì˜

## ?„ìˆ˜ ?ŒìŠ¤??

```text
test_candidate_selector_prefers_high_throughput_low_cost
test_candidate_selector_penalizes_saturated_goal
test_candidate_selector_is_deterministic
```

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- êµ¬í˜„: `candidate_score.py`, `candidate_selector.py` (`select_gene_candidates_greedy`)
- ?ŒìŠ¤?? `tests/unit/asteroid_lab/test_candidate_selector.py`
- ?ˆê±°??GA: [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md)

## ?¤ìŒ Phase

??[`phase_j_incremental_commit.md`](phase_j_incremental_commit.md)
