# Runtime Authority Drift Report

## Scope

Requested canonical paths under `documents/canon/` are not present in this checkout. The repository inventory marks the corresponding files under `documents/Algorithm/mining_solver_cursor_sessions/` as `CANON`, and also notes that the physical `documents/canon/` split is not complete. This audit therefore uses the inventory-backed canonical files:

- `documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md`
- `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md`
- `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md`
- `documents/Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md`
- `documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md`
- `documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md`

This is a read-only runtime authority audit. No code behavior was changed.

**Superseded passages (see [`authority_drift_matrix.md`](authority_drift_matrix.md)):** As of the 2026-05-13 authority matrix audit, [`reclaim/reclaim_corridors.py`](django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py) no longer merges corridor **authority** from `trunk_load` (`merge_step4_corridor_routing_mapping` ignores it) and no longer rebuilds **hard/soft** protected sets from `pass3_trace` in `protected_corridors_for_reclaim`. Matrix IDs **D1–D12** replace row-level truth for those areas; table rows below that still describe `trunk_load`/`pass3_trace` as reclaim **hard/soft** sources are **historical** relative to current code.

## Canonical Authority Baseline

- STEP4 route state authority must be explicit. `08_step4_routing.md:257-267` says the STEP4 result must carry route state, Pass3 gate source must be `explicit_arg`, and `trunk_load` is only a result mirror, not proof of STEP4 commit.
- Protected corridors must move through `candidate_corridor -> soft_protected -> hard_protected`. `12_protected_corridor.md:44-69` says hard and soft status is created only after STEP4 commit; final validation must not invent hard corridors.
- Pass3 may not touch hard protected corridors, and soft corridor removal requires replacement plus atomic replace. `12_protected_corridor.md:85-87`.
- Trace and replay layers are output/debug layers. `14_step10_replay_ui.md:28-31`, `14_step10_replay_ui.md:58-65`, and `14_step10_replay_ui.md:101` place NDJSON, replay, trace events, and `trunk_load` metrics in output/report surfaces.
- Recovery is a bounded branch, not a linear always-run repair pass. `02_pipeline_control_flow.md:34`, `02_pipeline_control_flow.md:107`, and `11_step8_recovery.md:11-25`.
- Capacity and trunk edge load are telemetry. `01_project_overview.md:102`, `01_project_overview.md:185-186` describe edge load as computed/recorded totals, while route ownership remains in explicit solver state.

## Runtime Flow Diagram

```text
Intended authority:

STEP4
  -> Step4RoutingResult.routing_state
       -> final_route_cells
       -> hard_protected_corridors
       -> soft_protected_corridors
       -> downstream Pass3, Reclaim, Recovery

Observed authority drift:

STEP4
  -> Step4RoutingResult.routing_state
  -> Step4RoutingResult.trunk_load
       -> merge_step4_corridor_routing_mapping()
            -> protected corridor DTO for runtime guards
       -> pass3 edge congestion weights
       -> recovery high-sharing victim skip cells

Pass3
  -> pass3_trace
       -> protected_corridors_for_reclaim()
            -> hard/soft protected corridor reconstruction
       -> reclaim transport budget and permission gates
       -> atomic soft replacement input

Reclaim
  -> live mining_map transport scan
       -> final_route_cells
       -> mineable exclusion
       -> placement rejection

Recovery
  -> reuses STEP4 trunk_load and Pass3 p3_trace
       -> Pass3 and Reclaim routing decisions

Replay / NDJSON / solver_summary
  <- should receive snapshots only
  -> mostly output-only, but helper factories and trace dictionaries are reused by runtime paths
```

## Authority Drift Findings

