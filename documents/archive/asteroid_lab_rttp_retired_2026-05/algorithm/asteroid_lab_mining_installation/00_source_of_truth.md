---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: en
supersedes: []
related_docs:
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - docs/domain/asteroid_game_data_snapshot.md
---

# Asteroid Lab — Source-of-Truth Priority (Miner, Extension, Installation)

## Document hub (single-folder collection)

Enter scattered documents, code, and DB evidence through **`asteroid_lab_mining_installation/` in one place**. Do not move every legacy file here. Instead:

- **Index:** [`README.md`](README.md) — reading order `00` → `04`
- **Verdicts:** `01` contradiction table, `02` drift matrix
- **DB facts:** `03` cross-reference (PR-1+)
- **Narrative:** `04` installation guide (PR-2)

This folder is an **audit hub** for source-of-truth realignment (D2) on **miner, extension, and installation flow**. `00`–`04` and `README` form one set; bulk edits to external Phase RESEARCH bodies are out of hub scope. Open items are tracked via `needs-review` in `01` and the action column in `02`.

## Priority stack

| Rank | Source | Role |
|:--:|---|---|
| 1 | Latest `game_data` import DB + dump audit | Distributed **facts** (no single miner-only table) |
| 2 | `django_apps/asteroid_lab/**` + passing pytest | Lab **runtime behavior** |
| 3 | `ACTIVE` / `CANON` (`game_rules`, `solver_runtime/*`, `asteroid_lab_09`, etc.) | **Design contracts** |
| 4 | `documents/Algorithm/asteroid_lab_0*` (`RESEARCH`) | History and background |
| 5 | replay / NDJSON / artifact | **Observation only** — not algorithm input |

## Conflict rules

```text
RESEARCH/REPORT vs code/tests → do not change code; mark document rows in 02_doc_drift_matrix for edit/delete.
CANON promotion → requires normalized_db and/or code_invariant and/or test_evidence (see 01).
replay/metrics do not override code invariants (layers C/D).
```

## Distributed DB facts (normative statement)

```text
The current game_data dump does not provide miner/extension/throughput in a single dedicated normalized table.
Evidence is distributed across building geometry, toolbar placement, simulation/reflection rows, and Lab code invariants.
```

## Evidence layers (A–E)

| Layer | Column name | Examples | Confidence |
|----|------------|------|--------|
| A | `normalized_db_evidence` | `buildingvariant`, `buildinggroup`, `buildingfootprinttile`, `buildingconnector`, transport registry, `toolbar*` | High for geometry/registry |
| B | `reflected_db_evidence` | `simulationsystem`, `unknownproperty`, `clrtyperegistryentry`, `simulation_systems` JSON paths | Medium |
| C | `code_invariant` | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS`, `throughput_factor_for_extension_count()`, `ExtractorPlacementPolicy.RIM_ONLY` | High for Lab rules |
| D | `test_evidence` | pytest paths, `ReplayEventType` wire values | High for behavior lock-in |
| E | `manual_gameplay_evidence` | Gameplay rules only when A–D are insufficient | Low — only when explicit |

**Throughput:** Do not close a verdict solely because no dedicated rate table exists. Connect via B + C + [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) + D. Do not close rows with 「not in DB → BLOCKED」.

## Naming rules

`BuildingSnapshot` / `TransportRegistryEntry` are **consumer DTOs** (`AsteroidGameDataSnapshot`), not Django ORM model names. Layer A uses dump/ORM table names; cite DTOs only in layer C or adapter notes.

## PR file map

| File | PR |
|------|-----|
| `00_source_of_truth.md` | PR-0 |
| `01_rule_reconciliation.md` | PR-0 |
| `02_doc_drift_matrix.md` | PR-0 |
| `03_db_cross_reference.md` | PR-1 |
| `04_installation_guide.md` | PR-2 |

## Hub completion criteria (D2 program)

- Every `needs-review` row in `01` specifies **owner**, **evidence gap**, and **next PR**
- Do not promote `keep` as CANON substitute without C/D evidence (throughput may stay `needs-review`)
- **`needs-review = 0` is a program-wide goal**, not a PR-0-only completion condition
- Meta wording in `00`–`04` and `README` must match actual file layout
