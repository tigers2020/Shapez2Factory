# Miner Seed 19-Equivalence Catalog — Design Spec

**Status:** Approved (catalog architect review 2026-05-28)  
**Date:** 2026-05-28  
**Track:** Asteroid Lab `GeneticSample` miner seed authority (follow-up to PR-Seed)  
**Supersedes (catalog row count / dedupe only):** §4 row-count and uniqueness rules in [`2026-05-28-miner-seed-decontamination-design.md`](2026-05-28-miner-seed-decontamination-design.md) — **14 → 19** canonical seeds with D₄ equivalence.  
**Does not supersede:** coordinate frame §2, `MinerSeedPattern` / PR-Legacy, RTTP deletion, or island-local `X==0` contract in the parent spec.

**Related:**

- Design / audit artifact (not runtime SoT): [`var/miner_seed_belt_ignored_canonical_parent_r_patterns.md`](../../../var/miner_seed_belt_ignored_canonical_parent_r_patterns.md)
- Ingest bootstrap SoT: [`var/default_miner_pattern.txt`](../../../var/default_miner_pattern.txt) — **19** non-empty `SHAPEZ2-4-…$` lines
- Parent decontamination spec: [`2026-05-28-miner-seed-decontamination-design.md`](2026-05-28-miner-seed-decontamination-design.md)
- Implementation plan: [`../plans/2026-05-28-miner-seed-19-equivalence.md`](../plans/2026-05-28-miner-seed-19-equivalence.md)
- Copy JSON island-local: [`documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md`](../../../documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md)

---

## §1 — Problem and goals

### Problem

PR-Seed established **14** `miner_seed_v1` rows using `topology_signature` (island-local cells + roles + **raw `R`**). That signature:

- Treats **rotation/reflection** of the same extension tree as different catalog entries.
- **Includes** belt cells and miner `R`, which are not part of the intended catalog identity.
- Does not match the **19** belt-ignored, parent-tree equivalence classes documented in `var/miner_seed_belt_ignored_canonical_parent_r_patterns.md`.

### Goals

| Goal | Contract |
|------|----------|
| Canonical store | Exactly **19** active miner seed rows (`schema == miner_seed_v2`, `is_seed == true`) |
| Equivalence | D₄ quotient on extension **parent tree** (belt + miner `R` excluded from signature) |
| Bootstrap | `var/default_miner_pattern.txt` = **19-line** ingest evidence; runtime must not read it (unchanged boundary) |
| Audit | Keep `topology_signature` for paste fidelity; **do not** use it for catalog uniqueness |
| Ingest safety | **Strict** layout/R validation by default; **no** auto-correction in this track |
| Purge | Remove only stale **`miner_seed_*`** rows with `miner_seed_v1` / `miner_seed_v2` schema outside the expected 19 keys |

### Non-goals

- Auto-fixing bootstrap paste (`--normalize-r`, `--rewrite-bootstrap`) — deferred; flags may be added later
- Fluid-specific DB rows (shape-only seeds; L3 projection unchanged)
- Replacing S2b production solver enumeration policy (19 = full catalog; solver may still defer subsets)
- Changing `topology_signature` algorithm (audit-only retention)

---

## §2 — Catalog composition (19 rows)

Stable IDs and counts match the audit markdown.

| Bucket | `gene_key` pattern | Count |
|--------|-------------------|------:|
| M + 0E | `miner_seed_m0e_01` | 1 |
| M + 1E | `miner_seed_m1e_01` | 1 |
| M + 2E | `miner_seed_m2e_01` … `m2e_04` | 4 |
| M + 3E | `miner_seed_m3e_01` … `m3e_13` | 13 |
| **Total** | | **19** |

**Ordered ingest rank (`seed_rank` 1..19):**  
`m0e_01`, `m1e_01`, `m2e_01`, `m2e_02`, `m2e_03`, `m2e_04`, `m3e_01` … `m3e_13` (same order as audit doc sections).

