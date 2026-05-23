# PR-F Extinction Wave C — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In one coordinated wave, remove runtime dependence on dense server `(server_x, server_y)` and `server_xy_params` across reconstruction persist, replay/RTTP/web adapters, while keeping **one-release read-compat** for legacy persisted JSON.

**Architecture:** Introduce shared **island bbox** helpers (`island_bbox.py`). Reconstruction topology/confidence/export emit **only island `(x,y)`** keys and `full_map_island_bbox` meta. Replay/web/RTTP treat overlay `(x,y)` as island-local (identity projection). **`server_coords.py` deleted** (product + tests); AST gate forbids `server_*` tokens in `django_apps`/`src`. Doc sweep: 2026-05-23.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`), existing `CoordFrame` / `IslandRawCoord` in `coord_frames.py`.

**Spec:** [`../specs/2026-05-23-coordinate-tagged-frames-design.md`](../specs/2026-05-23-coordinate-tagged-frames-design.md)  
**Parent plan:** [`2026-05-23-coordinate-tagged-frames.md`](2026-05-23-coordinate-tagged-frames.md) (PR-F F1 Step 2 + Step 5)

**Branch (recommended):** `refactor/pr-f-extinction-wave-c` off `master` @ `3e68740b` or later.

---

## File map (Wave C)

| File | Responsibility after Wave C |
|------|-----------------------------|
| **Create** `django_apps/asteroid_lab/snapshots/island_bbox.py` | `island_bbox_from_cells`, `island_bbox_from_xy_dicts`, `full_map_island_bbox_from_decoded_json` (+ legacy server bbox read shim) |
| **Modify** `reconstruction/display_map.py` | Delegate island bbox; deprecate server bbox writers |
| **Modify** `reconstruction/result.py` | `coord_frame: CoordFrame`; stop setting `server_xy_params` on new runs |
| **Modify** `reconstruction/acceptance_topology.py` | Default `ISLAND_RAW`; remove `server_coords` import |
| **Modify** `reconstruction/topology_contract.py` | Island bbox for topology extent; no `map_bbox_dense_and_y` |
| **Modify** `reconstruction/pipeline.py` | Seam via `entries_have_explicit_raw_x_zero` from `copy_json_coords`; no `unpack_server_xy_params` |
| **Modify** `reconstruction/confidence.py` | Pass `coord_frame` only; no dense params |
| **Modify** `adapters/reconstruction_blueprint_export.py` | `full_map_island_bbox`; no `server_x`/`server_y` on entries |
| **Modify** `services/reconstructed_map_persist_builder.py` | Persist island bbox meta |
| **Modify** `replay/projection_context.py` | Island identity; remove `lab_xy_from_server_xy` from product path |
| **Modify** `services/lab_rttp_snapshot_compose.py` | Island-only overlay clip |
| **Modify** `services/lab_replay_timeline_payload.py` | Island bbox for timeline rows |
| **Modify** `web/services/replay_frame_cell_lookup.py` | Island synthetic cells; no `server_xy_for_raw_xy` |
| **Modify** `cleanup/pipeline.py` | Island bbox params |
| **Modify** `genetic_sample_mini_map.py` | Prefer `full_map_island_bbox_from_decoded_json` |
| **Modify** `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py` | Empty allowlists + `map_bbox_dense_and_y` gate |
| **Modify** tests listed per task | Contract updates |
| **Modify** `documents/Algorithm/asteroid_lab_03_candidate_generator.md`, `.cursor/rules/asteroid-lab-invariants.mdc` | Docs sync |
| **Delete** `snapshots/server_coords.py` | Removed PR-F; historical spec in archived research doc |

---

## Pre-flight

- [ ] **Step 1:** Confirm not on RTTP-only branch; read spec §Boundary rules and §RTTP branch policy.

- [ ] **Step 2:** Baseline

```powershell
cd f:\Python_Projects\shapez2Factory
powershell -File scripts/test_fast.ps1
```

Expected: PASS (1163+ tests; 1 xfail `test_coordinate_frame_equivalence` world path is OK).

- [ ] **Step 3:** Create branch

```bash
git checkout -b refactor/pr-f-extinction-wave-c
```

---

### Task 1: Island bbox helpers (shared kernel)

**Files:**
- Create: `django_apps/asteroid_lab/snapshots/island_bbox.py`
- Create: `tests/unit/asteroid_lab/test_island_bbox.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/asteroid_lab/test_island_bbox.py
from __future__ import annotations

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.island_bbox import (
    island_bbox_from_cells,
    island_bbox_from_xy_dicts,
)


