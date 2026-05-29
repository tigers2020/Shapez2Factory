# Miner Seed Decontamination — Design Spec

**Status:** Approved (contract review 2026-05-28)  
**Date:** 2026-05-28  
**Track:** Asteroid Lab genetic sample / miner layout seed authority  

> **Catalog follow-up (2026-05-28):** Canonical row count and dedupe rules are superseded for ingest by [**19-equivalence spec**](2026-05-28-miner-seed-19-equivalence-design.md) (19 `miner_seed_v2` rows, `equivalence_signature`, 19-line bootstrap). This document remains authoritative for coordinates (§2), `MinerSeedPattern` (§7), and PR-Legacy / PR-RTTP split. PR-Seed history (14 rows) is preserved for forensics.

**Related:**

- **19-equivalence catalog (follow-up):** [`2026-05-28-miner-seed-19-equivalence-design.md`](2026-05-28-miner-seed-19-equivalence-design.md)
- Bootstrap evidence: `var/default_miner_pattern.txt` (14 SHAPEZ2 copy strings at PR-Seed approval; **19 lines** per follow-up spec)
- Copy JSON contract: [`documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md`](../../../documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md)
- Retired exhaustive seed plan (superseded): [`documents/ai/plans/exhaustive_sample_gene_seed.md`](../../../documents/ai/plans/exhaustive_sample_gene_seed.md)
- Parent decontamination authority: [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md)

**Naming:** **Miner seed decontamination** is **not** RTTP algorithm work. RTTP is retired; see §6.

---

## §1 — Problem and goals

### Problem

1. **Wrong canonical source:** `GeneticSample` rows seeded by `exhaustive_sample_gene_v1` use an abstract/raw grid (`abstract_grid_to_raw_xy`, `X==0` rejection) that conflicts with in-game island-local paste coordinates.
2. **Duplicate identity:** Same topology is stored twice (belt vs pipe) and implied four-way rotation expansion in the old generator path.
3. **Broken export bridge:** `genetic_sample_gene_export.gene_template_from_genetic_sample` resolves `gene_key` via an in-memory exhaustive cache instead of the DB row’s `code` / `decoded_json`.
4. **Legacy pollution:** `GeneTemplate`, fixture JSON loaders, `PatternTemplate` / `PatternVariant` (lab), and RTTP remnants confuse the active layer-stack solver contract.

### Goals

| Goal | Contract |
|------|----------|
| Canonical store | Exactly **14** active miner seed rows in `GeneticSample` (DB) |
| Bootstrap only | `var/default_miner_pattern.txt` is ingest evidence; **runtime must not read it** |
| Resource projection | Shape/fluid (belt/pipe) differ only at **projection/encode** time — **no** 28 DB rows |
| DTO rename | Replace `GeneTemplate` with **`MinerSeedPattern`** (in-memory only) |
| Coordinate hygiene | Remove `x==0` / `X==0` **reject assertions** on solver-facing and seed paths (§2) |
| RTTP | Hard delete in separate PR; no archive trees |

### Non-goals (this track)

- New solver algorithm beyond seed lookup → candidate → route probe
- Fluid-specific manual paste files (shape-only seeds until user adds them)
- Preserving `documents/archive/*rttp*` trees (git history is the archive)

---

## §2 — Coordinate frame contract (normative)

Three frames must not be conflated. **Do not** use “world map forbids x==0” as a solver validator.

### Frames

| Frame | `X` / `x == 0` | Role |
|-------|----------------|------|
| **Copy JSON island-local** | **`X == 0` allowed** | Seed `code`, `GeneticSample.decoded_json` (normative input) |
| **Raw game-global blueprint** | `x == 0` may be absent in export encoding | **Observation only** at decode/import boundary — not a solver gate |
| **Server / reconstruction / optimization dense coord** | **`x == 0` allowed** | `MinerSeedPattern`, `ReconstructionCompleteMap`, route/candidate/probe DTOs — **no reject assert** |

### Forbidden (remove or fail CI if reintroduced)

```text
- Rejecting seed decode when island-local X == 0
- Rejecting server / reconstruction / optimization coordinates when x == 0
- assert_blueprint_entries_raw_x_nonzero (and equivalents) on seed ingest, solver, or runtime paths
- abstract_grid_to_raw_xy as the canonical mapping from user paste to stored seed
- Using “raw global has no x==0 column” as a validator/gate (observation in docs only)
```

### Allowed

- Documenting that some raw global export encodings omit an `x == 0` column (forensic note only)
- World-map helpers that **construct** coords without `x==0` for specific BFS layouts **only where** the API explicitly documents that construction rule — not as a universal rejection of `x==0` on incoming evidence

### Preservation rule

`GeneticSample.decoded_json` **preserves** copy JSON island-local entries (including omitted keys normalized to `0` per `copy_json_coords`).

---

## §3 — Authority ladder

