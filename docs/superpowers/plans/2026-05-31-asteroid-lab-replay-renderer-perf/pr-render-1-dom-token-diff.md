# PR-RENDER-1 — DOM Token-Diff Paint (P0 + P1)

**Type:** UI change · implementation change
**Depends on:** PR-RENDER-0 (baseline closed)
**Enables:** PR-RENDER-2, PR-RENDER-3, PR-RENDER-6
**Branch (suggested):** `feat/lab-renderer-token-diff`

---

## Goal

Touch only the cells whose visual token changed between frames. Eliminate the "reset everything, repaint
everything" pattern in the DOM paint path so a frame change updates changed cells only (Guard R1, R6).

## Behavior contract

- Painting a frame whose visible cells are visually identical to the previous frame touches **0** DOM cells.
- Painting a changed frame touches at most `changed token count + bounded housekeeping` cells.
- `img.src` is written only when a cell's render token changes.
- Bundle-bridge DOM is not created/removed every frame (token-gated or pooled; full pooling lands in RENDER-3).
- Visual output is identical to current behavior for every frame (regression hooks preserved, FD-3/FD-4).

## Non-goals

- No layout read/write split (RENDER-2).
- No canvas (RENDER-4/5).
- No data-shape change (RENDER-6).

---

## Current code (entry points)

- `renderFullMapCells(baseClasses, domCells, cells, resolveCellIndex, frame)` — L1296–1339, writes
  `el.className` + sprite + HUD for every cell every call.
- `renderReplayFrame` → `resetForFrame()` then `renderFullMapReplayFrame` — L1918–1971.
- `resetDomCellAtIndex` / `resetGridBase` — L1816–1846.
- `applyLabCellSprite` — L409–436 (writes `img.src` unconditionally).
- `replayFrameNeedsFullGridReset` — L948–971 (keyframe + ≥15% threshold forces full reset).
- `LAB_REPLAY_FULL_RESET_CELL_THRESHOLD = 64` — L120.

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | token-diff skip in paint path; sprite write guard; perf-debug counter |
| Create | `tests/unit/asteroid_lab/test_lab_renderer_token_diff.py` | source contract for token helper + skip-on-equal |
| Modify | `tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py` | remove xfail; flag now present |

---

## Implementation sketch

```javascript
// closure state inside init() (alongside replayPaintedCellIndices)
const renderedTokenByKey = new Map(); // key: cell DOM index, value: token string
let labPerfTouchedCells = 0;          // debug counter (data-lab-perf-debug)

function cellRenderToken(cell, frame) {
  const ck = overlayCellKind(cell);
  const rot = cell.rotation ?? "";
  const role = cell.overlay_role ?? "";
  const sprite = labSpriteRelpathForCell(cell, frame) ?? "";
  const tone = toneForFullMapCell(cell, frame) ?? "";
  return ck + "|" + role + "|" + rot + "|" + sprite + "|" + tone;
}

function renderFullMapCells(baseClasses, domCells, cells, resolveCellIndex, frame) {
  if (!Array.isArray(cells)) return;
  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i];
    if (!cell || typeof cell !== "object") continue;
    const idx = resolveCellIndex(cell);
    if (idx == null || idx < 0 || idx >= domCells.length) continue;

    const token = cellRenderToken(cell, frame);
    if (renderedTokenByKey.get(idx) === token) continue; // R1: skip unchanged cell

    // ... existing className / HUD / sprite apply (unchanged) ...
    renderedTokenByKey.set(idx, token);
    labPerfTouchedCells++;
  }
}
```

Token-map invalidation (so skip is correct):

```javascript
function resetDomCellAtIndex(domCells, baseClasses, index) {
  // ... existing reset ...
  renderedTokenByKey.delete(index); // forget token so next paint re-applies
}

// on surface remount / full reset / keyframe: renderedTokenByKey.clear()
```

Sprite write guard (only when token changed — already gated by the `continue` above, but make
`applyLabCellSprite` idempotent on `img.src`):

