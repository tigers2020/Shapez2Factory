# PR-RENDER-6 — Replay Frame Compact Adapter (OPTIONAL — Gated)

**Type:** UI change · (optional) contract change
**Depends on:** PR-RENDER-1..5 + LOCK-3 start gate
**Enables:** — (optional payload reduction)
**Branch (suggested):** `feat/lab-renderer-compact-frames`

---

## Start gate (LOCK-3 — hard, no "perf intuition" start)

```text
RENDER-6 may start ONLY if, after RENDER-1..5, at least one holds:
- payload/parse/hydrate remains a dominant measured cost, OR
- replay payload remains >5MB compressed / >15MB decoded, OR
- full/overlay duplication proven by byte accounting.
```

The triggering measurement **must be recorded** in [`baseline-notes.md`](baseline-notes.md) (the
`Run <N> — RENDER-5` block) before any RENDER-6 task begins. If none of the three conditions holds,
RENDER-6 stays **closed** — mark it `[-] skipped` in [`checklist.md`](checklist.md) with the recorded
numbers as the reason.

> Reference signal (pre-work): `lab_perf.jsonl` shows `lab_replay_get` `payload_bytes` ~14MB on the RTTP
> reference. That is a *pre-RENDER* number; the gate is decided on the **post-RENDER-5** measurement, since
> the renderer PRs may already remove the dominant cost.

---

## Goal

Reduce parse/paint work when replay frames carry redundant spatial data, by adapting the viewer to consume
delta-only frames (and, only if byte accounting proves need, emitting delta-only frames from the compose
pipeline).

## Behavior contract

- Adapter is **projection-only**: it changes how the viewer reads frames, not replay semantics (FD-1).
- A frame that already carries only `map_view.cell_delta` skips the `full_map` branch.
- No replay semantic substitution; no metrics/artifact used as algorithm input.
- If backend emission changes, replay schema version + docs are updated together (invariant).

## Non-goals

- No solver algorithm change.
- No change to frame ordering / monotonic `frame_index` (invariant: single replay timeline).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | delta-only frames skip `full_map` branch in `fullMapCellsFromFrame` consumers |
| Create | `tests/unit/asteroid_lab/test_lab_compact_frame_adapter.py` | adapter projection contract |
| Modify (optional) | replay compose pipeline (Django) | emit delta-only frames — only if byte accounting proves need |
| Modify | [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) | document compact-frame contract |

---

## Implementation sketch (viewer-first)

```javascript
// in fullMapCellsFromFrame / collectFrameSpatialTargets:
// when a frame is explicitly delta-only, do not fall back to full_map
function isDeltaOnlyFrame(frame) {
  const mv = frame && frame.map_view;
  return !!(mv && mv.compact === true && Array.isArray(mv.cell_delta));
}
// renderReplayFrame: if isDeltaOnlyFrame(frame), render only cell_delta (token-diff from RENDER-1
// guarantees unchanged cells are untouched)
```

Backend (optional, gated):

```text
compose pipeline emits map_view.compact = true + cell_delta only for non-keyframe frames.
keyframes remain full snapshots so seeking stays O(1) from nearest keyframe.
replay schema_version bumped; asteroid_lab_09 doc updated in same PR.
```

---

## Tasks

- [ ] **Gate (LOCK-3)** — record post-RENDER-5 measurement in `baseline-notes.md`; confirm at least one of
  the three conditions. If none, close RENDER-6 as skipped (document numbers).
- [ ] **Step 1 (TDD) — `test_lab_compact_frame_adapter.py`** (source contract: `isDeltaOnlyFrame`,
  delta-only path does not read `full_map`).
- [ ] **Step 2 — JS adapter:** delta-only frames render `cell_delta` only.
- [ ] **Step 3 — Document** compact-frame contract in `asteroid_lab_09_replay_timeline.md`.
- [ ] **Step 4 (optional) — Django emission** of delta-only frames; bump replay schema version + doc
  together — only if byte accounting proves need (separate commit inside this PR).
- [ ] **Step 5 — Verify** payload/parse reduction; append `Run <N> — RENDER-6` block to `baseline-notes.md`.
- [ ] **Step 6 — Verify + lint.**

---

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_compact_frame_adapter.py -v
python -m pytest tests/unit/asteroid_lab/replay/ -v
python -m pytest tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py -v
python -m ruff check tests/unit/asteroid_lab
```

If backend emission changes: `python -m mypy django_apps config src` + replay schema tests.

## Risks

- `invariant:` no replay semantic substitution; adapter is projection-only (asteroid-lab-invariants Replay row).
- `invariant:` keyframes stay full snapshots so seeking is correct; monotonic `frame_index` preserved.
- `assumption:` PR-CLI-5 JSONL streaming synergy — compact frames reduce per-line parse cost; coordinate if both land.
- `uncertain:` if the gate is not met, this PR is intentionally not done — that is the correct outcome (LOCK-3).

## Done criteria

- Either: gate met → delta-only adapter (and optional emission) lands with recorded payload/parse
  reduction and schema/doc updated; OR: gate not met → RENDER-6 closed as `[-] skipped` in `checklist.md`
  with the recorded numbers as justification (LOCK-3).