| File path | Function | Exact authority drift | Canonical violation | Risk |
|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | `merge_step4_corridor_routing_mapping` | Merges `routing_state` with `trunk_load`; if routing state fields are absent or empty, imports `protected_corridors`, `hard_protected_corridors`, and `soft_protected_corridors` from `trunk_load`. | Violates `08_step4_routing.md:257-267`: `trunk_load` mirrors STEP4 result and must not become authority. Violates `12_protected_corridor.md:44-69`: protected status must come from committed STEP4 route state. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | `_corridors_from_pass3_trace_protected_block` | Reconstructs `ProtectedCorridorSets` from `pass3_trace["protected_corridors"]` and marks source as `pass3_trace`. | Violates `14_step10_replay_ui.md:28-31` and `14_step10_replay_ui.md:58-65`: trace/replay data is output/debug. Violates runtime-only authority requirement for hard/soft corridors. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | `hard_soft_corridors_from_pass3_trace` | Rebuilds hard and soft protected sets from `p3e3_guarded_commit_candidate` touched-cell telemetry. | Violates `12_protected_corridor.md:85-87`: hard and soft corridors constrain Pass3, not the other way around. A Pass3 trace event cannot define protected-corridor authority. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | `_merge_existing_layout_solver_hints_into_soft` | Merges ELA hint cells and cleanup candidates into `soft_protected` runtime set. | Violates `12_protected_corridor.md:44-69`: ELA component corridors may become candidates, but soft/hard classification happens after STEP4 commit. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py` | `protected_corridors_for_reclaim` | Fallback chain is `solver_routing_state -> pass3_trace protected block -> p3e3 touched hard/soft trace -> empty -> ELA hints merged into soft`. | Violates the single-authority rule: reclaim should consume `routing_state`, not debug mirrors or hints. This is the central protected-corridor authority drift. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_shadow_scan.py` | `_p4_scan_shadow_candidates` | Calls `protected_corridors_read_for_reclaim()` with `pass3_trace`; resulting hard/soft sets decide mineable cells and reclaim candidate exclusions. Also reads `pass3_trace["pass3_internal_transport_saved"]` for reclaim transport budget. | Violates `14_step10_replay_ui.md:58-65`: trace event data is output. Violates `12_step_protected_corridor.md` contract by letting trace-derived corridor sets block runtime candidate generation. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_map_ops.py` | `_all_transport_cells`, `_mineable_cur_for_reclaim`, `_p4_overlap_reject_reason` | Derives `final_route_cells` from all live map transport cells, then uses that derived set with hard/soft corridors to remove mineable cells and reject placements. | Violates `08_step4_routing.md:257-267`: final route authority must be explicit route state, not inferred from current map contents or mirrors. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_shadow_commit_b1_provisional.py` | `try_commit_b1_provisional_candidate` | Builds `final_route_cells` from `_all_transport_cells(mining_map)` and uses `protected_corridors_read_for_reclaim(pass3_trace, solver_routing_state)` to reject candidate placement. | Mixes live map inference, routing state, and Pass3 trace into one authority set. Violates STEP4 explicit-authority rule and trace-output-only rule. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_shadow_commit_b2_incremental.py` | `try_commit_b2_incremental_route` | Reads `pass3_trace["pass3_internal_transport_saved"]` to cap or reject reclaim transport additions. | Violates the output-only trace rule when Pass3 trace metrics drive runtime acceptance. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_shadow_commit_loop.py` | `run_reclaim_shadow_commit_loop` | Passes `pass3_trace` and `solver_routing_state` through scan, provisional commit, and soft replacement paths. Reads commit trace fields such as `p4_reclaim_final_route_cells_added` and `p4_reclaim_last_soft_protected_candidate_cells` back into loop state. | Runtime state is partially driven by trace dictionaries. Violates `14_step10_replay_ui.md:58-65` and the `routing_state`-only authority rule. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/routing/protected_corridor_replace.py` | `attempt_atomic_soft_corridor_replacement` | Reads protected corridors through `protected_corridors_read_for_reclaim(pass3_trace, solver_routing_state)` and then uses that result to reject hard/soft overlap. | Atomic soft replacement is a legitimate runtime operation, but its guard authority may come from Pass3 trace or `trunk_load` fallback instead of `routing_state`. | CRITICAL |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_transport.py` | `run_pass3_transport_reconstruction` | Accepts `trunk_load` and `routing_state_summary`; docstring states `trunk_load` is used for P3-E2/P3-E3 lexicographic congestion weights and recovery-mode greedy skip behavior. | Violates `08_step4_routing.md:257-267` and `14_step10_replay_ui.md:101`: `trunk_load` is a trace/metric mirror, not route authority or routing cost authority. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_e2_shadow.py` | `run_p3e2_shadow_reroute` | Builds edge congestion weights from `trunk_load`, merges routing state with `trunk_load`, then reads protected corridors through a replay-oriented corridor read factory for runtime hard guards. | Mixes route authority with mirror load metrics and replay read infrastructure. Violates STEP4 explicit-authority and protected-corridor authority contracts. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_e3_guarded_lex_collect.py` | `evaluate_guarded_collect_candidates` | Builds lexicographic routing weights from `trunk_load`, influencing candidate route selection. | Makes a mirror/debug load surface affect runtime route choice. Violates `trunk_load` output-only authority boundary. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_greedy_core.py` | `run_greedy_pass3_reconstruction` | In recovery mode, derives `skip_victim_cells` from high-sharing trunk edges in `trunk_load`, preventing some transport cells from becoming removal victims. | Uses trunk-load mirror as recovery routing authority. Violates `11_step8_recovery.md:11-25` bounded branch semantics and `08_step4_routing.md:257-267` mirror-only rule. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_trunk_load.py` | `trunk_edge_load_to_pass3_edge_weights`, `cells_on_high_sharing_trunk_edges` | Converts `trunk_load` into runtime Pass3 route weights and recovery victim-skip cells. | The helper itself is deterministic, but its runtime use turns output load mirrors into routing policy. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py` | `_attempt_recovery_stage` | Correctly states replay/NDJSON/summary are not inputs, but passes `step4.step4_result.trunk_load` into Pass3 and `pass3.p3_trace` into P4 reclaim during recovery. | Recovery remains bounded, but its branch internals are driven by `trunk_load` and Pass3 trace surfaces. Violates mirror/output-only authority boundaries. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_permission.py` | `p4_reclaim_permission_snapshot`, `post_reclaim_pass3_permission`, `post_reclaim_pass3_gate` | Uses `pass3_trace.get("pass3_skipped")` and Pass3/reclaim summary counters as control gates. | Summary and trace fields become branch authority. This is lower blast radius than protected-corridor reconstruction but still mixes runtime semantic state with output telemetry. | MEDIUM |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_recovery_trigger.py` | `evaluate_step4_recovery_trigger` | Contains a recovery trigger fallback reading reserved capacity-failure signal from `result.trunk_load`. Current code path appears reserved, but the authority hook exists. | Recovery trigger authority should come from explicit STEP4 result state, not `trunk_load`. Violates `02_pipeline_control_flow.md:150-151` and `08_step4_routing.md:257-267` if activated. | MEDIUM |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/routing/route_adapter.py` | `route_adapter_input_for_pass3_stub` | Builds `final_route_cells` from `same_kind_transport_cells` scanned from the map for Pass3 stub routing. | Violates the strict runtime authority rule that `final_route_cells` must come from `routing_state`, not from live map transport scans. | HIGH |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridor_read_factory.py` | `protected_corridors_read_from_routing_state` | Module says it is a replay/STEP10 read model, but runtime code imports it after merging routing state with `trunk_load`. | Read factory code is not the root bug, but runtime use blurs replay read models and runtime authority. | MEDIUM |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py` | `finalize_solver_result` | Reads `routing_state` for final assertions and summary, then mirrors `trunk_load` and replay overlays into output. Mostly output-only. | No direct runtime repair found here. Residual risk is mixed summary assembly, not route authority. | LOW |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_corridors.py` | `latest_routing_state_at_timeline_index`, `effective_trunk_load_overlay_at_timeline_index` | Replay-only timeline helpers. No runtime routing import found in audited path. | Safe if kept out of runtime routing. | LOW |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_trace.py` | `trace_event` and NDJSON mirror helpers | Writes trace output and debug NDJSON. No direct algorithmic read found. | Safe output layer. Risk is downstream consumers reading its dictionaries as authority, not this writer. | LOW |

