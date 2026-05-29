# L4 Replay Sprite Cell-Kind Fallback — Implementation Plan (PR-A / P0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop L4 replay `miner` / `extension` overlay rows from resolving to belt sprites in the Lab grid.

**Architecture:** Emit domain `cell_kind` (or `tile_type`) from `layer04_segment.py` based on `transport_kind`. Extend Lab JS kind→sprite mapping and/or tint-only policy for legacy `miner`|`extension` on non–L3-pool frames. No solver algorithm changes.

**Tech Stack:** Python 3.12+ / Django `asteroid_lab` replay · Lab JS · pytest · ruff

**Spec:** [`2026-05-30-outer-rim-direction-arbitration-design.md`](../specs/2026-05-30-outer-rim-direction-arbitration-design.md) §6–§7 (PR-A summary only)

**Related (do not implement here):** [`2026-05-30-outer-rim-direction-arbitration.md`](2026-05-30-outer-rim-direction-arbitration.md) (PR-B)

---

## Execution contract

```text
Commit: ONLY when the user explicitly requests git commit.
```

- [ ] **Checkpoint** — Record files + `python -m pytest <paths>` + `ruff check <paths>`; no commit unless user asks.

---

## Acceptance (must all pass)

```text
L4 replay miner overlay resolves to shape_miner or explicit Layout_*Miner tile_type — not SpaceBelt_Forward.
L4 replay extension overlay resolves to shape_miner_extension / fluid_miner_extension — not belt.
kind=miner must not infer SpaceBelt_Forward.
kind=extension must not infer SpaceBelt_Forward.
```

---

## File map

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/replay/layer04_segment.py` | Map overlay `kind` → domain cell kinds + optional `tile_type` |
| `django_apps/asteroid_lab/replay/timeline_dtos.py` | No change unless wire needs extra fields (prefer `kind` fix only) |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Map legacy `miner`/`extension`; block belt infer for equipment kinds |
| `documents/ai/lab_map_rendering_contract.md` | Document L4 overlay kind contract |
| `tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py` | **New** — wire row contract |
| `tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py` or new JS contract test | Optional static string guard |

---

### Task 1: Failing replay wire test (Python)

**Files:**
- Create: `tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py`

- [ ] **Step 1: Write failing test**

```python
"""L4 replay overlay kinds must not use observation aliases that trigger belt fallback."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.replay.layer04_segment import _overlay_cells_for_placement
from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeStatus, RouteProbeResult
from django_apps.asteroid_lab.genetic_sample.enums import Direction


def _placement_entry() -> RouteProbedBundleCandidate:
    from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate

    candidate = make_bundle_candidate_for_test(
        anchor_coord=(3, 4),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        mining_occupied_cells=frozenset({(3, 4), (2, 4)}),
        transport_stub_cells=frozenset({(4, 4)}),
    )
    entry = RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=(8, 4),
            path_coords=((4, 4), (8, 4)),
            steps_expanded=2,
            transport_kind=TransportKind.SHAPE_BELT,
            route_cost=4,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )
    return entry


def test_layer04_overlay_extractor_kind_is_domain_shape_miner() -> None:
    placement = build_rim_bundle_placement(_placement_entry())
    cells = _overlay_cells_for_placement(placement)
    miner_rows = [c for c in cells if (3, 4) == (c.x, c.y)]
    assert miner_rows
    assert miner_rows[0].kind == "shape_miner"


def test_layer04_overlay_extension_kind_is_domain_not_alias() -> None:
    placement = build_rim_bundle_placement(_placement_entry())
    cells = _overlay_cells_for_placement(placement)
    ext_rows = [c for c in cells if (2, 4) == (c.x, c.y)]
    if ext_rows:
        assert ext_rows[0].kind in ("shape_miner_extension", "fluid_miner_extension")
        assert ext_rows[0].kind != "extension"
```

Adjust coordinates to match `make_bundle_candidate_for_test` default placements if needed after first run.

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py -v
```

Expected: `kind == 'miner'` assertion failure.

---

### Task 2: Fix `layer04_segment.py` overlay kinds

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer04_segment.py`

- [ ] **Step 3: Add kind resolver**

```python
def _overlay_kind_for_role(
    *,
    role: str,
    transport: str,
) -> str:
    if role == "miner":
        return "fluid_miner" if transport == "fluid_pipe" else "shape_miner"
    if role == "extension":
        return "fluid_miner_extension" if transport == "fluid_pipe" else "shape_miner_extension"
    if role == "transport_stub":
        return "space_pipe" if transport == "fluid_pipe" else "space_belt"
    return role
```

Use in `_overlay_cells_for_placement`:

```python
kind=_overlay_kind_for_role(role="miner", transport=transport),
```

(Same for extension / transport_stub.)

Optional: set `tile_type` on `ReplayOverlayCell` when dataclass extended — only if JS still misses; prefer domain `kind` first.

- [ ] **Step 4: Run Task 1 tests — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py -v
```

---

### Task 3: Lab JS belt-infer guard

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 5: Extend `LAB_SPRITE_CELL_KIND_TO_IDENTIFIER`**

```javascript
miner: "Layout_ShapeMiner",
extension: "Layout_ShapeMinerExtension",
```

(Or map to tint-only via `NON_SPRITE_OVERLAY_CELL_KINDS` for L4 event types — prefer domain kinds from server; JS mapping is defense-in-depth.)

- [ ] **Step 6: Guard `inferTransportSpriteIdentifier`**

```javascript
if (ck === "miner" || ck === "shape_miner" || ck === "fluid_miner") return null;
if (ck === "extension" || ck === "shape_miner_extension" || ck === "fluid_miner_extension") return null;
```

Place before `shape_belt` / `transport_kind` belt inference.

- [ ] **Step 7: Add `extension` to L3 legacy tint set** (if L3 pool frames still emit `extension`)

In `LEGACY_L3_POOL_OVERLAY_CELL_KINDS`, add `extension: true` alongside `miner`.

- [ ] **Step 8: Manual Lab check** (optional)

Run server, scrub to `layer04_rim_candidate_selected` frame, confirm extractor/extension cells show miner art not belt.

---

### Task 4: Documentation

**Files:**
- Modify: `documents/ai/lab_map_rendering_contract.md`

- [ ] **Step 9:** Add subsection: L4 replay overlay `kind` MUST be domain `cell_kind` (`shape_miner`, not `miner`).

---

### Task 5: Verification gate

- [ ] **Step 10:**

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py -v
python -m ruff check django_apps/asteroid_lab/replay/layer04_segment.py tests/unit/asteroid_lab/replay/test_layer04_overlay_cell_kind.py
```

---

## Plan self-review (spec coverage)

| Spec §7 requirement | Task |
|---------------------|------|
| Domain cell_kind on L4 overlay | Task 2 |
| No belt fallback | Tasks 2–3 |
| lab_map_rendering_contract sync | Task 4 |
| PR-A isolated from PR-B | Separate plan file ✓ |
