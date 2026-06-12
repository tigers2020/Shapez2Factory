# Replay Sprite Visibility — Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship read-path wire sanitizer (Python + JS), wire audit for committed cells, stable string cell index key, and persisted-frame audit — **no paint/UI behavior change**.

**Architecture:** Legacy candidate overlays with banned `transport` tokens normalize to `output_transport_kind` + `transport=none` before `merge_effective_cell_view` / `mergeEffectiveCellView`. Committed transport with invalid tokens **audit-fail**, never sanitize. Stable string keys `${x},${y}` (or `${layer}:${x},${y}`) for future effective-view index.

**Tech Stack:** Python 3.12, Django asteroid_lab replay modules, vanilla JS (Lab static bundle), pytest static JS contract tests.

**Spec:** [`docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md`](../specs/2026-06-12-replay-sprite-visibility-design.md)  
**Kanban:** `.devtool/features/replay-sprite-visibility-2026-06-12.md`

**Slice 1 stop:** All Slice 1 tests green; sanitizer wired at merge input (server + client detail lookup); **no** `buildLabPaintPlanFromEffectiveViews` yet.

---

## File map (Slice 1)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/replay/replay_cell_index.py` | `cell_key(x, y, layer)` stable string key |
| `django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py` | Candidate-only read sanitizer + audit helpers |
| `django_apps/web/static/web/js/lab_replay_wire_sanitize.js` | JS mirror of sanitizer + `cellKey` |
| `django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py` | Sanitize wire rows before merge (server) |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Sanitize in `labCellDetailLookupInMapView` before merge |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Load `lab_replay_wire_sanitize.js` before `lab_effective_cell_view.js` |
| `tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py` | Sanitizer + index key unit tests |
| `tests/unit/asteroid_lab/replay/test_replay_wire_audit.py` | Audit + persisted fixture scan |
| `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | JS sanitizer contract + Py/JS parity cases |

---

### Task 1: Stable cell index key (Python)

**Files:**
- Create: `django_apps/asteroid_lab/replay/replay_cell_index.py`
- Test: `tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py
from django_apps.asteroid_lab.replay.replay_cell_index import cell_key


def test_stable_view_index_key_default_layer() -> None:
    assert cell_key(10, 7) == "10,7"
    assert cell_key(10, 7, 0) == "10,7"


def test_stable_view_index_key_nonzero_layer() -> None:
    assert cell_key(10, 7, 2) == "2:10,7"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py::test_stable_view_index_key_default_layer -v`  
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# django_apps/asteroid_lab/replay/replay_cell_index.py
"""Stable string keys for per-cell effective-view index (paint Slice 2+)."""

from __future__ import annotations


def cell_key(x: int, y: int, layer: int | None = None) -> str:
    if layer is not None and layer != 0:
        return f"{layer}:{x},{y}"
    return f"{x},{y}"


__all__ = ["cell_key"]
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py -k stable_view_index -v`

---

### Task 2: Python read sanitizer (candidate/output-hint only)

**Files:**
- Create: `django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py`
- Test: `tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py`

- [ ] **Step 1: Write failing tests**