## Exact Fallback Chain Analysis

### 1. Protected corridor reconstruction

```text
protected_corridors_read_for_reclaim()
  -> protected_corridors_for_reclaim()
       -> if solver_routing_state exists:
            protected_corridors_read_from_routing_state(solver_routing_state)
            source = "routing_state"
       -> else if pass3_trace["protected_corridors"] exists:
            _corridors_from_pass3_trace_protected_block()
            source = "pass3_trace"
       -> else if pass3_trace contains p3e3_guarded_commit_candidate touched cells:
            hard_soft_corridors_from_pass3_trace()
            source = "pass3_trace_p3e3"
       -> else:
            empty ProtectedCorridorSets
       -> always:
            _merge_existing_layout_solver_hints_into_soft()
            source += "+ela_hints"
```

Authority drift: this chain explicitly allows Pass3 trace and ELA hint data to become hard/soft protected-corridor runtime state. It also hides the drift by returning a normalized `ProtectedCorridorSets` DTO, so downstream code cannot tell whether authority came from STEP4 or debug mirrors unless it inspects `source`.

### 2. Reclaim routing authority

```text
P4 scan / commit
  -> final_route_cells = _all_transport_cells(mining_map)
  -> hard/soft = protected_corridors_read_for_reclaim(pass3_trace, solver_routing_state)
  -> mineable_cur = mineable cells - final_route_cells - hard - soft
  -> candidate rejection uses final_route_cells, hard, soft
```