```javascript
function applyLabCellSprite(el, cell, frame) {
  // ... compute rel ...
  const nextSrc = base + rel;
  if (img.getAttribute("src") === nextSrc) {
    // still apply rotation if needed, but skip src write
  } else {
    img.src = nextSrc;
  }
}
```

Debug counter exposure:

```javascript
// behind lab-root[data-lab-perf-debug="1"]
if (labPerfDebugEnabled()) {
  console.debug("[lab-perf] touched_cells", labPerfTouchedCells, "frame", replayArrayIndex);
}
labPerfTouchedCells = 0; // reset per applyFrame
```

> Keep the existing `useIncremental` / `replayPaintedCellIndices` path; token-diff composes with it
> (incremental reset clears tokens for touched indices only). Revisit `LAB_REPLAY_FULL_RESET_CELL_THRESHOLD`
> only if token-diff makes the 15% rule redundant — change threshold in a separate step with a recorded
> before/after.

---

## Tasks

- [ ] **Step 1 (TDD) — `test_lab_renderer_token_diff.py`.** Source contract.

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_token_helper_present() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function cellRenderToken(" in src
    assert "renderedTokenByKey" in src


def test_render_full_map_cells_skips_unchanged_token() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function renderFullMapCells(")
    assert idx >= 0
    body = src[idx : idx + 1500]
    assert "cellRenderToken(" in body
    assert "renderedTokenByKey.get(" in body
    assert "continue" in body


def test_reset_clears_token() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function resetDomCellAtIndex(")
    assert idx >= 0
    body = src[idx : idx + 400]
    assert "renderedTokenByKey.delete(" in body


def test_sprite_src_write_is_guarded() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function applyLabCellSprite(")
    assert idx >= 0
    body = src[idx : idx + 900]
    assert 'getAttribute("src")' in body
```

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_renderer_token_diff.py -v`
Expected: FAIL (helpers not present yet).

- [ ] **Step 2 — Implement `cellRenderToken` + `renderedTokenByKey` skip** in `renderFullMapCells`.
- [ ] **Step 3 — Token-map invalidation** in `resetDomCellAtIndex` (`delete`) + `renderedTokenByKey.clear()`
  on surface remount / full reset / keyframe.
- [ ] **Step 4 — Guard sprite `img.src` write** by current src compare.
- [ ] **Step 5 — Touched-cell debug counter** behind `data-lab-perf-debug`; remove xfail in
  `test_lab_renderer_perf_debug_flag.py`.
- [ ] **Step 6 (LOCK-2) — Verify DOM-touch Done criteria** on the RTTP 88-frame fixture; append a
  `Run <N> — RENDER-1` block to `baseline-notes.md` with touched-cell numbers.
- [ ] **Step 7 — Verify + lint.**

---

## Done criteria (LOCK-2 — DOM-touch count, NOT speed)

```text
[ ] unchanged frame: touched cell DOM count == 0
[ ] changed frame: touched cell DOM count <= changed visual token count + bounded housekeeping
[ ] sprite img.src changes only when the cell render token changes
[ ] bundle bridge DOM is not created/removed every frame (token-gated or pooled)
```

These touch-count invariants are the acceptance gate. Timing improvements are reported afterward against
`baseline-notes.md` but **cannot substitute** for the touch-count criteria.

**Measurement:** `data-lab-perf-debug` touched-cell counter; compare unchanged vs changed frames on the
RTTP 88-frame fixture.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_renderer_token_diff.py tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py -v
python -m ruff check tests/unit/asteroid_lab
```

## Risks

- `invariant:` visual output must not change — diff against current frames; keep regression hooks (FD-4).
- `uncertain:` token must include every visual axis (kind/role/rotation/sprite/tone); a missing axis = stale cell. Add the axis to `cellRenderToken` and a regression test if found.
- `invariant:` island-local coords unaffected (FD-2).

## Done criteria

- Four LOCK-2 invariants satisfied; token-diff + perf-debug tests green; integration web tests green;
  RENDER-1 baseline block recorded.
