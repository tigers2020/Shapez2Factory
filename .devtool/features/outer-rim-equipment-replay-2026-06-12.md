---
status: verify
modified: 2026-06-12
---

# Outer rim miner/extension replay placement fix

## Scope

Fix L3 committed miner + extension replay overlay when `append_result` is empty (runtime wire deserialize / composed replay). Wrong: all cells `candidate_miner`, rotation 0, extension sprites missing.

## Acceptance

- [x] `build_persistent_committed_equipment_overlay_wire` emits `shape_miner` / `shape_miner_extension` with correct rotation when append cells absent
- [x] `deserialize_l3_wire` restores `append_result` from committed placements
- [x] Regression tests green for run #7 wire sample (north-facing anchor rotation 3)

## Progress

- 2026-06-12 — align — user report: outer_rim M/E placement weird on `copy-import-52921cd2` run #7; root cause: empty append fallback paints all equipment as `candidate_miner` @ rot 0
- 2026-06-12 — implement — rebuild append on deserialize + synthesize on replay projection; fix committed fallback overlay kinds/rotation; tests 6/6 + replay 17/17; refreshed run #7 cache