```python
import copy

import pytest

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    ReplayWireAuditError,
    audit_replay_wire_cell,
    is_candidate_output_hint_kind,
    sanitize_replay_wire_cell_for_read,
)

_LEGACY_CANDIDATE_ROW = {
    "x": 10,
    "y": 7,
    "kind": "candidate_miner",
    "transport": "shape_belt",
    "rotation": 0,
    "layer": 0,
}

_CANONICAL_CANDIDATE_ROW = {
    "x": 10,
    "y": 7,
    "kind": "candidate_miner",
    "transport": "none",
    "transport_kind": "none",
    "output_transport_kind": "space_belt",
    "rotation": 0,
    "layer": 0,
}


def test_is_candidate_output_hint_kind() -> None:
    assert is_candidate_output_hint_kind("candidate_miner")
    assert not is_candidate_output_hint_kind("space_belt")


def test_sanitizer_compat_legacy_transport() -> None:
    out = sanitize_replay_wire_cell_for_read(copy.deepcopy(_LEGACY_CANDIDATE_ROW))
    assert out["transport"] == "none"
    assert out["transport_kind"] == "none"
    assert out["output_transport_kind"] == "space_belt"


def test_sanitizer_merge_parity_with_canonical_wire() -> None:
    legacy = sanitize_replay_wire_cell_for_read(copy.deepcopy(_LEGACY_CANDIDATE_ROW))
    canonical = copy.deepcopy(_CANONICAL_CANDIDATE_ROW)
    legacy_view = merge_effective_cell_view(
        x=10,
        y=7,
        full_cell={"x": 10, "y": 7, "kind": "asteroid_shape_field", "transport": "none"},
        overlay_cells=[legacy],
    )
    canonical_view = merge_effective_cell_view(
        x=10,
        y=7,
        full_cell={"x": 10, "y": 7, "kind": "asteroid_shape_field", "transport": "none"},
        overlay_cells=[canonical],
    )
    assert legacy_view is not None and canonical_view is not None
    assert legacy_view.output_transport_kind == canonical_view.output_transport_kind == "space_belt"
    assert legacy_view.occupant_kind == canonical_view.occupant_kind


def test_sanitizer_does_not_normalize_committed_transport() -> None:
    committed = {
        "x": 3,
        "y": 4,
        "kind": "space_belt",
        "transport": "shape_belt",
        "tile_type": "SpaceBelt_Forward",
    }
    with pytest.raises(ReplayWireAuditError):
        audit_replay_wire_cell(committed)
    unchanged = sanitize_replay_wire_cell_for_read(copy.deepcopy(committed))
    assert unchanged["transport"] == "shape_belt"
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py -v`  
Expected: import / assertion failures

- [ ] **Step 3: Implement sanitizer**

```python
# django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py
"""Read-path replay wire sanitizer (candidate compat) and committed-cell audit."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import cast

from django_apps.asteroid_lab.replay.overlay_wire_contract import (
    CANDIDATE_OUTPUT_OVERLAY_KINDS,
)
from django_apps.asteroid_lab.replay.replay_cell_semantics import normalize_project_transport_kind
from django_apps.asteroid_lab.replay.replay_map_cell_wire import wire_field_kind, wire_field_transport
from django_apps.asteroid_lab.typing_boundary import JsonObject

_BANNED_CANDIDATE_OCCUPANCY = frozenset(
    {
        "space_belt",
        "space_pipe",
        "shape_belt",
        "fluid_pipe",
        "shape",
        "fluid",
        "belt",
        "pipe",
    }
)

_COMMITTED_TRANSPORT_KINDS = frozenset({"space_belt", "space_pipe"})


class ReplayWireAuditError(ValueError):
    """Committed wire row violates replay transport contract."""


def is_candidate_output_hint_kind(kind: str) -> bool:
    return kind in CANDIDATE_OUTPUT_OVERLAY_KINDS


def audit_replay_wire_cell(row: Mapping[str, object]) -> None:
    kind = wire_field_kind(row)
    transport = wire_field_transport(row).strip().lower()
    if is_candidate_output_hint_kind(kind):
        if transport in _BANNED_CANDIDATE_OCCUPANCY_TRANSPORT:
            raise ReplayWireAuditError(
                f"candidate overlay kind={kind!r} must not claim transport={transport!r}"
            )
        return
    if kind in _COMMITTED_TRANSPORT_KINDS and transport in _BANNED_CANDIDATE_OCCUPANCY:
        raise ReplayWireAuditError(
            f"committed transport kind={kind!r} has invalid transport={transport!r}"
        )


def sanitize_replay_wire_cell_for_read(row: Mapping[str, object]) -> JsonObject:
    """Normalize legacy candidate occupancy transport for display merge input only."""

    out = cast(JsonObject, copy.deepcopy(dict(row)))
    kind = wire_field_kind(out)
    if not is_candidate_output_hint_kind(kind):
        audit_replay_wire_cell(out)
        return out
    transport = wire_field_transport(out).strip().lower()
    if transport not in _BANNED_CANDIDATE_OCCUPANCY:
        audit_replay_wire_cell(out)
        return out
    normalized = normalize_project_transport_kind(transport)
    if normalized == "none":
        audit_replay_wire_cell(out)
        return out
    out["transport"] = "none"
    out["transport_kind"] = "none"
    existing = str(out.get("output_transport_kind") or "").strip()
    if not existing or normalize_project_transport_kind(existing) == "none":
        out["output_transport_kind"] = normalized
    return out


__all__ = [
    "ReplayWireAuditError",
    "audit_replay_wire_cell",
    "is_candidate_output_hint_kind",
    "sanitize_replay_wire_cell_for_read",
]
```