Authority drift: reclaim treats all map transport as final route authority and treats fallback corridor DTOs as hard/soft guards. This can make provisional, replay-derived, or mirror-derived cells block new mining candidates.

### 3. Recovery authority

```text
_attempt_recovery_stage()
  -> uses STEP4 routing snapshot
  -> passes step4_result.trunk_load into run_pass3_stage()
  -> Pass3 uses trunk_load for edge weights and victim skip rules
  -> passes pass3.p3_trace into run_p4_reclaim_stage()
  -> P4 may reconstruct protected corridors from pass3_trace
```

Authority drift: recovery is bounded at orchestration level, but inside the branch, `trunk_load` and `pass3_trace` shape runtime decisions. That means recovery can replay or amplify stale mirrors rather than relying only on `routing_state`.

### 4. Routing state restoration and mirror chain

```text
Step4RoutingResult
  -> routing_state
  -> trunk_load

solver_routing_state_for_p4_reclaim(step4_result)
  -> merge_step4_corridor_routing_mapping(routing_state, trunk_load)
       -> routing_state fields win when non-empty
       -> trunk_load protected-corridor fields fill missing/empty fields
```

Authority drift: the merge function makes authority implicit. Empty `routing_state` fields can be silently backfilled from `trunk_load`, so downstream code receives something shaped like routing state even when it contains mirror-derived data.

### 5. Runtime semantic state and replay/debug state mixing

```text
trace dictionaries
  -> commit_tr fields feed reclaim loop state

pass3_trace
  -> permission gates
  -> reclaim budget
  -> protected-corridor reconstruction
  -> soft replacement guard inputs

replay read model
  -> imported by runtime Pass3 after trunk_load merge
```

Authority drift: output-shaped dictionaries and replay-friendly read models are reused as runtime inputs. This is the main architectural problem because field names like `protected_corridors` and `final_route_cells` look authoritative regardless of whether their source was STEP4 `routing_state`, Pass3 debug state, or a mirror.

