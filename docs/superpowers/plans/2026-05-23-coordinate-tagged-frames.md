# Coordinate Tagged Frames — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce `IslandRawCoord`, `WorldRawCoord`, deprecated `ServerCoord`, and reserved `CoordFrame` names; migrate via PR-A–F without breaking `OptimizationInput` Server canonical frame until the proof gate (PR-E) is green.

**Architecture:** Tagged frozen dataclasses in `snapshots/coord_frames.py`; strangler at decode/reconstruction/replay boundaries; AST + mypy gates; server bridge removal only in PR-F. RTTP branch may land PR-A–C only per spec §RTTP branch policy.

**Tech Stack:** Python 3.12+, frozen dataclasses, `enum.StrEnum`, pytest, ruff, mypy (`django_apps config src`).

**Worktree:** Dedicated branch recommended — `fix/coordinate-tagged-frames` (not `feature/rttp-hybrid-c` for PR-E/F).

**Spec:** [`../specs/2026-05-23-coordinate-tagged-frames-design.md`](../specs/2026-05-23-coordinate-tagged-frames-design.md)

**Plan status:** Ready for execution (self-review 2026-05-23)

---

## Spec → plan coverage

| Spec section | Plan slice |
|--------------|------------|
| Type model + `CoordFrame` reservation | PR-A |
| Island decode boundary | PR-B |
| World reconstruction boundary | PR-C |
| Proof gate G1–G4 | PR-D |
| `OptimizationInput.coord_frame` | PR-E (blocked until PR-D green) |
| Server bridge removal | PR-F |
| AST silent tuple gate | PR-A (skeleton), PR-A/C tighten |
| RTTP policy | Pre-flight + every PR description |

---

## Pre-flight (all PRs)

- [ ] **Step 1:** Read spec end-to-end; confirm branch is **not** RTTP-only if doing PR-E/F.

- [ ] **Step 2:** Baseline narrow tests

```powershell
python -m pytest tests/unit/asteroid_lab/test_copy_json_island_local_coords.py tests/unit/asteroid_lab/test_asteroid_map_coords.py -v
```

Expected: PASS

- [ ] **Step 3:** If working on RTTP branch, verify scope ≤ PR-C (no `OptimizationInput` field changes, no `server_coords` deletion).

---

## PR-A — Types + `CoordFrame` reservation (no behavior change)

**Gate:** Types importable; existing tests green; AST gate file exists (may start minimal).

**Files:**

- Create: `django_apps/asteroid_lab/snapshots/coord_frames.py`
- Modify: `django_apps/asteroid_lab/snapshots/grid_contract.py` — docstring: `Coord` = `ServerCoord` semantics during migration
- Create: `tests/unit/asteroid_lab/test_coord_frames_types.py`
- Create: `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py`

### Task A1: Frozen coord types + enum

- [ ] **Step 1: Write failing test**

```python
# tests/unit/asteroid_lab/test_coord_frames_types.py
from django_apps.asteroid_lab.snapshots.coord_frames import (
    CoordFrame,
    IslandRawCoord,
    ServerCoord,
    WorldRawCoord,
)
import pytest


def test_coord_frame_enum_values_reserved():
    assert CoordFrame.SERVER_DENSE.value == "server_dense"
    assert CoordFrame.ISLAND_RAW.value == "island_raw"
    assert CoordFrame.WORLD_RAW.value == "world_raw"


def test_world_raw_rejects_x_zero():
    with pytest.raises(ValueError, match="x == 0"):
        WorldRawCoord(0, 1)


def test_island_raw_allows_x_zero():
    assert IslandRawCoord(0, 1).x == 0


def test_server_coord_allows_x_zero():
    assert ServerCoord(0, 1).x == 0
```

- [ ] **Step 2:** Run `python -m pytest tests/unit/asteroid_lab/test_coord_frames_types.py -v` — expect FAIL (module missing).