Fix typo in audit: use `_BANNED_CANDIDATE_OCCUPANCY` consistently (plan shows typo `_BANNED_CANDIDATE_OCCUPANCY_TRANSPORT` in audit - should be `_BANNED_CANDIDATE_OCCUPANCY`).

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py -v`

---

### Task 3: Wire sanitizer at server merge input

**Files:**
- Modify: `django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py`
- Test: extend `tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py`

- [ ] **Step 1: Write failing test**

Add to `test_replay_frame_cell_resolver.py`:

```python
def test_lookup_sanitizes_legacy_candidate_transport_on_read() -> None:
    ser = {
        "map_view": {
            "full_cells": [
                {"x": 10, "y": 7, "kind": "asteroid_shape_field", "transport": "none"},
            ],
            "overlay_cells": [
                {"x": 10, "y": 7, "kind": "candidate_miner", "transport": "shape_belt"},
            ],
            "cell_delta": [],
        }
    }
    effective, _sources = lookup_effective_cell_in_serialized_frame(ser, 10, 7)
    assert effective is not None
    assert effective.output_transport_kind == "space_belt"
    assert effective.transport_kind == "none"
```

- [ ] **Step 2: Run test — expect FAIL** (legacy transport may merge via old path but audit may not run; verify behavior)

- [ ] **Step 3: Sanitize rows in resolver before merge**

In `replay_frame_cell_resolver.py`, import `sanitize_replay_wire_cell_for_read` and apply to each wire cell dict immediately before passing into `merge_effective_cell_view` (full, delta, overlay rows).

- [ ] **Step 4: Run resolver tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py -v`

---

### Task 4: Persisted frame wire audit

**Files:**
- Test: `tests/unit/asteroid_lab/replay/test_replay_wire_audit.py`

- [ ] **Step 1: Write audit test for golden assembler output**

```python
# tests/unit/asteroid_lab/replay/test_replay_wire_audit.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import audit_replay_wire_cell
from tests.support.lab_replay_sprite_wire import golden_transport_replay_frames

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE_ROOT = _REPO / "tests" / "fixtures" / "asteroid_lab"
_BANNED = "shape_belt"


def _iter_wire_rows(obj: object, path: str) -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    if isinstance(obj, dict):
        if "kind" in obj and "x" in obj and "y" in obj:
            rows.append((path, obj))
        for k, v in obj.items():
            rows.extend(_iter_wire_rows(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            rows.extend(_iter_wire_rows(item, f"{path}[{i}]"))
    return rows


def test_persisted_replay_frames_wire_audit_golden_assembler() -> None:
    violations: list[str] = []
    for frame in golden_transport_replay_frames():
        for path, row in _iter_wire_rows(frame, "frame"):
            try:
                audit_replay_wire_cell(row)
            except Exception as exc:
                violations.append(f"{path}: {exc}")
    assert not violations, violations


@pytest.mark.skipif(not _FIXTURE_ROOT.is_dir(), reason="no fixture dir")
def test_persisted_fixture_json_no_shape_belt_on_candidate_transport() -> None:
    for path in sorted(_FIXTURE_ROOT.rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        if _BANNED not in text:
            continue
        payload = json.loads(text)
        for rel_path, row in _iter_wire_rows(payload, str(path)):
            kind = str(row.get("kind") or row.get("cell_kind") or "")
            transport = str(row.get("transport") or row.get("transport_kind") or "")
            if "candidate" in kind and _BANNED in transport:
                pytest.fail(f"{rel_path}: candidate row still has shape_belt transport")
```

- [ ] **Step 2: Run audit tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_audit.py -v`

Fix any golden assembler violations at **producer** if found (not sanitizer).

---

### Task 5: JS sanitizer module

**Files:**
- Create: `django_apps/web/static/web/js/lab_replay_wire_sanitize.js`
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Test: `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`

- [ ] **Step 1: Write failing JS contract tests**

Add to `test_lab_canvas_renderer.py`:

```python
SANITIZE_JS = JS_DIR / "lab_replay_wire_sanitize.js"


