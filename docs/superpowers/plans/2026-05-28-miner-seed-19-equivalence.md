# Miner Seed 19-Equivalence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the miner seed catalog from 14 orientation-sensitive rows to **19** `miner_seed_v2` equivalence classes with `equivalence_signature` dedupe, strict R validation, and a 19-line bootstrap SoT synced to the audit markdown.

**Architecture:** Extract 19 copy strings from audit md → `var/default_miner_pattern.txt` → `seed_miner_patterns` validates §5 rules, computes `equivalence_signature` (parent-tree + D₄) and audit `topology_signature` → narrow purge of stale `miner_seed_*` v1/v2 keys → tests lock md↔txt and uniqueness.

**Tech Stack:** Django 5.2, pytest, ruff, mypy (`django_apps config src`), PowerShell `scripts/test_fast.ps1`.

**Spec:** [`../specs/2026-05-28-miner-seed-19-equivalence-design.md`](../specs/2026-05-28-miner-seed-19-equivalence-design.md)

**Branch (recommended):** `feat/miner-seed-19-equivalence` from latest `master` or merged PR-Seed commit.

---

## File map

| File | Action |
|------|--------|
| `var/default_miner_pattern.txt` | Replace with **19** lines from audit md |
| `var/miner_seed_belt_ignored_canonical_parent_r_patterns.md` | No code import; referenced by sync test |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py` | `miner_seed_v2`, `EXPECTED_19_GENE_KEYS`, `gene_key_for_pattern_id` |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py` | **Create** — `equivalence_signature_from_decoded_root`, strict validation |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py` | Keep `topology_signature`; no uniqueness claims in docstrings |
| `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py` | 19 lines, v2 metadata, narrow purge |
| `django_apps/asteroid_lab/admin.py` | Admin copy: 19 seeds, purge checkbox text |
| `django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html` | Help text v2 / 19 |
| `django_apps/web/services/asteroid_lab_page_context.py` | Filter `miner_seed_v2` |
| `tests/integration/conftest.py` | `seed_miner_patterns` with v2 / 19 |
| `tests/unit/asteroid_lab/test_miner_seed_equivalence.py` | **Create** |
| `tests/unit/asteroid_lab/test_miner_seed_bootstrap_sync.py` | **Create** — md ↔ txt |
| `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py` | Update 14 → 19 |
| `tests/unit/asteroid_lab/test_genetic_sample_admin_seed.py` | Update counts |
| `docs/superpowers/specs/2026-05-28-miner-seed-decontamination-design.md` | Related link only |
| `documents/ai/current_plan.md` | CLOSED entry + link |

---

### Task 1: 19-line bootstrap artifact

**Files:**
- Modify: `var/default_miner_pattern.txt`
- Read: `var/miner_seed_belt_ignored_canonical_parent_r_patterns.md`

- [ ] **Step 1: Extract copy strings**

Run a one-off script or manual extract: 19 `SHAPEZ2-4-…$` strings in section order (`m0e_01` … `m3e_13`).

- [ ] **Step 2: Write `default_miner_pattern.txt`**

Exactly 19 non-empty lines; no BOM; each line ends with `$`.

- [ ] **Step 3: Verify decode**

```bash
python manage.py shell -c "from django.core.management import call_command; call_command('seed_miner_patterns', dry_run=True)"
```

Expected: passes line count (may fail later until Task 3 — OK for Task 1).

- [ ] **Step 4: Commit**

```bash
git add var/default_miner_pattern.txt
git commit -m "chore(asteroid_lab): add 19-line miner seed bootstrap SoT"
```

---

### Task 2: `equivalence_signature` helper + strict validation

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_equivalence.py`

- [ ] **Step 1: Write failing tests**

Cover:
- Two layouts related by D₄ share `equivalence_signature`
- Belt position change does not change signature
- Wrong extension `R` raises on `assert_miner_seed_layout_strict`
- `m0e_01` / `m3e_01` fixtures from bootstrap decode

- [ ] **Step 2: Run tests (red)**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_equivalence.py -v
```

- [ ] **Step 3: Implement**

- Build extension parent edges from island coords (ignore belt)
- D₄ canonicalize edge multiset; SHA-256 JSON
- `assert_miner_seed_layout_strict(decoded_root)` per spec §5

- [ ] **Step 4: Run tests (green) + ruff**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_equivalence.py -v
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(asteroid_lab): add miner seed equivalence signature and strict layout asserts"
```

