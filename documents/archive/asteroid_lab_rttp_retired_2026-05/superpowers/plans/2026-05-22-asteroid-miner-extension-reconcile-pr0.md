# Asteroid Miner / Extension Reconciliation — PR-0 (Audit Docs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PR-0 audit-only documentation under `documents/Algorithm/asteroid_lab_mining_installation/` (`00`–`02`) plus one `documents/Algorithm/README.md` index row — no code, migrations, or CANON promotion without evidence.

**Architecture:** D2 reconcile-first: Source of Truth stack (layers A–E), 9-column reconciliation seed table, drift matrix for legacy docs. PR-1 fills `03_db_cross_reference.md`; PR-2 writes `04_installation_guide.md` (out of scope here).

**Tech Stack:** Markdown (K/E), `rg` verification, design spec [`docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md`](../specs/2026-05-22-asteroid-miner-extension-reconcile-design.md)

**Follow-on plans (not this file):** PR-1 → `03_db_cross_reference.md`; PR-2 → `04_installation_guide.md`

**Plan revision (2026-05-22, PR-0 review):** evidence `rg` preflight; replay doc existence check; `git diff` base fix; spec approval in **same PR** before Task 5 verification (not post-merge).

---

## Pre-flight A (spec grep — green)

Run before Task 1 (record output in PR description):

```powershell
rg "needs-review = 0|02_db_cross_reference_inventory|db_evidence \| code_evidence" docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
```

**Expected (2026-05-22):**

- `needs-review = 0` — only under “Does not require” (PR-0) and “Optional program goal” (PR-2), **not** PR-0 success
- `02_db_cross_reference_inventory` — only in “do not use” warning
- `db_evidence | code_evidence` — **no matches** (9-column schema)

---

## Pre-flight B (code evidence paths — run before Task 2)

Legacy Algorithm docs may still cite `django_apps/shapez_asteroid/optimization/`. That app is **removed** from the repo. PR-0 evidence must use paths from this `rg` output only.

```powershell
rg "VALID_THROUGHPUT_FACTORS|throughput_factor_for_extension_count|ExtractorPlacementPolicy|ReplayEventType" django_apps tests
```

**Recorded baseline (2026-05-22) — use these in seed rows:**

| symbol | canonical path |
|--------|----------------|
| `VALID_THROUGHPUT_FACTORS`, `throughput_factor_for_extension_count` | `django_apps/asteroid_lab/optimization/gene_template.py` |
| `ExtractorPlacementPolicy`, `RIM_ONLY` | `django_apps/asteroid_lab/optimization/candidate_dtos.py` |
| `RIM_ONLY` default in generator | `django_apps/asteroid_lab/optimization/candidate_generator.py` (lines ~225, ~437) |
| `ReplayEventType` | `django_apps/asteroid_lab/replay/replay_enums.py` |

**Tests (exist under `tests/unit/asteroid_lab/` — do not use `tests/unit/shapez_asteroid/`):**

| topic | pytest anchor |
|-------|----------------|
| throughput / extension count | `test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` |
| extension 0..3 exhaust | `test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` |
| candidate ≠ commit | `test_candidate_generator.py::test_candidate_generator_does_not_commit_placements` |
| normal pool + probe | `test_candidate_generator.py::test_candidate_generator_reachable_only_enters_normal_pool` |
| commit reprobe | `test_incremental_commit.py::test_incremental_commit_reprobes_latest_domain` |
| replay input ban | `test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` |
| replay wire values | `test_replay_timeline_dto.py` (`ReplayEventType` enum parity) |

If preflight B paths differ after rebase, **update Task 2 seed table before writing `01`**.

---

## Pre-flight C (replay doc files — run before Task 3)

```powershell
@(
  "documents/Algorithm/asteroid_lab_09_replay_timeline.md",
  "documents/Algorithm/asteroid_lab_09_replay_debug.md",
  "documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md"
) | ForEach-Object { if (Test-Path $_) { "EXISTS: $_" } else { "MISSING: $_" } }
```