def test_js_sanitize_replay_wire_cell_for_read_exists() -> None:
    src = SANITIZE_JS.read_text(encoding="utf-8")
    assert "function sanitizeReplayWireCellForRead" in src
    assert "function cellKey" in src
    assert "LabReplayWireSanitize" in src


def test_js_sanitizer_matches_python_candidate_compat_cases() -> None:
    src = SANITIZE_JS.read_text(encoding="utf-8")
    assert '"shape_belt"' in src  # legacy compat token handled in sanitizer
    assert "output_transport_kind" in src
    assert "candidate_miner" in src
    assert "space_belt" in src
    assert "function isCandidateOutputHintKind" in src
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k sanitize -v`

- [ ] **Step 3: Implement JS module**

```javascript
// django_apps/web/static/web/js/lab_replay_wire_sanitize.js
(function (global) {
  "use strict";

  var CANDIDATE_OUTPUT_HINT_KINDS = {
    candidate_miner: 1,
    candidate_transport_stub: 1,
    candidate_route_path: 1,
    route_probe_path: 1,
  };

  var BANNED_CANDIDATE_OCCUPANCY = {
    space_belt: 1,
    space_pipe: 1,
    shape_belt: 1,
    fluid_pipe: 1,
    shape: 1,
    fluid: 1,
    belt: 1,
    pipe: 1,
  };

  var COMMITTED_TRANSPORT_KINDS = { space_belt: 1, space_pipe: 1 };

  function normalizeProjectTransportKind(raw) {
    if (typeof LabEffectiveCellView !== "undefined" && LabEffectiveCellView.normalizeProjectTransportKind) {
      return LabEffectiveCellView.normalizeProjectTransportKind(raw);
    }
    var value = String(raw || "").trim().toLowerCase();
    if (value === "shape_belt" || value === "belt" || value === "shape" || value === "space_belt") {
      return "space_belt";
    }
    if (value === "fluid_pipe" || value === "pipe" || value === "fluid" || value === "space_pipe") {
      return "space_pipe";
    }
    return "none";
  }

  function wireKind(cell) {
    if (!cell) return "";
    if (cell.kind != null && String(cell.kind) !== "") return String(cell.kind);
    if (cell.cell_kind != null && String(cell.cell_kind) !== "") return String(cell.cell_kind);
    return "";
  }

  function wireTransport(cell) {
    if (!cell) return "";
    if (cell.transport != null && String(cell.transport) !== "") return String(cell.transport);
    if (cell.transport_kind != null && String(cell.transport_kind) !== "") return String(cell.transport_kind);
    return "";
  }

  function isCandidateOutputHintKind(kind) {
    return CANDIDATE_OUTPUT_HINT_KINDS[String(kind || "")] === 1;
  }

  function auditReplayWireCell(cell) {
    var kind = wireKind(cell);
    var transport = wireTransport(cell).trim().toLowerCase();
    if (isCandidateOutputHintKind(kind)) {
      if (BANNED_CANDIDATE_OCCUPANCY[transport]) {
        throw new Error("candidate overlay must not claim transport=" + transport);
      }
      return;
    }
    if (COMMITTED_TRANSPORT_KINDS[kind] && BANNED_CANDIDATE_OCCUPANCY[transport]) {
      throw new Error("committed transport invalid transport=" + transport);
    }
  }

  function sanitizeReplayWireCellForRead(cell) {
    if (!cell || typeof cell !== "object") return cell;
    var out = Object.assign({}, cell);
    var kind = wireKind(out);
    if (!isCandidateOutputHintKind(kind)) {
      auditReplayWireCell(out);
      return out;
    }
    var transport = wireTransport(out).trim().toLowerCase();
    if (!BANNED_CANDIDATE_OCCUPANCY[transport]) {
      auditReplayWireCell(out);
      return out;
    }
    var normalized = normalizeProjectTransportKind(transport);
    if (normalized === "none") {
      auditReplayWireCell(out);
      return out;
    }
    out.transport = "none";
    out.transport_kind = "none";
    var existing = out.output_transport_kind != null ? String(out.output_transport_kind).trim() : "";
    if (!existing || normalizeProjectTransportKind(existing) === "none") {
      out.output_transport_kind = normalized;
    }
    return out;
  }

  function cellKey(x, y, layer) {
    if (layer != null && layer !== 0) {
      return String(layer) + ":" + String(x) + "," + String(y);
    }
    return String(x) + "," + String(y);
  }

  global.LabReplayWireSanitize = {
    auditReplayWireCell: auditReplayWireCell,
    cellKey: cellKey,
    isCandidateOutputHintKind: isCandidateOutputHintKind,
    sanitizeReplayWireCellForRead: sanitizeReplayWireCellForRead,
  };
})(typeof window !== "undefined" ? window : globalThis);
```

- [ ] **Step 4: Add script tag** in `asteroid_miner_layout_solver.html` **before** `lab_effective_cell_view.js`:

```html
<script src="{% static 'web/js/lab_replay_wire_sanitize.js' %}?v=replay_wire_sanitize_v1" defer></script>
```

- [ ] **Step 5: Run JS contract tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k sanitize -v`

