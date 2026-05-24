# Asteroid Lab — Miner / Extension Canon & DB Reconciliation (D2)

**Date:** 2026-05-22  
**Status:** Approved — PR-0 plan: [`2026-05-22-asteroid-miner-extension-reconcile-pr0.md`](../plans/2026-05-22-asteroid-miner-extension-reconcile-pr0.md)  
**Scope:** documentation change only (PR-0/PR-1/PR-2); no code or DB schema changes (PR-0)  
**Language:** K/E — Korean narrative, English enums · paths · table headers · verdict  
**Approach:** D2 Reconcile-first Mixed Guide (structure **#1**, not guide-first D)

**Canonical doc tree (implementation):**  
`documents/Algorithm/asteroid_lab_mining_installation/`

**Related:**

- [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md)
- [`docs/domain/asteroid_game_data_snapshot.md`](../../domain/asteroid_game_data_snapshot.md)
- [`django_apps/asteroid_lab/optimization/gene_template.py`](../../../django_apps/asteroid_lab/optimization/gene_template.py)
- [`documents/Algorithm/README.md`](../../../documents/Algorithm/README.md)

---

## 1. Problem

Asteroid Lab miner/extension installation explanations are scattered across documents, and some `RESEARCH`/`REPORT` docs may diverge from latest solver flow and DB import results. Writing guides first replicates stale CANON.

**Goal:** Realign canonical docs → drift management → narrative guide. Core principle: **candidate creation ≠ confirmed installation**.

---

## 2. Source of Truth (priority stack)

Fixed document: `00_source_of_truth.md`.

| Priority | Source | Role |
|:--:|---|---|
| 1 | Latest `game_data` import DB + dump audit | Distributed **facts** (not one miner table) |
| 2 | `django_apps/asteroid_lab/**` + passing pytest | Lab **runtime behavior** |
| 3 | `ACTIVE` / `CANON` (e.g. `game_rules`, `solver_runtime/*`, `asteroid_lab_09`) | Design **contracts** |
| 4 | `documents/Algorithm/asteroid_lab_0*` marked `RESEARCH` | History / background |
| 5 | replay / NDJSON / artifact | **Observation only** — never algorithm input |

**Conflict rule:**

```text
When RESEARCH/REPORT conflicts with code + tests → mark document for update/delete, not code.
When promoting a row to CANON → requires normalized_db and/or code_invariant and/or test_evidence.
Replay/metrics never override Layer C/D invariants.
```

**Distributed DB fact (normative wording):**

```text
The current game_data dump does not expose miner/extension/throughput as a single dedicated normalized table.
Evidence is distributed across building geometry tables, toolbar placement records, simulation/reflection rows, and Lab code invariants.
```

Korean (installation guide / SoT body):

```text
Current game_data dump does not provide miner/extension/throughput in a single dedicated normalized table.
Evidence is scattered across building geometry, toolbar placement, simulation/reflection rows, and Lab code invariants.
```

**Naming guard:** `BuildingSnapshot` / `TransportRegistryEntry` are **consumer DTOs** (`AsteroidGameDataSnapshot`), not Django ORM model names. In `03_db_cross_reference.md`, use dump/ORM table names (`buildingvariant`, `buildingfootprinttile`, …) in `normalized_db_evidence`; cite DTOs only under `code_invariant` or adapter notes.

---

## 3. Evidence layers (A–E)

Used in `01_rule_reconciliation.md` and `03_db_cross_reference.md`. Do **not** collapse layers into a single “DB evidence” column.

| Layer | Label | Examples | Trust |
|-------|--------|----------|-------|
| **A** | `normalized_db_evidence` | `buildingvariant`, `buildinggroup`, `buildingfootprinttile`, `buildingconnector`, transport registry tables, `toolbar*` | High for geometry/registry |
| **B** | `reflected_db_evidence` | `simulationsystem`, `unknownproperty`, `clrtyperegistryentry`, `simulation_systems` JSON paths | Medium — semi-structured |
| **C** | `code_invariant` | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS`, `throughput_factor_for_extension_count()`, `ExtractorPlacementPolicy.RIM_ONLY` | High for Lab rules |
| **D** | `test_evidence` | pytest paths, `replay_enums` wire values, UI payload contracts | High for behavior lock |
| **E** | `manual_gameplay_evidence` | Player-facing rules when A–D insufficient | Low — explicit only |

**Throughput rule:** Absence of a dedicated rate table is **not** a verdict. Route through B (simulation paths) + C (allowlist) + [`game_rules` CANON](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md) + D tests. Never end a row with “not in DB → BLOCKED”.

---

## 4. Deliverable tree (single naming — no drift)

**Only these filenames.** Do not use `02_db_cross_reference_inventory` or other aliases.

```text
documents/Algorithm/asteroid_lab_mining_installation/
  00_source_of_truth.md
  01_rule_reconciliation.md
  02_doc_drift_matrix.md
  03_db_cross_reference.md
  04_installation_guide.md
```

| File | PR | Purpose |
|------|-----|---------|
| `00_source_of_truth.md` | PR-0 | Priority stack + conflict rules + distributed-DB wording |
| `01_rule_reconciliation.md` | PR-0 | Reconciliation table (schema §5) |
| `02_doc_drift_matrix.md` | PR-0 | Per-legacy-doc drift tracking |
| `03_db_cross_reference.md` | PR-1 | Layer A/B inventory from DB + dump; links to dump paths |
| `04_installation_guide.md` | PR-2 | K/E narrative: in-game → Lab → candidate → selection → commit → replay |

Update [`documents/Algorithm/README.md`](../../../documents/Algorithm/README.md) with one row linking this folder (PR-0).

Mirror summary stays in **this** spec; long tables live under `documents/Algorithm/...`.

---

## 5. Reconciliation table schema (PR-0 seed + PR-1 fill)

**File:** `01_rule_reconciliation.md`

| column | meaning |
|--------|---------|
| `topic` | Rule name |
| `legacy_claim` | Old doc claim |
| `normalized_db_evidence` | Layer A tables/rows (ORM/dump names) |
| `reflected_db_evidence` | Layer B paths/rows |
| `code_invariant` | Layer C symbols |
| `test_evidence` | Layer D pytest / enum |
| `confidence` | `high` / `medium` / `low` |
| `verdict` | `keep` / `rewrite` / `delete` / `needs-review` |
| `action` | Target file/PR |

**PR-0 seed rows (minimum):**

| topic | initial verdict | action |
|-------|-----------------|--------|
| extension max 0..3 | keep (C + D) | link `gene_template` tests |
| throughput 4/8/12/16 | needs-review until B sampled | PR-1 `03` + game_rules cross-check |
| rim-only | rewrite | clarify anchor ≠ install |
| candidate probe | clarify | not commit proof |
| commit reprobe | keep | strong-canon → Phase 7 / tests |
| replay UI mapping | missing-doc | PR-2 §6 + `replay_enums` |

---

## 6. Installation guide outline (PR-2)

**File:** `04_installation_guide.md`

1. In-game rules — miner, extension chain, facing, output belt/pipe, throughput (link game_rules CANON)  
2. Lab input — paste, cleanup, strip miners/extensions, reconstruction  
3. Candidate creation — PatternLibrary / GeneTemplate, bundle 0–3 ext, output_stub, route probe (**not installed**)  
4. Selection — pool, genome/fitness  
5. Confirmed installation — `Gene.commit_order`, commit-time reprobe, reservation, domain rebuild, confirmed / rolled_back  
6. Replay — event types aligned with `django_apps/asteroid_lab/replay/replay_enums.py`

**Required callout box (Korean body, English title optional):**

```text
In Lab, miner/extension is not installed at candidate creation time.
After route feasibility → selection → commit-time reprobe + reservation pass,
placement becomes confirmed.
```

---

## 7. PR boundaries

| PR | Changes | Forbidden |
|----|---------|-----------|
| **PR-0** | Add `00`–`02`, frontmatter `status: AUDIT`, README link | Code, migrations, CANON promotion without evidence |
| **PR-1** | Fill `03_db_cross_reference.md`; extend `01` rows with A/B evidence; optional **read-only** audit script under `scripts/` | Schema changes; declaring throughput CANON from guesswork |
| **PR-2** | `04_installation_guide.md`; drift matrix `action` updates for wording-only fixes | Mass rewrite of `asteroid_lab_0*` series (separate PRs) |

### Success criteria

**PR-0:**

- Every `needs-review` row has **owner**, **evidence gap**, and **next PR target**  
- No row promoted to CANON without A/B/C/D evidence  
- **Does not** require `needs-review = 0`

**PR-1:**

- `03` lists Layer A entities for miner/extension/transport-related variants (e.g. `ExtractorDefaultInternalVariant` footprint in dump)  
- Throughput rows cite B paths and/or explicit “Layer C + game_rules only” with confidence  

**PR-2:**

- Reader can distinguish candidate vs commit without reading Algorithm phase docs  
- Optional program goal: `needs-review = 0` for topics in scope (or deferred list with owners)

---

## 8. Drift matrix (`02_doc_drift_matrix.md`)

Columns: `document | status | claim_summary | drift_type | action | owner`

**drift_type** enum (fixed): `stale-canon-risk`, `wording-risk`, `ok-but-db-check-needed`, `missing-doc`, `strong-canon`

Seed entries:

| document | drift_type | action |
|----------|------------|--------|
| `shapez2_asteroid_space_transport_throughput.md` | stale-canon-risk | PR-1 B-layer sample |
| `asteroid_lab_02_pattern_library.md` | ok-but-db-check-needed | PR-1 footprint cross-check |
| `asteroid_lab_03_candidate_generator.md` | wording-risk | PR-2 link + optional phrase patch PR |
| `asteroid_lab_07_incremental_commit.md` | strong-canon | keep, link from `04` |
| UI / `asteroid_miner_layout_lab.js` | missing-doc | PR-2 §6 |

---

## 9. Out of scope (this program)

- Implementing solver changes  
- Promoting `documents/Algorithm/asteroid_lab_0*` from RESEARCH to CANON in bulk  
- Using replay frames as algorithm input (forbidden invariant)  
- Committing design spec to git (human/agent explicit request only per repo policy)

---

## 10. Self-review (2026-05-22)

| Check | Result |
|-------|--------|
| Placeholders / TBD | None |
| Internal consistency | Single filename tree; DTO vs ORM naming guarded |
| Scope | One documentation program, 3 PRs |
| Ambiguity | `03_db_cross_reference.md` only name for DB inventory |
| PR-0 vs PR-2 success | `needs-review=0` deferred to PR-2+ |

---

## 11. Next step

After user approves this spec → invoke **writing-plans** skill for:

- `docs/superpowers/plans/2026-05-22-asteroid-miner-extension-reconcile.md`  
- Task breakdown per PR-0 / PR-1 / PR-2 with file paths and verification (markdown lint, link check; no pytest for PR-0)