**Baseline (2026-05-22):** all three **EXIST**.

| file | drift matrix role |
|------|-------------------|
| `asteroid_lab_09_replay_timeline.md` | **ACTIVE** — product replay contract (link from `01` replay rows) |
| `asteroid_lab_09_replay_debug.md` | **ARCHIVED** — historical dual-track; do not treat as CANON |
| `asteroid_lab_12_runtime_replay_wiring.md` | **RESEARCH** — runtime output-only / UI read path; PR-2 §6 support |

---

## File map (PR-0 only)

| File | Action |
|------|--------|
| `documents/Algorithm/asteroid_lab_mining_installation/00_source_of_truth.md` | Create |
| `documents/Algorithm/asteroid_lab_mining_installation/01_rule_reconciliation.md` | Create |
| `documents/Algorithm/asteroid_lab_mining_installation/02_doc_drift_matrix.md` | Create |
| `documents/Algorithm/README.md` | Modify — one table row + optional read-order bullet |
| `docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md` | Modify — `Status: Approved` in **same PR**, before Task 5 verification (Task 5 Step 0) |

**Forbidden in PR-0:** `django_apps/**`, `tests/**`, `game_data` migrations, `03_db_cross_reference.md`, `04_installation_guide.md`, `scripts/*`

---

### Task 1: Create directory and `00_source_of_truth.md`

**Files:**
- Create: `documents/Algorithm/asteroid_lab_mining_installation/00_source_of_truth.md`

- [ ] **Step 1: Create the directory**

```powershell
New-Item -ItemType Directory -Force -Path "documents/Algorithm/asteroid_lab_mining_installation"
```

- [ ] **Step 2: Write `00_source_of_truth.md` (full body)**

Create the file with this exact content (adjust `last_reviewed` if implementing on a later date):