def test_island_bbox_from_cells_tight_extent() -> None:
    cells = (
        DecodedCellDTO(
            x=0,
            y=-1,
            layer=None,
            rotation=0,
            tile_type="Layout_FluidMiner",
            cell_kind="miner",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
            server_x=None,
            server_y=None,
        ),
        DecodedCellDTO(
            x=1,
            y=-1,
            layer=None,
            rotation=0,
            tile_type="SpacePipe_Forward",
            cell_kind="transport",
            transport_kind="forward",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
            server_x=None,
            server_y=None,
        ),
    )
    bb = island_bbox_from_cells(cells)
    assert bb == {
        "min_x": 0,
        "max_x": 1,
        "min_y": -1,
        "max_y": -1,
        "width": 2,
        "height": 1,
    }


def test_island_bbox_from_xy_dicts_empty_returns_none() -> None:
    assert island_bbox_from_xy_dicts([]) is None
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m pytest tests/unit/asteroid_lab/test_island_bbox.py -v
```

Expected: FAIL `ModuleNotFoundError: island_bbox`

- [ ] **Step 3: Write minimal implementation**

```python
# django_apps/asteroid_lab/snapshots/island_bbox.py
"""Island-local bbox helpers (PR-F Wave C). Pure — no Django imports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def island_bbox_from_xy_dicts(rows: Sequence[dict[str, Any]]) -> dict[str, int] | None:
    xs: list[int] = []
    ys: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            xs.append(int(row["x"]))
            ys.append(int(row["y"]))
        except (KeyError, TypeError, ValueError):
            try:
                xs.append(int(row["X"]))
                ys.append(int(row["Y"]))
            except (KeyError, TypeError, ValueError):
                continue
    if not xs:
        return None
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "width": max_x - min_x + 1,
        "height": max_y - min_y + 1,
    }


def island_bbox_from_cells(cells: Sequence[DecodedCellDTO]) -> dict[str, int] | None:
    return island_bbox_from_xy_dicts([{"x": c.x, "y": c.y} for c in cells])


def full_map_island_bbox_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, int] | None:
    """Read persisted reconstruction meta or compute from ``BP.Entries`` island X/Y."""

    meta = decoded_json.get("_asteroid_lab_reconstruction")
    if isinstance(meta, dict):
        bb = meta.get("full_map_island_bbox")
        if isinstance(bb, dict) and "min_x" in bb and "width" in bb:
            return {k: int(bb[k]) for k in ("min_x", "max_x", "min_y", "max_y", "width", "height")}
    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return None
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        return None
    return island_bbox_from_xy_dicts(
        [{"X": e.get("X"), "Y": e.get("Y")} for e in entries if isinstance(e, dict)]
    )


__all__ = [
    "full_map_island_bbox_from_decoded_json",
    "island_bbox_from_cells",
    "island_bbox_from_xy_dicts",
]
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m pytest tests/unit/asteroid_lab/test_island_bbox.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/snapshots/island_bbox.py tests/unit/asteroid_lab/test_island_bbox.py
git commit -m "feat(coords): island bbox helpers for PR-F wave C"
```

---

### Task 2: Reconstruction export — island meta, no server on entries

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py`
- Modify: `django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py`
- Modify: `tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py`

- [ ] **Step 1: Write the failing test** (add to `test_reconstruction_persist_full_map_bbox.py` or new test file)

```python
def test_reconstructed_export_writes_full_map_island_bbox_not_server_on_entries() -> None:
    from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
        build_reconstructed_blueprint_root,
    )
    from django_apps.asteroid_lab.services.dto import DecodedCellDTO

    cell = DecodedCellDTO(
        x=1,
        y=0,
        layer=None,
        rotation=0,
        tile_type="SpacePipe_Forward",
        cell_kind="transport",
        transport_kind="forward",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": 1, "Y": 0, "T": "SpacePipe_Forward"},
        server_x=None,
        server_y=None,
    )
    root = build_reconstructed_blueprint_root(
        (cell,),
        full_map_island_bbox={
            "min_x": 1,
            "max_x": 1,
            "min_y": 0,
            "max_y": 0,
            "width": 1,
            "height": 1,
        },
    )
    entry = root["BP"]["Entries"][0]
    assert "server_x" not in entry and "server_y" not in entry
    meta = root["_asteroid_lab_reconstruction"]
    assert "full_map_island_bbox" in meta
    assert "full_map_server_bbox" not in meta
```

- [ ] **Step 2: Run test — expect FAIL** (wrong kwarg or server keys present)

- [ ] **Step 3: Implement**

In `reconstruction_blueprint_export.py`:

1. Replace parameter `full_map_server_bbox` → `full_map_island_bbox` on `build_reconstructed_blueprint_root` and `build_reconstructed_normalized_dto`.
2. In `_entry_dict_from_cell`, **delete** the block that sets `server_x`/`server_y`.
3. In `recon_meta`, set `full_map_island_bbox` when provided; do **not** write `full_map_server_bbox` on new exports.
4. Update `reconstructed_map_persist_builder.py` call sites to pass `island_bbox_from_cells(result.cells)` instead of server bbox.

Keep **read** compat in `display_map.full_map_server_bbox_from_decoded_json` unchanged for this task (Task 6 admin).

- [ ] **Step 4: Run test — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py -v
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(coords): reconstruction export island bbox meta only"
```

---

### Task 3: Reconstruction topology — ISLAND_RAW only on new runs

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/acceptance_topology.py`
- Modify: `django_apps/asteroid_lab/reconstruction/topology_contract.py`
- Modify: `django_apps/asteroid_lab/reconstruction/confidence.py`
- Modify: `django_apps/asteroid_lab/reconstruction/result.py`
- Modify: `django_apps/asteroid_lab/reconstruction/pipeline.py`
- Test: `tests/unit/asteroid_lab/test_reconstruction_topology.py`, `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py`

- [ ] **Step 1: Write failing test** — fixture contract expects no `server_xy_params` on new reconstruction results

```python
def test_reconstruction_result_default_coord_frame_is_island_raw(sample_fixture) -> None:
    from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame

    result = sample_fixture  # use existing fixture helper
    assert getattr(result, "coord_frame", CoordFrame.ISLAND_RAW) == CoordFrame.ISLAND_RAW
    assert result.server_xy_params is None
```

(Adapt to existing fixture names in `test_reconstruction_fixture_contract.py`.)

- [ ] **Step 2: Run — FAIL**

- [ ] **Step 3: Implement**

1. `ReconstructionResult`: add field `coord_frame: CoordFrame = CoordFrame.ISLAND_RAW`. Document `server_xy_params` as **legacy read-only**; pipeline sets `None` for new runs.
2. `acceptance_topology.py`: remove `from server_coords import server_xy_for_raw_xy, unpack_server_xy_params`. `infer_topology_coord_frame` → always return `ISLAND_RAW` when no cell has `server_x` int (current behavior); if any cell has `server_x`, still support **read** via `server_coord_for_cell` but log boundary event once (optional).
3. `topology_coord_for_cell`: when `coord_frame == ISLAND_RAW`, return `(cell.x, cell.y)` only.
4. `topology_contract.py`: replace `map_bbox_dense_and_y` with `island_bbox_from_cells` / `island_bbox_from_xy_dicts`.
5. `pipeline.py`: remove `from server_coords import unpack_server_xy_params`. For seam guard at `x == 0`, use `entries_have_explicit_raw_x_zero` from `copy_json_coords` on source entries instead of `unpack_server_xy_params`.
6. `confidence.py`: pass `coord_frame=result.coord_frame`; stop threading `server_xy_params` into topology when `None`.

- [ ] **Step 4: Run narrow tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_topology.py tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py -v
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(coords): reconstruction topology island-only (wave C)"
```

---

### Task 4: Replay + RTTP + web — island projection (bundled with Task 3 commit or separate)

**Files:**
- Modify: `django_apps/asteroid_lab/replay/projection_context.py`
- Modify: `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py`
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Modify: `django_apps/web/services/replay_frame_cell_lookup.py`
- Test: `tests/unit/asteroid_lab/test_server_to_lab_projection.py`, `tests/unit/web/test_replay_frame_cell_lookup.py`, `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Write failing test** — RTTP clip uses island overlay without `server_xy_params`

```python
def test_clip_overlay_island_coords_without_server_params() -> None:
    base = {
        "full_cells": [{"x": 1, "y": 0, "kind": "asteroid_shape_field"}],
    }
    overlay = [{"x": 1, "y": 0, "cell_kind": "transport"}]
    out = clip_overlay_cells_to_base_map_domain(overlay, base, server_xy_params=None)
    assert len(out) == 1
    assert out[0]["x"] == 1 and out[0]["y"] == 0
```

- [ ] **Step 2: Run — FAIL** if server path required

- [ ] **Step 3: Implement**

1. `lab_rttp_snapshot_compose.py`: remove `lab_xy_from_server_xy` import and `server_to_lab` map from `_base_map_overlay_anchors`. Treat overlay `x,y` as island; only clip to `lab_anchors` from `full_cells.x/y`.
2. Remove `server_xy_params` kwargs from `clip_overlay_cells_to_base_map_domain`, `project_rttp_row_to_product_frame`, `interleave_rttp_snapshot_frames`; update all callers (grep `server_xy_params=` in `django_apps/`).
3. `projection_context.py`: keep `lab_xy_from_replay_cell` as canonical. Move `lab_xy_from_server_xy` / `dense_index_to_raw_x` to `server_coords.py` or mark deprecated; **product code must not call them**.
4. `ReplayProjectionContext`: make `server_xy_params` optional with default `None`; timeline builders omit it.
5. `replay_frame_cell_lookup.py`: remove `from server_coords import server_xy_for_raw_xy`. In `_try_synthetic_lab_empty`, island branch only — no `server_x`/`server_y` on synthetic dict.
6. `lab_replay_timeline_payload.py`: replace `map_bbox_dense_and_y` with `island_bbox_from_xy_dicts`.

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_server_to_lab_projection.py tests/unit/web/test_replay_frame_cell_lookup.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -v
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(coords): replay RTTP web island-only projection (wave C)"
```

---

### Task 5: Cleanup pipeline + optimization adapter tail

**Files:**
- Modify: `django_apps/asteroid_lab/cleanup/pipeline.py`
- Modify: `django_apps/asteroid_lab/cleanup/result.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Test: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`

- [ ] **Step 1: Write failing test** — cleanup result has no dense params when island frame

(Extend existing cleanup test or add assertion `cleanup.server_xy_params is None`.)

- [ ] **Step 3: Implement**

1. `cleanup/pipeline.py`: `params = island_bbox_from_cells(...)` stored as optional metadata only if needed; **do not** call `map_bbox_dense_and_y`.
2. `reconstruction_adapter.py`: `_cells_by_server_coord` path only when legacy cells have `server_x`; else key by `(c.x, c.y)`.

- [ ] **Step 4: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_optimization_input_adapter.py -v
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(coords): cleanup and optimization adapter island keys"
```

---

### Task 6: AST gates — empty allowlists + dense symbol ban

**Files:**
- Modify: `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py`

- [ ] **Step 1: Write failing tests**

```python
_RECONSTRUCTION_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset()
_REPLAY_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset()
_WEB_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset()

_DENSE_BBOX_SYMBOLS: frozenset[str] = frozenset(
    {"map_bbox_dense_and_y", "unpack_server_xy_params", "lab_xy_from_server_xy"}
)

def test_reconstruction_does_not_import_map_bbox_dense_and_y() -> None:
    ...
```

- [ ] **Step 2: Run — FAIL** (pipeline/topology still import)

- [ ] **Step 3: Fix any remaining production imports** until gates pass. Tests may still import `server_coords` in `tests/unit/asteroid_lab/test_server_coords_and_fingerprint.py`.

- [ ] **Step 4: PASS** `test_coordinate_frame_ast_gate.py`

- [ ] **Step 5: Commit**

```bash
git commit -m "test(coords): empty server_xy allowlists after wave C"
```

---

### Task 7: Admin mini-map + display_map read compat

**Files:**
- Modify: `django_apps/asteroid_lab/genetic_sample_mini_map.py`
- Modify: `django_apps/asteroid_lab/reconstruction/display_map.py`

- [ ] **Step 1: Test** — mini-map uses island meta when `full_map_island_bbox` present on decoded JSON (extend `test_genetic_sample_mini_map.py` with reconstructed meta fixture).

- [ ] **Step 3: Implement**

1. `display_map.py`: add `full_map_island_bbox_from_decoded_json` delegating to `island_bbox.full_map_island_bbox_from_decoded_json`.
2. `genetic_sample_mini_map.py`: prefer island meta over `full_map_server_bbox_from_decoded_json`.

- [ ] **Step 4: Run** `test_genetic_sample_mini_map.py`

- [ ] **Step 5: Commit**

---

### Task 8: Docs + invariants

**Files:**
- Modify: `documents/Algorithm/asteroid_lab_03_candidate_generator.md`
- Modify: `.cursor/rules/asteroid-lab-invariants.mdc`
- Modify: `docs/superpowers/plans/2026-05-23-coordinate-tagged-frames.md` (F1 Step 2 done, Step 5 commit hash)

- [ ] **Step 1:** Replace `neighbors4_server` checklist with `neighbors4` / island topology wording.

- [ ] **Step 2:** Invariants: reconstruction meta `full_map_island_bbox`; legacy `full_map_server_bbox` read-compat one release.

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(coords): wave C island frame canonical in algorithm docs"
```

---

### Task 9: Full verification + final commit message

- [ ] **Step 1:**

```powershell
python -m pytest tests/unit/asteroid_lab/ tests/unit/shapez_asteroid/ tests/unit/web/test_replay_frame_cell_lookup.py -v
powershell -File scripts/test_fast.ps1
python -m ruff check django_apps/asteroid_lab/snapshots/ django_apps/asteroid_lab/reconstruction/ django_apps/asteroid_lab/replay/ django_apps/web/services/replay_frame_cell_lookup.py
```

- [ ] **Step 2:** Squash or final commit per team policy:

```bash
git commit -m "refactor(coords): remove server dense bridge (PR-F wave C)" -m "Reconstruction persist and replay/RTTP/web adapters use island bbox and (x,y) only. server_coords confined to unit tests. AST allowlists empty."
```

- [ ] **Step 3:** Update parent plan PR-F progress log with commit SHA.

---

## Out of scope (follow-up PR)

| Item | Reason |
|------|--------|
| Delete `server_coords.py` entirely | Keep dense math tests until golden migration |
| Remove `DecodedCellDTO.server_x/y` fields | Separate breaking DTO PR |
| JS `asteroid_miner_layout_lab.js` dense mirror removal | UI wave D in extinction order |
| `neighbors4_server` alias removal | Low risk; do after bridge imports zero |
| DTO field removal + `data-server-*` HTML rename | Admin contract change |

---

## Spec self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| No `attach_server_coords` on new persist | Task 2 (already true; reinforced) |
| Remove `lab_xy_from_server_xy` product usage | Task 4 |
| Reconstruction stops emitting server tuples | Task 2, 3 |
| `server_coords` creation sites only listed | Task 6 AST |
| island→world forbidden | No task (unchanged xfail) |
| Read-compat one release for legacy JSON | Task 2 read paths, Task 6 display_map |

**Placeholder scan:** None.

---

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-23-pr-f-extinction-wave-c.md`.**

**Two execution options:**

1. **Subagent-Driven (recommended)** — one subagent per task (1→9), spec compliance then code quality review between tasks.

2. **Inline Execution** — same session with executing-plans checkpoints after Tasks 3 and 6 (largest coupling surfaces).

**Which approach?**
