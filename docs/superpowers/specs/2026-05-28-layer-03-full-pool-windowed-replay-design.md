# Layer 03 — Full Pool Windowed Replay — Design Spec

**Document type:** Asteroid Lab replay / timeline contract  
**Status:** **APPROVED (2026-05-28)** — Replay Contract Architect  
**Work classification:** contract change · UI change  
**Scope:** `django_apps/asteroid_lab/replay/` · `layers/contracts/layer03_observability.py` · `replay/layer03_segment.py` · `web/static/web/js/asteroid_miner_layout_lab.js`  
**Extends:** [`2026-05-28-central-solver-runtime-replay-assembler-design.md`](2026-05-28-central-solver-runtime-replay-assembler-design.md)

**Supersedes (L3 pool preview only):** `LAYER03_REPLAY_TOP_N`, `top_normal_candidates`, single-frame `layer03_rim_bundle_pool_summary` as overlay carrier, UI copy `Top N of M`.

---

## §1 — Purpose

L3 normal pool may contain hundreds of route-probed candidates. Replay MUST show **every** candidate across bounded **logical windows** without implying algorithmic selection or mid-run interruption.

```text
Candidate cap in replay: FORBIDDEN
Logical window cap: LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS = 10
Physical frame count: MAY exceed 10 when cell-budget sub-split is required
L4 input: unchanged — full RimBundleCandidateSet.normal_candidates
```

---

## §2 — Runtime segment (ordered)

```text
layer03_rim_bundle_scan_begin
layer03_rim_bundle_scan_complete
layer03_rim_bundle_pool_summary              # metrics-only; overlay FORBIDDEN
layer03_rim_bundle_pool_probe_window         # × N logical (+ optional sub-splits)
layer04_rim_placement_begin
...
```

### 2.1 `layer03_rim_bundle_pool_summary` (table of contents)

**MUST NOT** include: candidate footprint, route path, miner/stub, or top-N overlays.

**MUST** include metrics such as:

| Metric | Meaning |
|--------|---------|
| `normal_candidate_count` | Normal pool size |
| `route_probe_succeeded_count` | Probe succeeded count |
| `logical_window_count` | `min(LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS, normal_candidate_count)` |
| `physical_probe_window_frame_count` | Emitted probe_window (+ sub-split) frames |
| `shows_all_candidates` | true iff union of windows covers full sorted pool |
| `pool_preview_overlay_mode` | `"candidate_observation"` |
| `cell_budget_subsplit_count` | Sub-split physical frames beyond logical windows |

### 2.2 `layer03_rim_bundle_pool_probe_window`

Only event type that carries candidate observation overlays (`candidate_miner`, `candidate_transport_stub`, `candidate_route_path`).

Example description: `Probe succeeded candidates 145–216 / 719 · Window 3 / 10`

Metrics (normative): `window_index`, `window_count`, `candidate_start_index`, `candidate_end_index` (1-based inclusive), `chunk_size`, `logical_window_index`, `physical_subwindow_index` (when sub-split), `probe_succeeded_count`, `normal_candidate_count`, `shows_all_candidates`, **`candidate_ids`** (wire: list of strings), **`candidate_count_in_window`**.

**Coverage SoT:** Replay pool preview coverage MUST be proven by **`candidate_ids` exact partition** across probe_window frames (not overlay cell identity).

---

## §3 — Layer03Observability

Replace:

```python
top_normal_candidates: tuple[RouteProbedBundleCandidate, ...]  # REMOVED
```

With:

```python
replay_pool_candidates: tuple[RouteProbedBundleCandidate, ...]
```

- Full sorted normal pool (same sort key as today’s replay ordering).
- Output-only; MUST NOT be read as algorithm input.

Remove `LAYER03_REPLAY_TOP_N` from `replay/replay_limits.py`.

---

## §4 — Windowing algorithm

```python
logical_window_count = min(LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS, normal_candidate_count)
chunk_size = ceil(normal_candidate_count / logical_window_count)  # when count > 0
```

**Coverage (normative):**

```text
All L3 normal candidates MUST appear in exactly one logical pool probe window overlay set.
Replay MUST NOT drop candidates from pool preview.
```

**Cell budget (normative):**

```text
If a logical window’s projected overlay_cells exceed MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
the assembler MAY emit multiple physical frames for that logical window (sub-split).
Sub-splitting MUST preserve candidate coverage and MUST NOT drop candidates.
```

**Assembler map-view ownership (normative):**

```text
structural_base_map_view — reconstruction or post-L2 map; NO L3 candidate overlays
display timeline — probe_window frames may show candidate overlays per window
L4 segment MUST receive structural_base_map_view only (never last probe_window map_view)
```

---

## §5 — UI rendering (candidate observation)

- **No belt/pipe sprites** for candidate observation overlay kinds.
- **`candidate_miner` on cells that already have a base map sprite** (e.g. `asteroid_shape_field`): preserve sprite; apply **ring-only** highlight (`lab-overlay-candidate-miner-ring`).
- **Void / no sprite:** fill tint (`lab-overlay-candidate-miner`).
- **`candidate_transport_stub` / `candidate_route_path`:** void-only tints; cells with an existing asteroid (or other) base sprite MUST be left unchanged (no stub/route overlay on non-miner field tiles).
- Hover / cell detail: `candidate only / not committed`.

---

## §6 — Event registration

Register `layer03_rim_bundle_pool_probe_window` in `replay/event_types.py`, `ReplayEventType`, and `SNAPSHOT_EVENT_TYPES`.

Keep `layer03_rim_bundle_pool_summary` registered; overlay remains forbidden.

---

## §7 — Testing

- Assembler: every `replay_pool_candidates` entry appears in exactly one `probe_window` `candidate_ids` partition. Overlay cells are visual output and MUST NOT be used as coverage SoT.
- Summary frame: `overlay_cells` empty; metrics report `logical_window_count` and coverage flags.
- UI: `candidate_miner` on field cell retains asteroid sprite + ring (regression).