```text
[L0 evidence]  var/default_miner_pattern.txt
                 bootstrap reference | manual seed source | forensic evidence
                 FORBIDDEN: runtime solver input | test fixture SoT | direct candidate generation input

[L1 canonical] GeneticSample (exactly 14 active miner seeds)
                 gene_key + code + decoded_json + metadata_json (miner_seed_v1)

[L2 runtime]   MinerSeedPattern (in-memory DTO, not ORM)
                 built from L1 decoded_json + topology_signature

[L3 projection] resource_kind (shape | fluid) → layout `T` swap + R via ports_compatible
[L4 candidate] encode → local validation → route probe → normal / rejected pool
```

---

## §4 — GeneticSample contract (v1)

Use existing columns for first ingest; no new DB columns required in PR-Seed.

### Row count and keys

| Field | Value |
|-------|--------|
| Active seed rows | **14** (`metadata_json.is_seed == true`, `schema == "miner_seed_v1"`) |
| `gene_key` | `miner_seed_01` … `miner_seed_14` (unique) |
| `name` | Display only, e.g. `Seed ext=3 rank=01` |
| `code` | Original SHAPEZ2 line from bootstrap file (byte-identical after ingest) |
| `decoded_json` | Populated via model `clean()` / decode pipeline with island meta attached |

### `metadata_json` schema (`miner_seed_v1`)

```json
{
  "schema": "miner_seed_v1",
  "is_seed": true,
  "seed_rank": 1,
  "source": {
    "file": "var/default_miner_pattern.txt",
    "line_no": 1,
    "file_sha256": "<computed at ingest>"
  },
  "topology_signature": "<stable graph hash>",
  "extension_count": 0,
  "throughput_factor": 4,
  "resource_kind_stored": "shape",
  "layout_types": [
    "Layout_ShapeMiner",
    "Layout_ShapeMinerExtension",
    "SpaceBelt_Forward"
  ]
}
```

| `extension_count` | `throughput_factor` | Seed ranks (bootstrap file) |
|-------------------|---------------------|-----------------------------|
| 3 | 16 | 1–8 |
| 2 | 12 | 9–11 |
| 1 | 8 | 12–13 |
| 0 | 4 | 14 |

**Fluid / pipe:** not stored as separate rows. `resource_kind_stored` is always `shape` for bootstrap seeds. Fluid projection uses a fixed `layout_t` mapping table at L3.

### DB constraints (enforced by tests + ingest)

- Exactly 14 rows match `miner_seed_v1` + `is_seed`
- `topology_signature` unique across those 14 rows
- `gene_key` unique (existing partial unique constraint when set)

### Stale data

Ingest **deletes** (or deactivates, if soft-delete added later) rows where `metadata_json.generator == "exhaustive_sample_gene_v1"`. No coexistence with exhaustive catalog.

---

## §5 — Bootstrap file (`var/default_miner_pattern.txt`)

- **14 non-empty lines**, each a `SHAPEZ2-4-…` copy string
- All verified: `Layout_ShapeMiner` + `Layout_ShapeMinerExtension` (where present) + `SpaceBelt_Forward`
- Island-local coordinates; multiple lines use `X == 0`
- File remains in repo for re-ingest and audit; **never** read by solver after PR-Seed merge

---

## §6 — Ingest pipeline (PR-Seed)

### Command

`python manage.py seed_miner_patterns` (name TBD in implementation plan)

| Flag | Behaviour |
|------|-----------|
| `--file` | Default `var/default_miner_pattern.txt` |
| `--dry-run` | Validate only; no writes |
| `--replace-stale` | Remove exhaustive-generated samples |

### Steps

```text
read lines → assert count == 14
for each line:
  decode_copy_string → normalize → attach island meta
  compute topology_signature (island-local graph)
  assert unique among 14
  update_or_create(gene_key=miner_seed_XX, code=line, metadata_json=...)
delete stale exhaustive_sample_gene_v1 rows
```

### PR-Seed verification

- 14/14 decode success
- Extension count distribution matches §4 table
- Stored `code` equals source line bytes
- Architecture test: no production import of bootstrap file path
- `topology_signature` uniqueness test

### PR-Seed exclusions

- RTTP mass deletion
- Solver runtime wiring to `MinerSeedPattern` (PR-Legacy)

---

## §7 — `MinerSeedPattern` DTO (PR-Legacy)

Replaces **`GeneTemplate`** (hard delete). Module location: `django_apps/asteroid_lab/genetic_sample/miner_seed_pattern.py` (TBD in plan).

### Fields (minimum)

```text
seed_id: str                    # gene_key
topology_signature: str
extension_count: int
throughput_factor: int
occupied_island_cells: frozenset[(x, y, layout_t)]
output_transport_cell: (x, y)
extension_attachments: tuple[ExtensionAttachment, ...]  # island-local edges
source_code: str                # debug / provenance only — not algorithm input
```

### Builder

```text
miner_seed_pattern_from_genetic_sample(sample: GeneticSample) -> MinerSeedPattern
```

- **Must** parse `sample.decoded_json` / island entries
- **Must not** call `generate_exhaustive_sample_genes` or exhaustive cache

### Resource projection

```text
project_miner_layout(pattern: MinerSeedPattern, resource_kind: shape | fluid) -> BP.Entries
```

