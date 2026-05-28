---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: en
related_docs:
  - asteroid_lab_mining_installation/01_rule_reconciliation.md
---

# Document Drift Matrix — Miner, Extension Program

Tracks **existing documents** against D2 source-of-truth priority. PR-0 does not bulk-edit `asteroid_lab_0*` bodies. Actions closed by PR-1·PR-2 hub outputs (`03`·`04`) are reflected below.

## `drift_type` (fixed)

`stale-canon-risk` · `wording-risk` · `ok-but-db-check-needed` · `missing-doc` · `strong-canon`

## Table

| Document | status | Claim summary | drift_type | Action | owner |
|------|--------|-----------|------------|------|-------|
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) | CANON | Throughput ×4..×16 absolute values | stale-canon-risk | **Done (partial):** `03` no rate table·2 variants; `01` throughput stays `needs-review` | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) | RESEARCH | linear 0–3 extension; `ExtensionAttachment` | ok-but-db-check-needed | **Done:** `03` footprint·variant; `04` §1·§3 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) | RESEARCH | rim-only; no greedy install | wording-risk | **Partial:** `04` §Key·§3; optional `03` body patch remains | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md) | RESEARCH | commit-time reprobe; `Gene.commit_order` | strong-canon | **Done:** keep; `04` §5 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) | RESEARCH | placement ≠ commit; replay input prohibition | strong-canon | **Done:** keep; cite `04` | asteroid-lab |
| [`documents/plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`](../../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md) | REPORT | Progress summary only | ok-but-db-check-needed | Do not treat as contract; link from `00` | asteroid-lab |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | — | replay scrub, solver feedback | missing-doc | **Partial:** `04` §6 event table; UI per-control label map remains | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md) | ACTIVE | Unified lab replay timeline | strong-canon | **Done:** keep; `04` §6 wire values | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_debug.md`](../asteroid_lab_09_replay_debug.md) | ARCHIVED | dual-track history | ok-but-db-check-needed | Do not cite as CANON; archaeology links only | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) | RESEARCH | Runtime replay wiring; output-only | strong-canon | **Done:** `04` §6; supplements `09` | asteroid-lab |

## Update checkpoints

- [x] PR-1: `03` reflected — `game_rules`·`asteroid_lab_02` actions done (partial)
- [x] PR-2: `04` reflected — `00`·`07`·`09`·`12`·replay JS rows partial/complete
- [ ] Re-evaluate `game_rules` `stale-canon-risk` after throughput simulation import
- [ ] Optional: patch `asteroid_lab_03` RESEARCH body rim-only wording
