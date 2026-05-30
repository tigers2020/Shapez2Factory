# PR-CLI-2a — Pure DTO Move (coord / grid / snapshot contracts)

**Type:** refactoring (relocation) · contract change (import path)
**Depends on:** PR-CLI-1
**Enables:** PR-CLI-2b, PR-CLI-2c
**Branch (suggested):** `feat/asteroid-cli-first-dto-move`

---

## Goal

Relocate leaf-level, dependency-free DTOs (coordinates, grid, game_data snapshot contracts) into
`src/shapez2_factory/domain/asteroid_lab/`, leaving thin re-export shims in `django_apps` so existing
imports keep working. No behavior change.

## Behavior contract

- All current imports of moved modules continue to resolve (via shim).
- Moved modules contain **no** Django imports (BA-1).
- Byte-for-byte logic identical; only location + import rewrites.

## Non-goals

- No cleanup/reconstruction move (2c).
- No layers move (2d).
- No `game_data` ORM decoupling (2b).

---

## Move set (leaf DTOs only)

| From | To |
|------|-----|
| [`snapshots/grid_contract.py`](../../../../django_apps/asteroid_lab/snapshots/grid_contract.py) | `domain/asteroid_lab/grid_contract.py` |
| [`snapshots/coord_frames.py`](../../../../django_apps/asteroid_lab/snapshots/coord_frames.py) | `domain/asteroid_lab/coord_frames.py` |
| [`contracts/game_data_snapshot.py`](../../../../django_apps/asteroid_lab/contracts/game_data_snapshot.py) | `domain/asteroid_lab/game_data_snapshot.py` |
| [`contracts/game_data_snapshot_provenance.py`](../../../../django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py) | `domain/asteroid_lab/game_data_snapshot_provenance.py` |
| [`contracts/building_catalog_slice.py`](../../../../django_apps/asteroid_lab/contracts/building_catalog_slice.py) | `domain/asteroid_lab/building_catalog_slice.py` |
| [`contracts/building_catalog_slice_hash.py`](../../../../django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py) | `domain/asteroid_lab/building_catalog_slice_hash.py` |

> Candidate set chosen because each is pure (verified: no `from django` in these files). Re-verify per file before moving.

## Shim pattern

```python
# django_apps/asteroid_lab/snapshots/grid_contract.py  (after move)
from shapez2_factory.domain.asteroid_lab.grid_contract import *  # noqa: F401,F403
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord, BBox  # explicit re-export
```

> Prefer explicit re-exports over `*` where `__all__` is unclear, to keep mypy strict happy.

---

## Tasks

- [ ] **Step 1:** For each module: confirm zero Django import; copy to `domain/asteroid_lab/`; adjust intra-core imports.
- [ ] **Step 2:** Replace original with shim re-export.
- [ ] **Step 3:** Run existing import-matrix + reconstruction tests to confirm no breakage:
  [`test_layer_import_matrix.py`](../../../../tests/unit/asteroid_lab/layers/test_layer_import_matrix.py).
- [ ] **Step 4:** Add `tests/unit/shapez2_factory/test_dto_importable_without_django.py` — import each moved module in a subprocess with `DJANGO_SETTINGS_MODULE` unset.
- [ ] **Step 5:** Purity gate + ruff + mypy.

## Tests / verification

```powershell
python -m pytest tests/unit/shapez2_factory/ tests/unit/asteroid_lab/layers/test_layer_import_matrix.py -v
python -m pytest tests/unit/asteroid_lab/ -v
python -m ruff check src/shapez2_factory django_apps/asteroid_lab/snapshots django_apps/asteroid_lab/contracts
python -m mypy django_apps config src
```

## Risks

- `invariant:` coordinate frame contracts (`island_raw_xy_v1`) must not change — pure relocation only.
- Circular import if a moved DTO imported a non-moved Django module — verify leaf purity first; defer non-leaf to later PRs.
- mypy strict on `*` re-export — use explicit names.

## Done criteria

- Moved DTOs live in core; shims green; full `tests/unit/asteroid_lab` suite unchanged; BA-1 gate green.
