# Exhaustive sample gene DB seed (approval summary)

## Purpose

Exhaustively generate combinations of **one miner + one R-direction transport cell + N/W/S extensions only (max 3, tree)** by rule, build copy strings via `encode_copy_string`, then idempotently persist to `GeneticSample` by **`gene_key`**. Existing 16 manual samples etc. are **reference for layout/tiles only**, not inputs.

## Pipeline

```text
rules → canonical topology → layout JSON → encode_copy_string → GeneticSample.update_or_create(gene_key=…)
```

Game official island export (`translate_lab_entries_to_official_xy`) anchor:

```text
export_x = raw_x_to_dense_index(raw_x) - raw_x_to_dense_index(extractor_x)
export_y = raw_y - extractor_y - 1
```

(Do not use `raw_x - (extractor_x + 1)` — dense column gap on west branch.) After seed, expect continuous bbox for `server_x` in `decoded_json`.

## Invariants

- **`gene_key`**: canonical topology string (JSON). **Canon for upsert · dedup · stale delete**.
- **`name`**: display only. Same topology → same `gene_key`; renaming alone upserts same row.

## Abstract grid → raw `X,Y` (`grid_to_raw_xy`)

- Abstract: extractor `(0,0)`, output transport `(1,0)` (= one R cell).
- Attach: extensions only `N=(0,-1), W=(-1,0), S=(0,1)` (R forbidden).
- Raw transform `abstract_grid_to_raw_xy` (impl: `django_apps/asteroid_lab/services/sample_gene_exhaustive_generator.py`):
  - `gx >= 0` → `X = gx + 1`
  - `gx < 0` → `X = gx`
  - `Y = gy`  
  → raw column `X==0` is **forbidden**; positive abstract columns always `X>=1`, negative abstract columns `X<0` by this formula.  
  `build_layout_root` fails with `ValueError` if `X==0` immediately after building `BP.Entries`.
- Extension `R` (quarter): pick so parent cell and `equipment_bundles.ports_compatible` align (inlet toward parent direction).

## Canonical `gene_key`

`transport_kind` + `extension_count` + sorted edge list  
Each edge: `(parent_abstract_coord, child_abstract_coord, attach_dir)`.

## DB fields

- `GeneticSample.gene_key` (nullable, indexed, partial unique: unique when set)
- `GeneticSample.metadata_json` — `generator`, `transport_kind`, `extension_topology_key`, `rules`, etc. (separate from game JSON)

## Command

```bash
python manage.py seed_exhaustive_sample_genes --dry-run
python manage.py seed_exhaustive_sample_genes
```

Options: `--transport-kind`, `--max-extensions`, `--limit`, `--delete-stale-generated`, `--generator-version`.  
`--delete-stale-generated` deletes rows where `metadata_json.generator` matches and `gene_key` not in this run's result; **skipped when `--limit` is set**.

## Django Admin

**「Exhaustive sample gene seed」** form at top of `GeneticSample` changelist → `seed_exhaustive_sample_genes` (`dry-run`, `delete_stale_generated` checkboxes).  
Impl: `django_apps/asteroid_lab/admin.py` · `django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html` (`TEMPLATES['DIRS']`).

## Verification

- `python -m pytest tests/unit/asteroid_lab -k "sample_gene or exhaustive"`
- `ruff` / `mypy` / `black` (changed scope)
