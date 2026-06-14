# Any Boundary Typing — Design Spec

**Status:** DESIGN APPROVED  
**Date:** 2026-06-11  
**Related:** SHA-20 (mypy phased rollout), `2026-06-10-solver-runtime-wires-replay-projection-design.md`  
**Governance manual:** `documents/ai/manuals/typing_contracts.md`

---

## 1. Problem

The repo has **~1,454** `typing.Any` occurrences across **196** Python files. Roughly **68%** are `dict[str, Any]`, concentrated in `django_apps` (replay, UI, artifact, game-data import) — not solver core logic.

This is not primarily “missing type hints.” It is **missing wire/schema authority** at serialization boundaries. Hotspot burn-down without named schemas risks **contract drift** (each module invents a de-facto JSON shape).

### Success metric

```text
Contract drift reduction (rename/missing field breaks compile or test)
NOT raw Any count reduction
```

---

## 2. Strategy (approved)

```text
Primary:   A) Wire-boundary contracts
           D) Governance first
Secondary: B) mypy phased rollout (report-only → hard gate)
Avoid:     C) Hotspot-only burn-down without schema names
```

---

## 3. Core invariants

```text
Semantic authority is frozen dataclass.
Wire authority is named TypedDict.
Raw dict[str, Any] is allowed only at explicit decode/import boundaries.
Converters are the only legal path between semantic DTOs and wire dictionaries.
```

### Boundary schema style (B+, dataclass-first semantics)

| Role | Type | Authority |
|------|------|-----------|
| In-process state | `frozen dataclass` | Semantic / business meaning |
| Serialized JSON | `named TypedDict` | Wire projection only |
| Pre-normalize input | `RawJsonObject` | Decode/import escape hatch |

**Do not** treat TypedDict as a second domain model. It is only the serialized projection contract.

### Module layout pattern

| Layer | Module pattern | Example |
|-------|----------------|---------|
| Semantic DTO | `*_dtos.py` | `timeline_dtos.py` → `ReplayOverlayCell` |
| Wire shape | `*_wire.py` / `*_wires.py` | `replay_overlay_wire.py` → `ReplayOverlayCellWire` |
| Converter | `*_serialization.py` / `overlay_wire_contract.py` | `overlay_cell_to_wire()` / `overlay_cell_from_wire()` |

### Shared aliases (Phase 0)

Location: `django_apps/asteroid_lab/typing_boundary.py`  
(Promote to `shapez2_factory/` only when cross-package reuse is proven.)

```python
from typing import Any, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

# typing_contracts: raw JSON before normalization only
RawJsonObject: TypeAlias = dict[str, Any]
```

Implementation may use Python 3.12 `type` alias syntax where ruff UP040 prefers it over `TypeAlias`.

Principle:

```text
RawJsonObject  = unvalidated input only
JsonValue      = validated generic JSON tree
TypedDict      = named wire contract
```

### TypedDict optional-field policy

```text
TypedDict must be total=True by default.
Use NotRequired[...] for optional wire keys.
Use total=False only for explicitly documented extension/patch payloads.
```

Literal narrowing for transport tokens happens inside converters, not at call sites.

---

## 4. Authority map (no drift)

Aligns with existing replay/runtime wire specs.

```text
Runtime wire (solver_runtime_wires.v1.json)
  → replay_projection_only; NOT algorithm input

Replay assembler (lab_timeline_adapter + solver_runtime_assembler)
  → timeline frame authority

overlay_wire_contract
  → overlay occupancy vs output_transport_kind invariant

effective_cell_view
  → UI read model (terrain + occupant + transport merge)

solver_run_config_keys
  → stable config_json key constants
```

### Forbidden patterns

```python
# FORBIDDEN: hand-built wire at call site
frame["overlay_cells"].append({"x": x, "y": y, "kind": "..."})

# REQUIRED: converter
frame_overlay_cells.append(overlay_cell_to_wire_dict(cell))
```

### `EffectiveCellView.to_wire()` migration (two-step)

Do not remove the method in the first PR slice.

```text
1. Add effective_cell_to_wire(view) -> EffectiveCellWire
2. Migrate all call sites to the converter
3. Remove to_wire() or delete deprecated shim in a follow-up slice
```

---

## 5. Phased rollout

### Phase 0 — Governance (no behavior change)

| Deliverable | Path |
|-------------|------|
| Typing policy manual | `documents/ai/manuals/typing_contracts.md` |
| Shared aliases | `django_apps/asteroid_lab/typing_boundary.py` |
| AGENTS / validation link | Reference manual from validation-routine or manuals index |

