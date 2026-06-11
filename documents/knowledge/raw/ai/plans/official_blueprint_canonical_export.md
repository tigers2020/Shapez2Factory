# Official Shapez2 blueprint export (dense anchor)

**Status**: ACTIVE (implementation reflected)  
**Related code**: [`django_apps/asteroid_lab/adapters/blueprint_canonical_export.py`](../../django_apps/asteroid_lab/adapters/blueprint_canonical_export.py), [`django_apps/asteroid_lab/snapshots/blueprint_equivalence.py`](../../django_apps/asteroid_lab/snapshots/blueprint_equivalence.py)

## Purpose

Convert lab-internal layout (`V:1`, raw `X,Y`) to game export form (`V`/`BP.BinaryVersion` 1137, `Icon`, omit defaults), then emit coordinates with **dense columns attached**. Fixed-byte golden (`H4sIAH8kC2oA/…` south 3-ext spread) is **excluded from regression canon**.

## Bug (discarded anchor)

```text
export_x = raw_x - (extractor_x + 1)   # west raw -1 → game X=-3, miner X=-1 → dense {-3,-1,0} gap
export_y = raw_y - (extractor_y + 2)
```

| Kind | copy prefix | dense (export `X`) | symptom |
|------|-------------|-------------------|---------|
| **bug** | `H4sIAAAAAAACC…` | `{-3,-1,0}` | -2 column gap, one cell apart in Admin/game |
| **correct** | `H4sIAMsrC2oA/…` | `{-1,0}` (+ pipe `X=1`) | adjacent |

Fixtures: `tests/fixtures/asteroid_lab/spread_branch_fluid_pipe_bug.txt`, `connected_branch_fluid_pipe.txt`.

## JSON serialization contract

- Top-level key order: `V`, `BP`
- `BP` key order: `$type`, `Icon`, `Entries`, `BinaryVersion`
- Each `Entries` item: omit `X`/`Y`/`R` keys when value is **0**; `T` always last
- `Icon`: `icon:Platforms` + `shape:RuRuRuRu`

## Copy JSON island-local (decode input)

`BP.Entries` `X`/`Y`/`R` are **island blueprint local** (omit → `0`, `X+1` right, `Y+1` down). Not world/Server coordinates. Canon: [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](../../research/research_shapez2_copy_json_island_local_coords_2026-05-23.md).

## Coordinates (lab raw → game export)

extractor raw \((e_x, e_y)\), `e_dense = raw_x_to_dense_index(e_x)`:

```text
export_x = raw_x_to_dense_index(raw_x) - e_dense
export_y = raw_y - e_y - 1
```

Export-column projection: [`copy_json_coords.py`](../../django_apps/asteroid_lab/snapshots/copy_json_coords.py) (PR-F: no `server_coords.py`). Persist: `island_bbox_left_bottom_raw_xy_v1`.

**Do not change** [`sample_gene_exhaustive_generator.py`](../../django_apps/asteroid_lab/services/sample_gene_exhaustive_generator.py) `abstract_grid_to_raw_xy` / NWS placement (bug is export layer only).

## Constants · gzip

- `CONNECTED_BRANCH_FLUID_PIPE_COPY` / `_JSON_BYTES`: user **correct** `H4sIAMsrC2oA/…` (no trailing unnecessary `=` in payload).
- `encode_official_copy_string`: after JSON serialization `gzip.compress(..., mtime=0)` — **no fixed gzip bytes per layout**.

## Layout equivalence

[`blueprint_equivalence.py`](../../django_apps/asteroid_lab/snapshots/blueprint_equivalence.py): extractor anchor + dense_x / raw Y parallel translation.

## Verification

- `tests/unit/asteroid_lab/test_official_canonical_export.py`
- `tests/unit/asteroid_lab/test_export_dense_contiguity.py`
- `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py`
- `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py`

## Done criteria (summary)

- Generated `code` ≠ spread bug copy; connected branch topology JSON bytes · layout equivalent to correct fixture.
- No `{-3,-1,0}` gap pattern in export dense column set.
