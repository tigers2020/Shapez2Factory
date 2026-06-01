# PR-CLI-2c — cleanup + reconstruction Move + complete_map Serializer

**Type:** refactoring (relocation) · contract change (serializer)
**Depends on:** PR-CLI-2a
**Enables:** PR-CLI-2d
**L3 gate:** no L3 touched
**Branch (suggested):** `feat/asteroid-cli-first-recon-move`

---

## Goal

Move the `cleanup/` and `reconstruction/` pipelines into `src/shapez2_factory/domain/asteroid_lab/`
with shims, and add a deterministic `layer01_complete_map.json` serializer for the artifact contract.

## Behavior contract

- `run_topology_reconstruction` and `build_reconstruction_complete_map` behavior unchanged.
- Reconstruction continues to **not** import `replay/` or `layers/` (existing gate
  [`test_reconstruction_does_not_import_layers`](../../../../tests/unit/asteroid_lab/layers/test_layer_import_matrix.py)).
- New `complete_map` serializer is pure and round-trips.

## Non-goals

- No layers/stack_runner move (2d).
- No `reconstructed_asteroid_service.py` move (that file is ORM-bound — stays Django, calls core via shim).

---

## BLOCKING — `display_map.py` pure/viewer split (architect-required, 2026-05-30)

**Confirmed coupling:** [`reconstruction/complete_map.py`](../../../../django_apps/asteroid_lab/reconstruction/complete_map.py) (L12-14)
imports `merged_display_cells_from_reconstruction` from
[`reconstruction/display_map.py`](../../../../django_apps/asteroid_lab/reconstruction/display_map.py), which in turn imports
`replay/snapshot_map_replay` (L13-23). So `build_reconstruction_complete_map()` transitively depends on
`replay/*`. Moving `complete_map` to core without splitting is **blocked** — it would drag a replay/viewer
import into core and break BA-1.

**Required split (this PR):**

```text
1. Pure part → core:
   domain/asteroid_lab/reconstruction/complete_map_merge.py
   - structural cleanup cells + reconstruction overlay merge
   - NO replay import
   - the synthetic-field replacement helpers currently in replay/snapshot_map_replay
     that are pure transforms move here (or to a pure shared module)

2. Viewer part → stays Django:
   reconstruction/display_map.py
   - replay/snapshot visual helpers, full_map row shaping for UI/persist
```

**Contract:** `build_reconstruction_complete_map()` must depend **only** on `complete_map_merge` (pure),
never on `display_map` or `replay/*`.

**Care:** `_replace_miners_with_synthetic_fields` / `_replace_extensions_with_synthetic_fields` /
`rows_from_cells` in [`replay/snapshot_map_replay.py`](../../../../django_apps/asteroid_lab/replay/snapshot_map_replay.py)
must be classified: pure structural transforms → core; replay-frame shaping → Django viewer. Add a parity
test asserting merged cells identical before/after the split.

---

## Move set

| From | To | Note |
|------|-----|------|
| [`cleanup/result.py`](../../../../django_apps/asteroid_lab/cleanup/result.py) | `domain/asteroid_lab/cleanup/result.py` | pure |
| [`cleanup/pipeline.py`](../../../../django_apps/asteroid_lab/cleanup/pipeline.py) | `domain/asteroid_lab/cleanup/pipeline.py` | verify purity |
| `reconstruction/<audited pure files>` | `domain/asteroid_lab/reconstruction/...` | **explicit allowlist only — NO wildcard** |
| — | `adapters/asteroid_lab/complete_map_serializer.py` | **new** — `ReconstructionCompleteMap` → JSON dict + parse |

**Stays in Django (calls core via shim):**
[`services/reconstructed_asteroid_service.py`](../../../../django_apps/asteroid_lab/services/reconstructed_asteroid_service.py) (ORM persist),
[`services/cell_snapshot_service.py`](../../../../django_apps/asteroid_lab/services/) (ORM input build),
[`reconstruction/display_map.py`](../../../../django_apps/asteroid_lab/reconstruction/display_map.py) (viewer part after split).

### NO wildcard move (architect-required, 2026-05-30)

```text
Do NOT bulk-move reconstruction/*.py.
After per-file audit, write an explicit move allowlist in the PR description.
Any file with replay/ viewer/ or ORM dependency stays Django-side.
```

Because the `display_map` split (above) proves reconstruction has hidden replay coupling, a wildcard move
would drag viewer/replay imports into core. Each file is classified pure / Django-bound individually.

---

## Care points

- `display_map.py` split is **blocking** (see section above) — `complete_map` must end up depending only on the pure `complete_map_merge`.
- `services/dto.py` `DecodedCellDTO` is imported widely — move to `domain/asteroid_lab/decoded_cell.py` with shim if pure.

## Tasks

- [ ] **Step 1:** Audit each `reconstruction/*.py` for Django/replay imports; write **explicit move allowlist** in PR description; partition pure vs Django-bound (no wildcard).
- [ ] **Step 2 (BLOCKING):** Split `display_map.py` → pure `complete_map_merge.py` (core) + viewer `display_map.py` (Django); classify synthetic-field transforms; add merge parity test.
- [ ] **Step 3:** Move only allowlisted pure reconstruction modules incl. `complete_map`; shim originals.
- [ ] **Step 4 (SDD):** `test_complete_map_serializer.py` — build a small complete map, serialize, parse, assert equality.
- [ ] **Step 5:** Run reconstruction narrow + decontamination scripts to confirm parity.
- [ ] **Step 6:** purity gate (complete_map now has zero replay import) + ruff + mypy.

## Tests / verification

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_reconstruction_decontamination.ps1
python -m pytest tests/unit/shapez2_factory/test_complete_map_serializer.py -v
python -m mypy django_apps config src
```

## Risks

- `invariant:` `ReconstructionResult.cells` = overlay only; serializer must not leak overlay as algorithm input.
- `invariant:` complete-map decontamination contract (PR #117) — serializer must preserve decontaminated full_map semantics.
- Hidden Django import in a reconstruction helper → keep it Django-side + shim; do not force-move.

## Done criteria

- Pure reconstruction in core; display/persist stay Django; serializer round-trips; reconstruction gates green.