### Phase 1 — Replay wire slice (highest ROI)

| Order | Target | Action |
|------:|--------|--------|
| 1 | `overlay_wire_contract.py` | Return `ReplayOverlayCellWire`; single converter authority |
| 2 | `timeline_serialization.py` | Named TypedDict per wire shape; validate on `from_wire` |
| 3 | `lab_timeline_adapter.py` | No hand-built wire dicts; converter calls only |
| 4 | `effective_cell_view.py` | `EffectiveCellWire` + external converter (two-step `to_wire` removal) |
| 5 | Tests | Extend `test_overlay_wire_contract.py`, `test_effective_cell_view.py` |

**Phase 1 non-goals:** `solver_run_lab_summary.py`, shapez_solver graph stack, game-data importers.

### Phase 2 — Service DTO + runtime wires

| Order | Target | Action |
|------:|--------|--------|
| 1 | `service_dtos.py` | Split `config_json`, `frame_payload`, `metric_snapshot_json` into named wires |
| 2 | `runtime_wires/serialize.py`, `deserialize.py` | Per-layer wire TypedDict + envelope |
| 3 | `solver_run_config_keys.py` | Map keys ↔ `SolverRunConfigWire` partial |
| 4 | DTO audit | Fix semantic mismatches (e.g. field names vs actual meaning); contract tests on rename |

### Phase 3 — mypy phased (SHA-20)

```text
1. Keep src/ strict (current)
2. strict: django_apps/asteroid_lab/replay/*
3. strict: wire-related services modules
4. report-only: remaining django_apps/, config/
5. CI hard gate expansion when boundary modules are green
```

Example `pyproject.toml` override:

```toml
[[tool.mypy.overrides]]
module = ["django_apps.asteroid_lab.replay.*"]
strict = true
```

### Phase 4 — Remaining boundaries

- game-data import (`importers/`, `space_transport_layout_*`)
- shapez_solver graph (`recipe_graph_*`) — may warrant separate sub-spec
- lab summary display DTOs (`solver_run_lab_summary.py`)

### Phase 5+ — Gap buckets (typing-zero loop inventory)

**Scan command:** `python scripts/typing_debt_inventory.py`  
**Guard:** `python scripts/check_typing_debt.py` (non-increase until baseline reaches zero)

**Baseline (2026-06-11, pre slice-1):**

| Metric | Count |
|--------|------:|
| `typing.Any` tokens | 1,454 |
| Any-containing `.py` files | 198 |
| Production `dict[str, object]` files | 44 |
| `dict[str, Any]` tokens | 982 |

| Phase | Bucket | Files | Any | Priority |
|------:|--------|------:|----:|----------|
| 5a | `replay/` wire gaps (beyond Phase 1 four) | 12 | 76 | high |
| 5b | `replay/persistent_exterior_overlay` + connector plan | 2 | 6 | **slice-1** |
| 6 | `asteroid_lab/services/` replay compose | 35 | 219 | high |
| 7 | `web/` replay UI | 11 | 91 | high |
| 8 | `snapshots/` + `adapters/` | 10 | 117 | medium |
| 9 | `genetic_sample/` | 6 | 39 | medium |
| 10 | `src/` strict region | 32 | 207 | medium |
| 11 | `shapez_solver/` graph stack | 11+ | 203+ | low (sub-spec) |
| 12 | `game_data/` + `shapez_core/` | 15+ | 80+ | low |

**Parallel escape hatch (same governance):** `dict[str, object]` on production boundaries — 44 files; includes `replay/layer03_segment.py`, `layer04_segment.py`, `layer05_transport_segment.py`, observability post-summary metrics in `src/`.

**Slice-1 (branch `typing-zero/phase-5-persistent-exterior-overlay`):**

- Add `PersistentConnectorOverlayWire` + `planned_connector_overlays_from_wire()`
- Remove `Any` from `typing_boundary.py` (`RawJsonObject` → `JsonObject` / `JsonValue`)
- Tighten `overlay_wire_contract.assert_candidate_overlay_wire_contract` to `Mapping[str, object]`

---

## 6. Testing and validation

### Per-slice regression gate

```bash
python -m pytest tests/unit/asteroid_lab/replay/ -q
python -m pytest tests/unit/asteroid_lab/replay/test_overlay_wire_contract.py -q
python -m pytest tests/unit/asteroid_lab/test_effective_cell_view.py -q
mypy django_apps/asteroid_lab/replay
```