- [ ] **Step 3: Implement** `coord_frames.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

_MSG_WORLD_NO_X0 = "Shapez2 world grid has no x == 0 coordinate"


class CoordFrame(StrEnum):
  SERVER_DENSE = "server_dense"
  ISLAND_RAW = "island_raw"
  WORLD_RAW = "world_raw"


@dataclass(frozen=True, slots=True)
class IslandRawCoord:
  x: int
  y: int


@dataclass(frozen=True, slots=True)
class WorldRawCoord:
  x: int
  y: int

  def __post_init__(self) -> None:
    if self.x == 0:
      raise ValueError(_MSG_WORLD_NO_X0)


@dataclass(frozen=True, slots=True)
class ServerCoord:
  x: int
  y: int


def neighbors4_island(c: IslandRawCoord) -> tuple[IslandRawCoord, ...]:
  x, y = c.x, c.y
  return (
    IslandRawCoord(x - 1, y),
    IslandRawCoord(x + 1, y),
    IslandRawCoord(x, y - 1),
    IslandRawCoord(x, y + 1),
  )


def server_coord_to_tuple(c: ServerCoord) -> tuple[int, int]:
  return (c.x, c.y)


def island_to_tuple(c: IslandRawCoord) -> tuple[int, int]:
  return (c.x, c.y)
```

- [ ] **Step 4:** Run `python -m pytest tests/unit/asteroid_lab/test_coord_frames_types.py -v` — expect PASS.

- [ ] **Step 5:** `python -m ruff check django_apps/asteroid_lab/snapshots/coord_frames.py tests/unit/asteroid_lab/test_coord_frames_types.py`

- [ ] **Step 6:** Commit `feat(coords): add tagged coord frames and CoordFrame enum`

### Task A2: AST gate skeleton

- [ ] **Step 1: Write failing test** — forbid new `server_xy_for_raw_xy` imports under `optimization/` (extend list in PR-C).

```python
# tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py
from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_OPTIMIZATION = _REPO / "django_apps" / "asteroid_lab" / "optimization"


def test_optimization_does_not_import_server_xy_for_raw_xy():
    violations: list[str] = []
    for path in _OPTIMIZATION.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "server_coords" in node.module:
                for alias in node.names:
                    if alias.name == "server_xy_for_raw_xy":
                        violations.append(f"{path}:{node.lineno}")
    assert not violations, "server_xy_for_raw_xy in optimization: " + ", ".join(violations)
```

- [ ] **Step 2:** Run test — expect PASS today (documents contract) or FAIL if violation exists (fix import before commit).

- [ ] **Step 3:** Commit `test(coords): AST gate server_xy_for_raw_xy out of optimization`

---

## PR-B — Island boundary tagging

**Gate:** Copy path exposes `IslandRawCoord`; `server_x`/`server_y` documented deprecated; island tests extended.

**Files:**

- Modify: `django_apps/asteroid_lab/snapshots/copy_json_coords.py` — add `entry_island_raw_coord(entry) -> IslandRawCoord`
- Modify: `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py`
- Modify: `docs/domain/asteroid_coord_transform_spec.md` — link spec

### Task B1: `entry_island_raw_coord`

- [ ] **Step 1: Write failing test**

```python
def test_entry_island_raw_coord_wraps_entry_raw_xy():
    from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord
    from django_apps.asteroid_lab.snapshots.coord_frames import IslandRawCoord

    row = {"Y": 1, "T": "Layout_ShapeMinerExtension"}
    c = entry_island_raw_coord(row)
    assert c == IslandRawCoord(0, 1)
```

- [ ] **Step 2:** Run `python -m pytest tests/unit/asteroid_lab/test_copy_json_island_local_coords.py::test_entry_island_raw_coord_wraps_entry_raw_xy -v` — FAIL.

- [ ] **Step 3:** Implement in `copy_json_coords.py`:

```python
from django_apps.asteroid_lab.snapshots.coord_frames import IslandRawCoord

def entry_island_raw_coord(entry: dict[str, Any]) -> IslandRawCoord:
    x, y = entry_island_local_xy(entry)
    return IslandRawCoord(x, y)
```

- [ ] **Step 4:** Run full `test_copy_json_island_local_coords.py` — PASS.

- [ ] **Step 5:** Commit `feat(coords): IslandRawCoord at copy JSON boundary`

**RTTP note:** May use `entry_island_raw_coord` in replay overlay labeling only.

---

## PR-C — World boundary tagging

**Gate:** Reconstruction topology uses `WorldRawCoord` / `ServerCoord` explicitly at API surface; no `island_to_world` module.