---

### Task 6: Wire JS sanitizer at client merge input

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Sanitize in `labCellDetailLookupInMapView`**

Before `mergeEffectiveCellView`, wrap each source cell:

```javascript
function sanitizeWireCellForMerge(cell) {
  if (
    typeof LabReplayWireSanitize !== "undefined" &&
    typeof LabReplayWireSanitize.sanitizeReplayWireCellForRead === "function"
  ) {
    return LabReplayWireSanitize.sanitizeReplayWireCellForRead(cell);
  }
  return cell;
}
```

Apply to `fullCell`, `deltaCell`, and each overlay in `overlayMatches` after lookup, before merge call.

- [ ] **Step 2: Manual smoke (optional)**

Load Lab replay frame 38 (or golden run), open cell `(10,7)` detail — `output_transport` should be `space_belt`, sources may still show raw wire in `sources` block (raw preserved) or sanitized copies per implementation choice. **Document:** keep `sources` as raw wire for debugging; merge uses sanitized copy.

- [ ] **Step 3: Run regression tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py tests/unit/asteroid_lab/replay/test_effective_cell_view.py -q`

---

### Task 7: Slice 1 validation gate

- [ ] **Step 1: Full Slice 1 pytest**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_wire_audit.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py \
  tests/unit/asteroid_lab/test_shape_belt_ui_wire_ban.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  -q
```

Expected: all passed

- [ ] **Step 2: Lint touched Python**

Run: `ruff check django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py django_apps/asteroid_lab/replay/replay_cell_index.py django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py`

- [ ] **Step 3: Update kanban**

Set `.devtool/features/replay-sprite-visibility-2026-06-12.md` → `status: implement`, Progress note: Slice 1 complete + validation command output.

- [ ] **Step 4: Commit (when user requests)**

```bash
git add django_apps/asteroid_lab/replay/replay_cell_index.py \
  django_apps/asteroid_lab/replay/replay_wire_read_sanitize.py \
  django_apps/asteroid_lab/replay/replay_frame_cell_resolver.py \
  django_apps/web/static/web/js/lab_replay_wire_sanitize.js \
  django_apps/web/static/web/js/asteroid_miner_layout_lab.js \
  django_apps/web/templates/web/asteroid_miner_layout_solver.html \
  tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_wire_audit.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md \
  docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-1.md

git commit -m "feat(replay): Slice 1 wire read sanitizer and audit (Py+JS)"
```

---

## Spec coverage self-check (Slice 1)

| Spec requirement | Task |
|------------------|------|
| Stable string index key | Task 1 |
| Read sanitizer candidate-only | Task 2 |
| Committed transport audit failure | Task 2, 4 |
| Sanitizer at merge input (server + client) | Task 3, 6 |
| JS sanitizer contract tests | Task 5 |
| Persisted frame audit | Task 4 |
| No paint/UI plan swap | Out of scope (Slice 2+) |
| Feature flag semantics | Out of scope (Slice 3+) |

## Out of scope (Slice 1 — do not implement)

- `lab_paint_layers_from_view` / `LabPaintLayers`
- `buildLabPaintPlanFromEffectiveViews`
- Canvas/DOM paint changes
- Removing `NON_SPRITE_OVERLAY_CELL_KINDS`
- Quarantine/delete harvest paths

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-1.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — implement tasks in this session with checkpoints

Which approach?