| `extension_count` | `throughput_factor` | Keys |
|-------------------|---------------------|------|
| 0 | 4 | `m0e_01` |
| 1 | 8 | `m1e_01` |
| 2 | 12 | `m2e_01`–`m2e_04` |
| 3 | 16 | `m3e_01`–`m3e_13` |

---

## §3 — Equivalence contract (`equivalence_signature`)

### Included in signature input

- `extension_count` (0..3)
- **Extension parent tree** relative to the miner, as a multiset of **directed** parent edges in island-local coordinates:
  - Each edge: `(child_coord, parent_coord)` where both are `(x, y)` island-local integers from `entry_island_raw_coord`
  - Direction is semantic: **child → parent** (extension or miner); never belt
  - D₄ canonicalization removes orientation-space duplicates; it does **not** drop parent direction
  - Tree must be connected to the miner over extension cells only

### Excluded from signature (belt / miner orientation)

- All `SpaceBelt_*` / `SpacePipe_*` cells (coordinates, path, **`R`**)
- **Miner `R`**
- Output-axis placement differences that differ only by belt routing (belt is not in the graph)
- Raw extension `R` values as signature key material (see validation below)

### Symmetry

Apply **D₄** (four rotations + reflection) to the set of edge vectors: for each edge `(child, parent)`, transform both endpoints; re-normalize by translating so **miner** is at `(0, 0)`; sort edges lexicographically; take the **minimum** representation across all D₄ transforms; hash canonical JSON.

### Extension `R` — validation only, not signature key

Do **not** hash raw `E.R` into `equivalence_signature`.

At ingest, **assert** each extension’s quarter `R` matches the **parent-facing** expectation derived from grid geometry:

```text
expected_R = rotation_quarter such that extension output faces parent
             (use existing ports_compatible / direction_from_a_to_b policy)
```

Signature identity uses **geometry of parent links** `(child_coord, parent_coord)` only; `R` is a **strict assert** that the paste is physically consistent with that tree.

---

## §4 — Signature field separation

| Field | Role | Uniqueness |
|-------|------|------------|
| `topology_signature` | Decoded paste fidelity / audit / regression | **Not** required unique across catalog |
| `equivalence_signature` | Catalog dedupe, ingest guards | **Required unique** among 19 v2 seeds |
| `gene_key` | Solver-facing stable ID (`miner_seed_m3e_07`, etc.) | **Required unique** (DB partial unique when set) |

---

## §5 — Strict ingest validation (default)

Ingest and `GeneticSample.clean()` for v2 seeds **must fail** (no silent rewrite) when any check below fails.

| Rule | Requirement |
|------|-------------|
| Miner rotation | `Layout_*Miner` has `R == 0` (East) |
| Output belt | Exactly **one** `SpaceBelt_Forward` (shape seeds) |
| Belt placement | Belt is on miner **forward** island cell (miner R-facing neighbor) |
| Extension rotation | Each extension `R` equals parent-facing `expected_R` |
| Acyclicity | Extension parent graph has **no** cycles |
| Belt isolation | **No** extension parent is a belt cell |
| Output axis | **No** extension occupies the miner forward / output-axis cell |

**Forbidden in this PR:** `--normalize-r`, auto-rewrite of `BP.Entries`, or silent `R` patching. Optional future flags must be explicit and off by default.

---

## §6 — Bootstrap and audit artifacts

| Artifact | Role |
|----------|------|
| `var/miner_seed_belt_ignored_canonical_parent_r_patterns.md` | Human audit: ASCII, JSON entries, copy strings, IDs |
| `var/default_miner_pattern.txt` | **Ingest SoT:** 19 lines, byte-identical to audit copy strings in section order |

**Sync contract (test-enforced):**

1. Extract 19 copy strings from the audit markdown (`Copy string:` fenced blocks, in section order).
2. Read 19 non-empty lines from `default_miner_pattern.txt`.
3. Assert lists are equal.
4. Assert every line ends with `$`.