**Files:**

- Modify: `django_apps/asteroid_lab/snapshots/asteroid_map_coords.py` — add `world_raw_coord(x,y) -> WorldRawCoord`, `neighbors4_world(c: WorldRawCoord)`
- Modify: `django_apps/asteroid_lab/reconstruction/acceptance_topology.py` — return type `ServerCoord` via helper `server_coord_for_cell` → `ServerCoord` dataclass
- Modify: `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` (if needed)
- Extend: `test_coordinate_frame_ast_gate.py` — optional: bare tuple annotations in new reconstruction functions

### Task C1: World helpers

- [ ] **Step 1: Write failing test** in `test_asteroid_map_coords.py`:

```python
def test_neighbors4_world_matches_map_cardinals():
    from django_apps.asteroid_lab.snapshots.asteroid_map_coords import neighbors4_world
    from django_apps.asteroid_lab.snapshots.coord_frames import WorldRawCoord

    c = WorldRawCoord(-1, 2)
    nbrs = neighbors4_world(c)
    assert WorldRawCoord(1, 2) in nbrs
    assert WorldRawCoord(-2, 2) in nbrs
```

- [ ] **Step 2:** Implement `neighbors4_world` wrapping `left_of`/`right_of`.

- [ ] **Step 3:** Run `python -m pytest tests/unit/asteroid_lab/test_asteroid_map_coords.py -v` — PASS.

- [ ] **Step 4:** Commit `feat(coords): WorldRawCoord neighbors at map boundary`

### Task C2: `server_coord_for_cell` returns `ServerCoord`

- [ ] **Step 1:** Adjust `acceptance_topology.server_coord_for_cell` to return `ServerCoord` (wrap tuple).

- [ ] **Step 2:** Run `python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py -v`

- [ ] **Step 3:** Commit `refactor(coords): ServerCoord type at reconstruction adapter`

---

## PR-D — Proof pack (equivalence)

**Gate:** G1–G2 remain green; G3 documents proven or **explicit xfail** with issue link; no `OptimizationInput` changes.

**Files:**

- Create: `tests/unit/asteroid_lab/test_coordinate_frame_equivalence.py`
- Create: `tests/fixtures/asteroid_lab/coord_frame/` (optional JSON manifests)

### Task D1: Equivalence scaffold

- [x] **Step 1: Write test** (initially xfail or skip until adapter exists):

```python
import pytest
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy
from tests.unit.asteroid_lab.test_copy_json_island_local_coords import (
    _THREE_EXT_MINER_BELT_COPY,
)

@pytest.mark.xfail(reason="island_to_world adapter not proven — gate closed")
def test_three_ext_layout_island_and_world_topology_equivalent():
    """When adapter exists, mineable/occupied sets match under WorldRawCoord."""
    pytest.skip("implement after explicit island→world proof module")
```

- [x] **Step 2:** Document in test module docstring: gate closed until xfail removed.

- [x] **Step 3:** Run `python -m pytest tests/unit/asteroid_lab/test_coordinate_frame_equivalence.py -v` — xfail/skip acceptable.

- [x] **Step 4:** Commit `test(coords): equivalence gate scaffold (PR-D)`

**Exit criterion for PR-E:** Remove xfail/skip on ≥1 fixture; G3 green.

---

## PR-E — `OptimizationInput.coord_frame` (blocked until PR-D green)

**Do not start** until `test_coordinate_frame_equivalence` passes without xfail.

**Files:**

- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Modify: `documents/Algorithm/asteroid_lab_01_optimization_input.md`
- Modify: `.cursor/rules/asteroid-lab-invariants.mdc`
- Create: `tests/unit/asteroid_lab/test_optimization_input_coord_frame.py`

### Task E1: DTO field

- [ ] **Step 1: Write failing test**

```python
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame

def test_optimization_input_defaults_to_server_dense_frame(greenfield_optimization_input):
    assert greenfield_optimization_input.coord_frame == CoordFrame.SERVER_DENSE
```

- [ ] **Step 2:** Add to frozen `OptimizationInput`:

```python
coord_frame: CoordFrame = CoordFrame.SERVER_DENSE
```

- [ ] **Step 3:** Run optimization unit tests — PASS.