## Deletion Candidates

These are deletion candidates only. No code changes were made.

1. Delete the `trunk_load` fallback branch in `merge_step4_corridor_routing_mapping()`. Runtime callers should fail closed or receive empty non-authoritative data when `routing_state` is missing.
2. Delete `_corridors_from_pass3_trace_protected_block()` from runtime reclaim paths. If useful, keep it only under replay/debug assembly.
3. Delete `hard_soft_corridors_from_pass3_trace()` from runtime reclaim and soft replacement paths. Pass3 touched-cell telemetry must not define protected corridors.
4. Stop merging `ExistingLayoutSolverHints` into `soft_protected` runtime sets. Keep those cells as candidate or diagnostic fields unless STEP4 commits them into `routing_state`.
5. Replace runtime `final_route_cells = _all_transport_cells(mining_map)` authority with explicit `routing_state.final_route_cells`. If the field is missing, add a regression test first and fail the audit path rather than inferring from the map.
6. Remove `trunk_load` as a source for Pass3 routing weights and recovery victim-skip rules, or introduce an explicit runtime load authority only after a documented contract change.
7. Split replay corridor read factories from runtime corridor authority readers so runtime code cannot accidentally consume replay-normalized DTOs.
8. Move summary/trace counters used by `solver_permission.py` into explicit branch-result fields if those gates are intentional runtime semantics.

## Regression Risk Notes

- Existing reclaim tests likely encode fallback behavior. Tests around `tests/unit/shapez_asteroid/test_reclaim_shadow.py` include scenarios for Pass3-trace corridor fallback and STEP4 routing-state protected corridors; those will need contract updates before deletion.
- Pass3 route choices may change if `trunk_load`-derived congestion weights are removed. This can affect output density and candidate ordering without changing extractor placement semantics.
- Reclaim candidate counts can shift when `final_route_cells` stops being inferred from all map transport cells.
- Replay and solver summary output can remain stable if mirrors are still written after the authoritative runtime state is computed.
- Final validation was not found to invent new routes in the audited paths. Its main role appears assertion and output assembly, with low risk compared to reclaim and Pass3.

## Primary Root Cause

The largest current runtime authority problem is not a single bad field name; it is a normalized fallback architecture that converts mirror/debug surfaces into authoritative DTOs. The most severe instance is `protected_corridors_for_reclaim()`, because it accepts `routing_state`, `trunk_load`-merged state, `pass3_trace`, and ELA hints, then returns one `ProtectedCorridorSets` object used by reclaim and soft replacement as if all sources were equally authoritative.

This can produce downstream symptoms such as false reclaim blocking, corridors that appear hard or soft without STEP4 authority, Pass3/recovery paths preserving or avoiding cells because of stale load mirrors, and telemetry that looks consistent because output summaries are generated from the same mixed state.

## Suggested Read-Only Regression Probe

Smallest probe before changing code:

1. Add a temporary test fixture or script that builds a `Step4RoutingResult` with an empty or missing `routing_state` protected-corridor set and a non-empty `trunk_load["protected_corridors"]`.
2. Call `solver_routing_state_for_p4_reclaim()` and then `protected_corridors_read_for_reclaim()`.
3. Assert the current behavior imports hard/soft corridor cells from `trunk_load`.
4. Mark the future expected behavior as rejecting or ignoring mirror-derived corridors once the fix phase begins.

Second probe:

1. Call `protected_corridors_for_reclaim()` with `solver_routing_state=None` and a `pass3_trace` containing `protected_corridors` or `p3e3_guarded_commit_candidate`.
2. Confirm the returned source is `pass3_trace` or `pass3_trace_p3e3`.
3. Use that as the regression gate for deleting trace-derived runtime authority.

No UI behavior is required for either probe.
