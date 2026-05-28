# Asteroid Lab — Miner, Extension, Installation (Document Hub)

Miner, extension, and Lab installation flow content is covered **in this folder only**. Existing Phase documents stay in their original locations; this folder is the **entry point** (table of contents + verdicts + DB facts + narrative).

## Reading order

| # | File | PR | Role |
|---|------|-----|------|
| 1 | [`00_source_of_truth.md`](00_source_of_truth.md) | PR-0 | Source-of-truth priority, evidence layers A–E, conflict rules |
| 2 | [`01_rule_reconciliation.md`](01_rule_reconciliation.md) | PR-0 → PR-1 | Rule verdict table (9 columns) |
| 3 | [`02_doc_drift_matrix.md`](02_doc_drift_matrix.md) | PR-0 | Existing document catalog + drift types + actions |
| 4 | [`03_db_cross_reference.md`](03_db_cross_reference.md) | PR-1 | Normalized DB + dump-reflected row listing |
| 5 | [`04_installation_guide.md`](04_installation_guide.md) | PR-2 | End-to-end installation flow (candidate ≠ confirmed) — **complete** |
| 6 | [`05_island_extractor_variants.md`](05_island_extractor_variants.md) | — | Island extractor default blueprints (balance / omni / fluid) copy canon |

**Parent index:** [`documents/Algorithm/README.md`](../README.md) item 6.

**Design spec:** [`docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md`](../../../docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md)

## What stays outside this folder

| Location | Why we link instead of moving |
|------|---------------------------|
| `documents/Algorithm/asteroid_lab_0*` | Phase RESEARCH contracts |
| `documents/game_rules/shapez2_asteroid_space_transport_throughput.md` | Throughput CANON |
| `django_apps/asteroid_lab/` | Runtime code and tests |
| `docs/domain/asteroid_game_data_snapshot.md` | Consumer DTO contract |

Do not copy Phase body text wholesale into this folder. **Verdicts** and **links** are updated in `01` / `02`.

## Hub status (2026-05-23)

- **Done:** PR-0–PR-2 (`00`–`04`); `05` island extractor copy catalog + `IslandExtractorBlueprint` seed
- **Previous:** PR-0–PR-2 (`00`–`04`); meta alignment refresh (`00`·`01`·`02`)
- **Remaining:** `01` throughput `needs-review` (simulation rate → import); `asteroid_lab_03` RESEARCH body (optional); Lab JS per-control replay labels