- Swap `Layout_ShapeMiner*` ↔ `Layout_FluidMiner*`, `SpaceBelt_Forward` ↔ `SpacePipe_Forward`
- Recompute extension `R` via existing `ports_compatible` / `equipment_bundles`

### Provenance wire (rename)

`runtime_gene_template_source.py` enums/types rename to `MinerSeedPatternSource*` (no `GeneTemplate` substring).

---

## §8 — Deletions (PR-Legacy)

| Artifact | Action |
|----------|--------|
| `genetic_sample/gene_template.py` | Delete |
| `genetic_sample/gene_template_loader.py` | Delete (JSON fixture loader) |
| `genetic_sample/exhaustive_generator.py` | Delete |
| `management/commands/seed_exhaustive_sample_genes.py` | Delete |
| Admin exhaustive seed UI | Replace with miner seed ingest |
| `genetic_sample_gene_export.py` exhaustive cache path | Rewrite to `MinerSeedPattern` from DB |
| `tests/fixtures/asteroid_lab/gene_templates/*.json` | Remove or reduce to non-SoT helpers |
| `asteroid_lab.models.PatternTemplate` / `PatternVariant` | Drop models + migration |
| `assert_blueprint_entries_raw_x_nonzero` on seed/solver paths | Remove |

---

## §9 — RTTP hard delete (PR-RTTP, separate)

**Principle:** No new `documents/archive/*rttp*` tree. Git history is the archive.

### In scope

```text
rttp_* modules (if any remain outside archive)
RTTP_* replay event types and timeline appenders
RTTP fields in solver_run_lab_summary / lab_replay_timeline_payload
RTTP UI in asteroid_miner_layout_lab.js / templates
.github/workflows/rttp-lab-macro-smoke.yml
docs/superpowers/specs/*rttp* and dependent plans/reports
RTTP tests and fixtures
catalog-rttp roadmap references
GeneTemplate / pattern_library / exhaustive_sample_gene string remnants
```

### Out of scope (do not delete)

```text
Layer 02 exterior transport / reconstruction complete map (non-RTTP)
MiningExtractionRule / game_data CANON tables
Copy JSON island-local research docs
```

### CI gate (after PR-RTTP)

```bash
rg -i "rttp|GeneTemplate|pattern_library|exhaustive_sample_gene"
```

| Match | Policy |
|-------|--------|
| `GeneTemplate` | **Fail** |
| `pattern_library` | **Fail** |
| `exhaustive_sample_gene` | **Fail** |
| `rttp` (case-insensitive) | **Fail** |
| `MinerSeedPattern` | **Allowed** (contains `Pattern` but is not `pattern_library`) |

No allowlist file: zero matches required in tracked code/config/workflows; spec/plan docs under `docs/superpowers/` cleaned in same PR.

---

## §10 — PR sequence

| PR | Depends on | Delivers |
|----|------------|----------|
| **PR-Seed** | — | 14 DB rows, ingest command, stale exhaustive purge, bootstrap read-ban tests |
| **PR-Legacy** | PR-Seed | `MinerSeedPattern`, export rewrite, exhaustive/GeneTemplate/PatternTemplate removal, `x==0` assert removal on solver paths |
| **PR-RTTP** | Independent of 1–2 (may merge after) | RTTP hard delete + `rg` gate |

---

## §11 — Testing contract

### PR-Seed

- `test_seed_miner_patterns_ingests_fourteen_unique_signatures`
- `test_genetic_sample_seed_count_exactly_fourteen`
- `test_runtime_does_not_read_bootstrap_miner_pattern_file` (architecture)
- `test_stale_exhaustive_samples_removed_on_replace`

### PR-Legacy

- `test_miner_seed_pattern_from_db_decoded_json` (no exhaustive import)
- `test_project_fluid_layout_types_from_shape_seed`
- `test_no_assert_raw_x_nonzero_on_seed_encode_path`
- Update integration tests that referenced `GeneTemplate` / fixture JSON SoT

### PR-RTTP

- `test_repo_has_no_rttp_gene_template_pattern_library_tokens` (architecture / rg wrapper)

---

## §12 — Approvals log

| Item | Status |
|------|--------|
| Approach A (14 rows + runtime projection) | Approved |
| DB canonical; file bootstrap only | Approved |
| `MinerSeedPattern` (S2) | Approved |
| §2 coordinate contract (revised: no solver-facing `x==0` ban) | Approved |
| PR-Seed → PR-Legacy → PR-RTTP | Approved |
| RTTP hard delete, no archive | Approved |

**Implementation plan:** [`../plans/2026-05-28-miner-seed-decontamination.md`](../plans/2026-05-28-miner-seed-decontamination.md) (includes blocking PR-Legacy **Task 8A**: remove `asteroid_map_coords` solver-facing `x==0` rejection)

---

## §13 — Self-review (2026-05-28)

| Check | Result |
|-------|--------|
| Placeholders | None; ingest command name marked TBD only in plan pointer |
| Internal consistency | L1 island-local preserved; L2–L4 dense coords allow `x==0`; forbids aligned with reviewer |
| Scope | Three PRs; RTTP separated |
| Ambiguity | `pattern` in `MinerSeedPattern` explicitly allowed vs `pattern_library` gate |