---

### Task 3: Update `seed_miner_patterns` for v2 / 19 rows

**Files:**
- Modify: `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py`
- Modify: `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py`
- Modify: `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py`

- [ ] **Step 1: Update failing command tests**

Expect 19 rows, `miner_seed_v2`, keys `miner_seed_m0e_01` … `miner_seed_m3e_13`, unique `equivalence_signature`.

- [ ] **Step 2: Implement constants**

```python
MINER_SEED_SCHEMA_V2 = "miner_seed_v2"
EXPECTED_19_GENE_KEYS: tuple[str, ...]  # ordered
def gene_key_for_pattern_id(pattern_id: str) -> str: ...
```

- [ ] **Step 3: Wire ingest (no narrow purge logic here)**

- Line count 19
- Strict assert before save
- Store `pattern_id`, `equivalence_signature`, `topology_signature`
- Preserve existing purge **entrypoints/flags** (`--replace-stale`, `--purge-non-seed`) but do **not** implement the final narrow v1/v2 filter in this task — Task 4 owns that behaviour

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_seed_miner_patterns_command.py -v
```

- [ ] **Step 5: Commit**

---

### Task 4: Narrow stale purge guard

**Files:**
- Modify: `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py`
- Create: `tests/unit/asteroid_lab/test_seed_miner_patterns_purge.py`

- [ ] **Step 1: Failing purge test**

Seed `miner_seed_01` (v1), `miner_seed_m0e_01` (v2), `manual_legacy` (no prefix). Run ingest with purge. Assert only `miner_seed_01` removed; manual kept.

- [ ] **Step 2: Implement final narrow filter (spec §8)**

`gene_key` starts with `miner_seed_` AND `schema` in `{miner_seed_v1, miner_seed_v2}` AND `gene_key` not in `EXPECTED_19_GENE_KEYS`

- [ ] **Step 3: Green + commit**

---

### Task 5: md ↔ txt sync test

**Files:**
- Create: `tests/unit/asteroid_lab/test_miner_seed_bootstrap_sync.py`

- [ ] **Step 1: Implement extractor** (test helper: regex `Copy string:` blocks in audit md)

- [ ] **Step 2: Assert ordered equality with txt lines and `$` suffix**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_bootstrap_sync.py -v
```

- [ ] **Step 3: Commit**

---

### Task 6: Admin, integration, docs

**Files:**
- Modify: `django_apps/asteroid_lab/admin.py`, change_list template, `asteroid_lab_page_context.py`, `tests/integration/conftest.py`
- Modify: `docs/superpowers/specs/2026-05-28-miner-seed-decontamination-design.md` (link banner only)
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Admin queryset / copy for v2 and 19 rows**

- [ ] **Step 2: Integration conftest `seed_miner_patterns`**

- [ ] **Step 3: Parent spec banner + plan CLOSED note**

- [ ] **Step 4: Commit**

---

### Task 7: Verification gate

- [ ] **Step 1: Focused pytest**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_equivalence.py tests/unit/asteroid_lab/test_miner_seed_bootstrap_sync.py tests/unit/asteroid_lab/test_seed_miner_patterns_command.py tests/unit/asteroid_lab/test_seed_miner_patterns_purge.py tests/unit/asteroid_lab/test_genetic_sample_admin_seed.py -v
```

- [ ] **Step 2: Ruff / mypy (scoped)**

```bash
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
python -m mypy django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py
```

- [ ] **Step 3: Note PR / full gate for merge** (`scripts/test_full.ps1` when opening PR)

---

## Risks

- Bootstrap paste may fail strict R until audit strings are regenerated with `R=0` miner + `ports_compatible` extensions — fix **source md/txt**, not ingest auto-patch.
- Purge mis-filter if `gene_key` prefix widened — keep test from Task 4.

## Out of scope (this plan)

- `--normalize-r` / `--rewrite-bootstrap`
- Solver using all 19 seeds in S2b-1 production path
- Deleting `topology_signature` or `exhaustive_generator.py` (PR-Legacy)
