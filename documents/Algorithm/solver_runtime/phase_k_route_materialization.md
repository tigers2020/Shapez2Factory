---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: K
pr: 6
related_docs:
  - documents/Algorithm/solver_runtime/open_decisions.md
---

# Phase K ? Route Network Materialization

## Purpose

Convert confirmed route reservations to actual belt/pipe sprite/layout structure. **merger/splitter conversion happens only in this stage.**

## Input

```text
confirmed placements
confirmed route reservations
shared path graph
transport kind
flow direction observations
```

## Output

```text
MaterializedLayoutCells
```

## Tasks

### Conversion rules

```text
single path ? straight / turn
multiple incoming same kind ? merger / yMerger / triple merger
multiple outgoing same kind ? splitter / ySplitter / triple splitter
vertical / lift variants ? later
```

### OD-1 recommendation

Prepend `fixed_output_transport` cell **before** reservation path during materialization ([`open_decisions.md`](open_decisions.md)).

## Forbidden

- candidate placement stage merger/splitter conversion
- Pre-install transport in void ([§0.2](00_core_principles.md))
- shape belt / fluid pipe sharing same cell

## Completion criteria

- [x] straight/turn match path topology
- [x] shared path merger/splitter selection deterministic
- [x] shape/fluid overlap reject

## Prerequisite phase

```text
test_route_materializer_creates_straight_and_turns
test_route_materializer_merges_same_kind_shared_paths
test_route_materializer_rejects_shape_fluid_overlap
test_route_materializer_selects_y_or_triple_merger
```

## Hardening tests (PR6)

```text
test_full_path_prepends_fixed_output_transport
test_full_path_dedupes_consecutive_duplicate
test_route_materializer_splits_shared_trunk
test_route_materializer_selects_triple_splitter_at_hub
test_route_materializer_cell_order_is_deterministic
```

## Related code?documents

- Implementation: `route_network_materializer.py` (`materialize_route_network`, `pick_tile_type`)
- DTO: `materialization_dtos.py`
- Tests: `tests/unit/asteroid_lab/test_route_materializer.py`

## Placement equipment (K2)

CONFIRMED extractor?extension tiles: [`phase_k2_placement_materialization.md`](phase_k2_placement_materialization.md) (`merge_materialized_layout` after route cells).

## Next Phase

? [`phase_l_final_validation.md`](phase_l_final_validation.md) (PR7: `commit_selected_candidates` ? route + placement materialize ? read-only validation ? replay; [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md))
