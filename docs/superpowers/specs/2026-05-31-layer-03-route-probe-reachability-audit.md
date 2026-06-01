---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-31
supersedes: []
related_docs:
  - docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
---

# Layer 03 Route Probe Reachability Audit (PR-C)

## Problem

`exterior_connector_unreachable` collapses distinct failure modes (void component
disconnect, probe budget exhaustion, true walkable dead-end, missing goals, invalid stub)
into one reject reason. That blocks deciding whether follow-up work belongs in L2 goal
coverage (PR-A) or L3 geometry (PR-B).

## Goal

Split exterior goal failures into enumerated reject reasons and attach a structured
`RouteProbeDiagnostic` on failed route probes.

## Non-goals

- Changing L2 connector placement policy (PR-A).
- Changing gene priority / footprint policy (PR-B).
- Hard-enforcing trunk saturation capacity (CANON: share/merge is soft).

## Contract

### Reject reasons (replace monolithic `exterior_connector_unreachable` emission)

| Enum | When |
| --- | --- |
| `exterior_goal_unreachable_no_goals` | No route goals for candidate transport kind |
| `exterior_goal_unreachable_invalid_stub_component` | Probe start not walkable in domain |
| `exterior_goal_unreachable_no_same_void_component` | ≥1 goal exists but none share void component with stub void |
| `exterior_goal_unreachable_probe_limit_hit` | Same-component goal reachable in walkable graph but shortest path length > `LAYER03_ROUTE_PROBE_MAX_PATH_CELLS`, or expanded-node budget exhausted while frontier remains |
| `exterior_goal_unreachable_frontier_exhausted` | Walkable BFS frontier exhausted; no goal reachable |

Legacy enum value `exterior_connector_unreachable` remains for backward compatibility in
metrics readers but MUST NOT be emitted by `weighted_route_probe` / `immediate_route_probe`.

### `RouteProbeDiagnostic`

Attached on failed probes (`route_probe_diagnostic` on `RouteProbedBundleCandidate`).

Fields: `anchor_coord`, `stub_coord`, `output_dir`, `transport_kind`, `bfs_limit`,
`visited_count`, `max_depth_reached`, `frontier_exhausted`, `probe_limit_hit`,
`nearest_goal_manhattan`, `reachable_goal_count`, `same_void_component_goal_count`,
`stub_component_id`, `goal_component_ids`, `detailed_unreachable_reason`.

Void component ids are deterministic labels over `external_void_cells` (4-neighbor BFS).

### Invariants

- Corridor / trunk share is NOT a hard route blocker (commit reprobe unchanged).
- L2 connector count is goal coordinate cardinality, not miner cap.
- Successful probes carry `route_probe_diagnostic is None`.

## Acceptance tests

See `tests/unit/asteroid_lab/layers/test_route_probe_reachability_audit.py`.

## PR sequence

PR-C (this spec) → PR-A (L2 coverage, if diagnostics show component/coverage skew) →
PR-B (small-gene priority, if `mining_cell_off_field` dominates).