- [ ] **Step 4:** Commit `feat(coords): OptimizationInput.coord_frame gate field`

### Task E2: Promote single frame (only when G3 green)

- [ ] **Step 1:** Set `coord_frame=CoordFrame.ISLAND_RAW` or `WORLD_RAW` per proof outcome; migrate `mineable_cells` to matching typed coord set (breaking — update all consumers in same PR).

- [ ] **Step 2:** Full `python -m pytest tests/unit/asteroid_lab/ -v` (coordinate-related paths first).

- [ ] **Step 3:** Commit with body explaining proof fixture IDs.

---

## PR-D follow-up — scaffold + wiring (committed after PR-A–C)

- [x] `test_coordinate_frame_equivalence.py` (G3 xfail + island fixture)
- [x] `entry_island_raw_coord` in decode / normalization / fingerprint / export import
- [x] AST allowlists: `optimization`, `reconstruction`, `replay`, `web/services`

---

## PR-F — Remove server bridge (north star: server x/y extinction)

**Blocked until PR-E stable on chosen frame.**

**Files:**

- Delete or gut: `server_coords.py` public attach (keep fingerprint migration shim if needed)
- Remove: `lab_xy_from_server_xy` usage in replay after UI uses promoted frame
- Update: `coord_system` fingerprint version + golden tests
- Modify: `documents/Algorithm/asteroid_lab_00_overview.md`, `asteroid_lab_03_candidate_generator.md`

### PR-F extinction order (delete sequence)

1. `django_apps/asteroid_lab/snapshots/server_coords.py` — bridge (last consumer wins)
2. `django_apps/asteroid_lab/replay/projection_context.py` — `lab_xy_from_server_xy`
3. `django_apps/web/services/replay_frame_cell_lookup.py`
4. `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — dense mirror
5. `reconstruction/pipeline.py`, `topology_contract.py`, `confidence.py` — stop emitting server tuples
6. `decoded_blueprint_snapshot.py` — drop `server_x`/`server_y` attach; island-only DTO coords
7. `services/dto.py` — remove `server_x`/`server_y` fields (or legacy read one release)
8. `layout_fingerprint.py` — new `coord_system` string + golden refresh
9. `optimization/**` — `neighbors4_server` → island/world neighbors; AST allowlists **empty**
10. `.cursor/rules/asteroid-lab-invariants.mdc`, `asteroid_lab_01` — raw frame canonical

### Task F1: Forbidden token expansion

- [ ] **Step 1:** Extend AST gate: `raw_to_server`, `server_to_raw`, `attach_server_coords` not imported in `optimization/**`.

- [ ] **Step 2:** Remove bridge; fix tests.

- [ ] **Step 3:** `python -m pytest tests/unit/asteroid_lab/ tests/unit/shapez_asteroid/ -v` (per project narrow/full policy).

- [ ] **Step 4:** `python -m ruff check django_apps/asteroid_lab/snapshots/ django_apps/asteroid_lab/optimization/`

- [ ] **Step 5:** Commit `refactor(coords): remove server dense bridge (PR-F)`

---

## Verification matrix (per PR)

| PR | Command |
|----|---------|
| A–C | `python -m pytest tests/unit/asteroid_lab/test_coord_frames_types.py tests/unit/asteroid_lab/test_copy_json_island_local_coords.py tests/unit/asteroid_lab/test_asteroid_map_coords.py tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py -v` |
| D | `python -m pytest tests/unit/asteroid_lab/test_coordinate_frame_equivalence.py -v` |
| E–F | `powershell -File scripts/test_fast.ps1` (or full gate before merge) |

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| `CoordFrame` enum reserved PR-A | A1 |
| No silent tuple AST | A2, extended F1 |
| RTTP PR-A–C only | Pre-flight, PR headers |
| Gate before PR-E | D1, E blocked |
| Server creation allowlist | A2, F1 |
| island→world forbidden until proof | D xfail, no adapter task |

No TBD placeholders in task bodies above.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-23-coordinate-tagged-frames.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — one subagent per PR (A→B→C→D→E→F), review between PRs.
2. **Inline Execution** — same session with executing-plans checkpoints; stop before PR-E until equivalence green.

**Which approach do you want?**