```markdown
---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: K/E
supersedes: []
related_docs:
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - docs/domain/asteroid_game_data_snapshot.md
---

# Asteroid Lab — Source of Truth (miner / extension / installation)

This folder holds audit outputs from the canonical realignment program for **miner · extension · installation flow**. PR-0 provides only the contradiction table and drift matrix. The narrative guide is written in `04_installation_guide.md` (PR-2).

## Priority stack

| priority | source | role |
|:--:|---|---|
| 1 | Latest `game_data` import DB + dump audit | Distributed **facts** (not one miner table) |
| 2 | `django_apps/asteroid_lab/**` + passing pytest | Lab **runtime behavior** |
| 3 | `ACTIVE` / `CANON` (`game_rules`, `solver_runtime/*`, `asteroid_lab_09`, …) | Design **contracts** |
| 4 | `documents/Algorithm/asteroid_lab_0*` (`RESEARCH`) | History / background |
| 5 | replay / NDJSON / artifact | **Observation only** — never algorithm input |

## Conflict rules

```text
RESEARCH/REPORT vs code + tests → update/delete the document row in 02_doc_drift_matrix, not code.
Promote to CANON → requires normalized_db and/or code_invariant and/or test_evidence (see 01).
Replay/metrics never override code invariants (Layer C/D).
```

## Distributed DB fact (normative)

```text
The current game_data dump does not expose miner/extension/throughput as a single dedicated normalized table.
Evidence is distributed across building geometry tables, toolbar placement records, simulation/reflection rows, and Lab code invariants.
```

```text
Current game_data dump does not provide miner/extension/throughput in a single dedicated normalized table.
Evidence is scattered across building geometry, toolbar placement, simulation/reflection rows, and Lab code invariants.
```

## Evidence layers (A–E)

| layer | column label | examples | trust |
|-------|----------------|----------|-------|
| A | `normalized_db_evidence` | `buildingvariant`, `buildinggroup`, `buildingfootprinttile`, `buildingconnector`, transport registry tables, `toolbar*` | high for geometry/registry |
| B | `reflected_db_evidence` | `simulationsystem`, `unknownproperty`, `clrtyperegistryentry`, `simulation_systems` JSON paths | medium |
| C | `code_invariant` | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS`, `throughput_factor_for_extension_count()`, `ExtractorPlacementPolicy.RIM_ONLY` | high for Lab rules |
| D | `test_evidence` | pytest paths, `ReplayEventType` wire values | high for behavior lock |
| E | `manual_gameplay_evidence` | player-facing rules when A–D insufficient | low — explicit only |

**Throughput:** Dedicated rate table absence is **not** a verdict. Route through B + C + [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) + D. Never close a row with "not in DB → BLOCKED".

## Naming guard

`BuildingSnapshot` / `TransportRegistryEntry` are **consumer DTOs** (`AsteroidGameDataSnapshot`), not Django ORM model names. Use dump/ORM table names in Layer A; cite DTOs under Layer C or adapter notes only.

## PR map (this program)

| file | PR |
|------|-----|
| `00_source_of_truth.md` | PR-0 |
| `01_rule_reconciliation.md` | PR-0 |
| `02_doc_drift_matrix.md` | PR-0 |
| `03_db_cross_reference.md` | PR-1 |
| `04_installation_guide.md` | PR-2 |

## PR-0 success (this PR only)

- Every `needs-review` row in `01` has **owner**, **evidence gap**, and **next PR target**
- No row promoted to `keep` as CANON surrogate without C and/or D evidence (throughput may stay `needs-review`)
- **Does not** require `needs-review = 0`
```

- [ ] **Step 3: Verify file exists**

```powershell
Test-Path "documents/Algorithm/asteroid_lab_mining_installation/00_source_of_truth.md"
```

Expected: `True`

- [ ] **Step 4: Commit**

```bash
git add documents/Algorithm/asteroid_lab_mining_installation/00_source_of_truth.md
git commit -m "docs(asteroid-lab): add mining installation SoT stack (PR-0)"
```

---

### Task 2: `01_rule_reconciliation.md` (9-column seed table)

**Files:**
- Create: `documents/Algorithm/asteroid_lab_mining_installation/01_rule_reconciliation.md`

**Evidence sources:** Pre-flight B table only. Skim (~10 min):

- `django_apps/asteroid_lab/optimization/gene_template.py`
- `django_apps/asteroid_lab/optimization/candidate_dtos.py` — `ExtractorPlacementPolicy.RIM_ONLY`
- `django_apps/asteroid_lab/optimization/candidate_generator.py` — default `RIM_ONLY`
- `documents/Algorithm/asteroid_lab_07_incremental_commit.md`
- `django_apps/asteroid_lab/replay/replay_enums.py`

**Do not cite** `django_apps/shapez_asteroid/` (removed).

- [ ] **Step 1: Write `01_rule_reconciliation.md` (full body)**

```markdown
---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: K/E
related_docs:
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
---

# Rule reconciliation — miner / extension / installation

9-column table. **PR-0:** seed rows + explicit evidence gaps. **PR-1:** fill Layer A/B cells in `03_db_cross_reference.md` and update rows here.

## Column definitions

| column | meaning |
|--------|---------|
| `topic` | Rule name |
| `legacy_claim` | Old doc claim |
| `normalized_db_evidence` | Layer A — ORM/dump table names |
| `reflected_db_evidence` | Layer B — simulation/reflection paths |
| `code_invariant` | Layer C — symbols |
| `test_evidence` | Layer D — pytest / enums |
| `confidence` | `high` / `medium` / `low` |
| `verdict` | `keep` / `rewrite` / `clarify` / `delete` / `needs-review` |
| `action` | Target file / PR; include **owner** and **evidence gap** when `needs-review` |

## Seed rows (PR-0)

| topic | legacy_claim | normalized_db_evidence | reflected_db_evidence | code_invariant | test_evidence | confidence | verdict | action |
|-------|--------------|------------------------|----------------------|----------------|---------------|------------|---------|--------|
| extension max 0..3 | `asteroid_lab_02`: linear 0–3 extensions | *PR-1:* variant rows for `Layout_ShapeMiner` / `Layout_FluidMiner` / `*Extension` in `buildingvariant` + footprint tiles | *PR-1:* attach paths under `simulation_systems` if present | `throughput_factor_for_extension_count()` rejects >3; `GeneTemplate` occupied = extractor + extensions | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count`; `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` | high (C+D) | keep | PR-1: add A rows in `03`; owner: asteroid-lab |
| throughput 4/8/12/16 | `game_rules` CANON: ×4 base, +×4 per extension, max ×16 | *gap PR-1* — no single rate table; sample `buildingvariant` + rate configs if imported | *gap PR-1* — `simulationsystem` / `unknownproperty` paths for miner pump rates | `VALID_THROUGHPUT_FACTORS = {4,8,12,16}`; `throughput_factor_for_extension_count()` | `test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` | medium | needs-review | **owner:** asteroid-lab · **gap:** Layer B sample from dump · **next:** PR-1 `03_db_cross_reference.md` + reconcile row |
| rim-only placement | `asteroid_lab_03`: `RIM_ONLY` / “rim-only” reads like install order | *PR-1:* rim is topology-derived, not a DB table | — | `ExtractorPlacementPolicy.RIM_ONLY` in `candidate_dtos.py`; `candidate_generator.py` default — **anchor coord ∈ rim_cells**, not greedy install | `test_candidate_generator.py::test_candidate_generator_does_not_commit_placements`; `::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | rewrite | **owner:** asteroid-lab · **gap:** wording in `asteroid_lab_03` · **next:** PR-2 `04` §3 + optional phrase patch PR |
| candidate route probe | Phase 3 / overview: probe before pool | — | — | `BundleCandidate.route_probe_result` at generation; **not** commit proof | `test_candidate_generator.py::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | clarify | PR-2 `04` §3–5 callout; link `asteroid_lab_04_route_probe.md` |
| commit-time reprobe | `asteroid_lab_07`: reprobe on latest `route_domain` | — | — | `RouteDomainSnapshotBuilder.build_snapshot` each commit step; candidate probe is reference only | `tests/unit/asteroid_lab/test_incremental_commit.py::test_incremental_commit_reprobes_latest_domain` | high | keep | strong-canon; PR-2 `04` §5; keep `asteroid_lab_07` |
| replay event vocabulary | UI / lab JS — no doc mapping | — | — | `ReplayEventType` in `replay_enums.py`: `candidate.generated`, `route_probe.succeeded`, `route.committed`, … | `test_replay_timeline_dto.py` (enum wire values); `test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` (input ban only) | medium | needs-review | **owner:** asteroid-lab · **gap:** event ↔ UI scrub labels · **next:** PR-2 `04` §6 + `asteroid_lab_12` |
| replay not algorithm input | `asteroid_lab_00` / invariants | — | — | metrics/NDJSON/replay frames excluded from optimization input | `test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` | high | keep | Link `asteroid_lab_09_replay_timeline.md` (ACTIVE); `asteroid_lab_12_runtime_replay_wiring.md` (output path); **not** `09_replay_debug` (ARCHIVED) |

## PR-0 closure checklist

- [ ] All `needs-review` rows list owner + evidence gap + next PR
- [ ] No row uses "not in DB" as final `verdict`
- [ ] `03_db_cross_reference.md` not created in PR-0 (reserved PR-1)
```

- [ ] **Step 2: Verify row count and forbidden verdict language**

```powershell
rg "not in DB|BLOCKED" documents/Algorithm/asteroid_lab_mining_installation/01_rule_reconciliation.md
rg "needs-review" documents/Algorithm/asteroid_lab_mining_installation/01_rule_reconciliation.md
```

Expected: no `not in DB` / `BLOCKED` as verdict; at least 2 `needs-review` rows with owner in `action` column

- [ ] **Step 3: Commit**

```bash
git add documents/Algorithm/asteroid_lab_mining_installation/01_rule_reconciliation.md
git commit -m "docs(asteroid-lab): add miner/extension reconciliation seed table (PR-0)"
```

---

### Task 3: `02_doc_drift_matrix.md`

**Files:**
- Create: `documents/Algorithm/asteroid_lab_mining_installation/02_doc_drift_matrix.md`

- [ ] **Step 1: Write `02_doc_drift_matrix.md` (full body)**

```markdown
---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: K/E
related_docs:
  - asteroid_lab_mining_installation/01_rule_reconciliation.md
---

# Document drift matrix — miner / extension program

Tracks legacy docs against D2 SoT. **Do not** mass-edit `asteroid_lab_0*` in PR-0.

## `drift_type` enum (fixed)

`stale-canon-risk` · `wording-risk` · `ok-but-db-check-needed` · `missing-doc` · `strong-canon`

## Matrix

| document | status | claim_summary | drift_type | action | owner |
|----------|--------|---------------|------------|--------|-------|
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) | CANON | throughput ×4..×16 absolute rates | stale-canon-risk | PR-1: Layer B sample + reconcile throughput row | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) | RESEARCH | linear 0–3 extension; `ExtensionAttachment` | ok-but-db-check-needed | PR-1 footprint cross-check in `03` | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) | RESEARCH | rim-only; no greedy install | wording-risk | PR-2 link from `04` §3; optional phrase patch | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md) | RESEARCH | commit-time reprobe; `Gene.commit_order` | strong-canon | keep; PR-2 `04` §5 links here | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) | RESEARCH | placement ≠ commit; replay input ban | strong-canon | keep; cite in `04` | asteroid-lab |
| [`documents/plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`](../../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md) | REPORT | progress summary only | ok-but-db-check-needed | do not treat as contract; link from `00` | asteroid-lab |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | — | replay scrub, solver run feedback | missing-doc | PR-2 `04` §6 + `ReplayEventType` table | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md) | ACTIVE | unified lab replay timeline | strong-canon | keep; PR-2 §6 wire values | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_debug.md`](../asteroid_lab_09_replay_debug.md) | ARCHIVED | dual-track history | ok-but-db-check-needed | do not cite as CANON; link only for archaeology | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) | RESEARCH | runtime replay wiring; output-only | strong-canon | PR-2 §6 UI read path; complements `09` | asteroid-lab |

## When to update this matrix

- After PR-1: set `action` done for rows touched by `03_db_cross_reference.md`
- After PR-2: close `missing-doc` / `wording-risk` where `04` landed
```

- [ ] **Step 2: Verify relative links + replay docs (Pre-flight C)**

```powershell
@(
  "documents/game_rules/shapez2_asteroid_space_transport_throughput.md",
  "documents/Algorithm/asteroid_lab_03_candidate_generator.md",
  "documents/Algorithm/asteroid_lab_09_replay_timeline.md",
  "documents/Algorithm/asteroid_lab_09_replay_debug.md",
  "documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md",
  "django_apps/web/static/web/js/asteroid_miner_layout_lab.js"
) | ForEach-Object { if (-not (Test-Path $_)) { throw "missing: $_" } }
```

Expected: no throw. If `09_replay_timeline.md` is missing, drop that row from matrix and set `01` replay link to `12` only (record in PR description).

- [ ] **Step 3: Commit**

```bash
git add documents/Algorithm/asteroid_lab_mining_installation/02_doc_drift_matrix.md
git commit -m "docs(asteroid-lab): add miner/extension doc drift matrix (PR-0)"
```

---

### Task 4: Index — `documents/Algorithm/README.md`

**Files:**
- Modify: `documents/Algorithm/README.md` (after line 27 in "read order", and file list table)

- [ ] **Step 1: Add read-order bullet after item 5 (Solver button)**

Insert after line containing `5. **Solver button:**`:

```markdown
6. **Miner / extension (reconcile):** [`asteroid_lab_mining_installation/00_source_of_truth.md`](asteroid_lab_mining_installation/00_source_of_truth.md) → `01` → `02` (PR-0 audit); `03`–`04` follow PR-1/PR-2
```

- [ ] **Step 2: Add file-list table row before `## Draft`**

```markdown
| [`asteroid_lab_mining_installation/`](asteroid_lab_mining_installation/) | `AUDIT` | Miner/extension SoT, reconciliation, drift (D2 program) |
```

- [ ] **Step 3: Verify README mentions folder once**

```powershell
rg "asteroid_lab_mining_installation" documents/Algorithm/README.md
```

Expected: at least 2 matches (read order + table)

- [ ] **Step 4: Commit**

```bash
git add documents/Algorithm/README.md
git commit -m "docs(algorithm): index asteroid_lab_mining_installation audit folder"
```

---

### Task 5: PR-0 verification gate (no pytest)

- [ ] **Step 0: Mark design spec approved (same PR, before diff check)**

Update `docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md` line 4:

```markdown
**Status:** Approved — PR-0 plan: [`2026-05-22-asteroid-miner-extension-reconcile-pr0.md`](../plans/2026-05-22-asteroid-miner-extension-reconcile-pr0.md)
```

```bash
git add docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
git commit -m "docs(spec): approve asteroid miner extension reconcile design"
```

- [ ] **Step 1: Confirm PR-0 file set only**

```powershell
Get-ChildItem documents/Algorithm/asteroid_lab_mining_installation
```

Expected: exactly `00_source_of_truth.md`, `01_rule_reconciliation.md`, `02_doc_drift_matrix.md` (no `03` or `04`)

- [ ] **Step 2: PR-0 success grep**

```powershell
rg "needs-review = 0" documents/Algorithm/asteroid_lab_mining_installation/
rg "02_db_cross_reference_inventory" documents/Algorithm/asteroid_lab_mining_installation/
rg "db_evidence \| code_evidence" documents/Algorithm/asteroid_lab_mining_installation/
```

Expected: no matches

- [ ] **Step 3: Every needs-review row has owner (manual)**

Open `01_rule_reconciliation.md` and confirm rows with `needs-review` in `verdict` column include `owner:` in `action` (throughput, replay UI).

- [ ] **Step 4: Confirm PR-0 diff scope (no `HEAD~N` — commit count varies)**

From repo root, after all Task 1–4 commits (and Task 5 Step 0):

```powershell
$base = git merge-base HEAD origin/master 2>$null
if (-not $base) { $base = git merge-base HEAD master 2>$null }
if (-not $base) { $base = git rev-parse HEAD~5 }
git diff --name-only "$base..HEAD"
```

Expected: only paths under `documents/` and `docs/superpowers/specs/`. No `django_apps/`, `tests/`, `config/`.

Alternative (explicit branch base):

```bash
git diff --name-only master..HEAD
```

---

## Plan self-review

| Spec section | Task |
|--------------|------|
| SoT stack + distributed DB wording | Task 1 |
| Layers A–E | Task 1 + column defs in Task 2 |
| 9-column reconciliation | Task 2 |
| PR-0 success (no needs-review=0) | Task 1 footer + Task 5 |
| Drift matrix seeds | Task 3 |
| README link | Task 4 |
| Forbidden PR-0 files | Task 5 Step 1 |
| PR-1/PR-2 | Named as follow-on only |

**Placeholder scan:** None — all markdown bodies are copy-paste ready.

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-22-asteroid-miner-extension-reconcile-pr0.md`](2026-05-22-asteroid-miner-extension-reconcile-pr0.md).

**Recommended: Subagent-Driven** (one worker per task; review between tasks)

| Task | Worker focus |
|------|----------------|
| Task 1 | SoT / documentation |
| Task 2 | Reconciliation / evidence (`rg` preflight B mandatory) |
| Task 3 | Drift matrix / links (`rg` preflight C mandatory) |
| Task 4–5 | Index + verification (spec approve Step 0, then merge-base diff) |

**Alternative:** Inline execution with executing-plans checkpoints.

After PR-0 merges, separate plans for PR-1 (`03_db_cross_reference.md`) and PR-2 (`04_installation_guide.md`).