Runtime code (solver, web, ingest after load) must **not** read the audit markdown file. Only `seed_miner_patterns` may read `default_miner_pattern.txt` (existing architecture boundary).

---

## §7 — `GeneticSample` metadata (`miner_seed_v2`)

```json
{
  "schema": "miner_seed_v2",
  "is_seed": true,
  "seed_rank": 7,
  "pattern_id": "m3e_01",
  "source": {
    "file": "var/default_miner_pattern.txt",
    "line_no": 7,
    "file_sha256": "<computed at ingest>"
  },
  "equivalence_signature": "<sha256 hex>",
  "topology_signature": "<existing audit hash>",
  "extension_count": 3,
  "throughput_factor": 16,
  "resource_kind_stored": "shape",
  "layout_types": [
    "Layout_ShapeMiner",
    "Layout_ShapeMinerExtension",
    "SpaceBelt_Forward"
  ]
}
```

### DB constraints (tests + ingest)

- Exactly **19** rows with `miner_seed_v2` + `is_seed`
- `equivalence_signature` unique among those 19
- `gene_key` equals expected 19-key set (see §2)
- `code` byte-identical to bootstrap line for that rank

---

## §8 — `seed_miner_patterns` command

### Behaviour changes

| Flag / behaviour | Contract |
|------------------|----------|
| Line count | `assert len(lines) == 19` |
| `gene_key` | `update_or_create` by `miner_seed_{pattern_id}` (e.g. `miner_seed_m3e_01`) |
| Validation | Run §5 strict checks before write |
| Signatures | Compute and store both `equivalence_signature` and `topology_signature` |
| `--replace-stale` | Retain: delete `metadata_json.generator == exhaustive_sample_gene_v1` |
| Purge (narrow) | Delete rows where **`gene_key` starts with `miner_seed_`** AND `metadata_json.schema` in `{"miner_seed_v1","miner_seed_v2"}` AND `gene_key` **not** in `EXPECTED_19_GENE_KEYS` |

**Purge must not** delete:

- Manual samples without `miner_seed_` prefix
- Unrelated `GeneticSample` rows
- Non-seed experiments unless they match the narrow rule above

### PR placement

Recommended: **follow-up PR** on top of merged PR-Seed (`feat/miner-seed-19-equivalence` or continuation branch). Updates bootstrap file, constants, ingest, tests, admin copy (19 seeds).

---

## §9 — Tests (minimum)

| Test | Asserts |
|------|---------|
| `test_bootstrap_md_txt_sync` | 19 strings from md == 19 lines from txt; `$` suffix |
| `test_equivalence_signature_*` | Known pair: D₄-related layouts share signature; belt-only diff ignored |
| `test_strict_r_validation_*` | Wrong miner R / belt count / extension-on-axis → ingest error |
| `test_seed_miner_patterns_ingests_nineteen` | 19 rows, unique `equivalence_signature`, expected keys |
| `test_purge_narrow` | Purge removes `miner_seed_01` v1 but not `manual_sample` |

---

## §10 — Approvals log

| Item | Status |
|------|--------|
| Approach A (19-line txt SoT, md = audit) | Approved |
| `equivalence_signature` (belt + miner R excluded; parent-tree + D₄) | Approved |
| `topology_signature` audit-only | Approved |
| Strict R validation; no auto-correction | Approved |
| Narrow purge scope | Approved |
| New spec (this document) + parent spec link only | Approved |

---

## §11 — Self-review

| Check | Result |
|-------|--------|
| Placeholders | None; pattern IDs fixed to audit doc |
| Internal consistency | Signature excludes belt/miner R; validation uses derived R; purge scoped |
| Scope | Catalog + ingest + tests; no solver algorithm change |
| Ambiguity | `equivalence_signature` uses edge coords, not raw `E.R`; `topology_signature` not dropped |