### Acceptance criteria

| Criterion | Verification |
|-----------|--------------|
| Wire key rename breaks compile or test | Converter round-trip unit tests |
| Invalid literal rejected at deserialize | `ReplayTimelineDeserializationError` tests |
| Runtime wire remains replay-projection-only | Existing invariant tests preserved |
| mypy strict on `replay/*` | CI report → hard gate |
| No hand-built overlay dict in production replay path | Ban test (see below) |

### Wire hand-build ban test (future slice)

Exact paths verified in Phase 0 inventory (2026-06-11):

```text
django_apps/asteroid_lab/replay/          (package; converter modules exempt)
django_apps/asteroid_lab/replay/effective_cell_view.py
django_apps/asteroid_lab/services/        (replay compose / timeline only — narrow in test)
django_apps/web/services/replay_frame_cell_lookup.py
```

Note: replay overlay uses `x` / `y` plus optional `layer` (height). There is no `z` key on overlay wire rows.

Allowlist:

```text
tests/ and tests/support/
raw JSON decode/import modules (annotated typing_contracts exception)
typing_boundary.py
*_serialization.py converter modules
```

---

## 7. Risks and non-goals

### Risks

| Risk | Mitigation |
|------|------------|
| TypedDict + dataclass dual maintenance | Wire = projection only; semantic changes touch dataclass + converter |
| `NotRequired` / `total=False` drift | Policy: `total=True` default; document exceptions |
| Phase 1 vs dirty WIP on overlay/effective_cell | Fix converter contract first on current branch |
| Full mypy expansion (900+ errors) | Boundary-only strict; SHA-20 phased |

### Non-goals

- Zero `Any` as KPI
- Hotspot burn-down without schema names
- JSON Schema codegen in Phase 1
- Broad solver `src/` refactor beyond existing strict mypy
- Removing `EffectiveCellView.to_wire()` in the same PR as converter introduction

---

## 8. Example (reference — matches `overlay_cell_to_wire_dict` today)

Replay overlay wire uses **planar `x`/`y`** and optional **`layer`** (map height). There is **no `z` key**.

`transport` and `transport_kind` are both set to **occupancy**; `output_transport_kind` is the **output requirement** family.

```python
from dataclasses import dataclass
from typing import NotRequired, TypedDict

from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell


class ReplayOverlayCellWire(TypedDict):
    """JSON projection for one overlay cell (wire authority)."""

    x: int
    y: int
    kind: str
    transport: str  # occupancy; narrowed in converter
    transport_kind: str  # mirrors transport (occupancy)
    output_transport_kind: str
    tile_type: str
    rotation: int
    layer: NotRequired[int]
    simulation: NotRequired[str]


def overlay_cell_to_wire_dict(cell: ReplayOverlayCell) -> ReplayOverlayCellWire:
    occupancy = str(cell.transport or "none")
    output = str(cell.output_transport_kind or "none")
    wire: ReplayOverlayCellWire = {
        "x": int(cell.x),
        "y": int(cell.y),
        "kind": str(cell.kind),
        "transport": occupancy,
        "transport_kind": occupancy,
        "output_transport_kind": output,
        "tile_type": str(cell.tile_type),
        "rotation": int(cell.rotation),
    }
    if cell.layer is not None:
        wire["layer"] = int(cell.layer)
    # simulation added when tile_type maps to a simulation id (see overlay_wire_contract)
    return wire
```

Semantic authority remains `ReplayOverlayCell` in `timeline_dtos.py` (frozen dataclass).

---

## 9. Approval record

| Section | Status |
|---------|--------|
| §1 Governance | APPROVED |
| §2 Boundary style B+ | APPROVED |
| §3 Authority / forbidden drift | APPROVED |
| §4 Phased rollout | APPROVED |
| §5 Testing / success criteria | APPROVED |
| §6 Risks / non-goals | APPROVED |

Reviewer amendments incorporated: `typing_boundary.py` location, `JsonValue` + `TypeAlias`, TypedDict optional policy, two-step `to_wire` removal, ban-test allowlist, canon path `documents/ai/manuals/`, overlay wire example aligned to `overlay_wire_contract.py`.

### Document canon paths

| Artifact | Canon path |
|----------|------------|
| Typing governance manual | `documents/ai/manuals/typing_contracts.md` |
| This design spec | `documents/superpowers/specs/2026-06-11-any-boundary-typing-design.md` |

Older copies under `documents/knowledge/raw/` are not authority for this workstream.
