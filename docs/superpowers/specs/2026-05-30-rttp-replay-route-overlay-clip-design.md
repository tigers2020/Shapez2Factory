# RTTP Replay Route Overlay Clip — Design Spec

**Status:** APPROVED (2026-05-30 — rev2: Option A + projected coords; rev3: dynamic render envelope, not fixed island bbox)  
**Owner:** asteroid-lab / replay-projection  
**Work classification:** contract change · implementation change  
**Scope:** replay projection-only (Lab compose clip policy)  
**Decision:** **Approach 1** — dual-channel clip in `lab_rttp_snapshot_compose.py` (equipment anchor-only; transport/route bbox-only).

**Next:** [`2026-05-30-rttp-replay-route-overlay-clip.md`](../plans/2026-05-30-rttp-replay-route-overlay-clip.md) implementation plan.

**Related (CANON / ACTIVE):**

- [`2026-05-26-rttp-confirmed-placement-footprint-design.md`](2026-05-26-rttp-confirmed-placement-footprint-design.md) — PR-1 placement overlay rows (`tile_type`, miner sprites)
- [`documents/ai/lab_map_rendering_contract.md`](../../../documents/ai/lab_map_rendering_contract.md) — bbox must include `overlay_cells` for grid layout
- [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md) — replay output-only; solver must not read replay
- [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md) — commit-time re-probe is proof; selection order is provisional

**Out of scope (this PR):**

- Selection UX metrics (`commit_order_count`, `committed_count`, `conflict_count` in inspector) — follow-up UX track
- Commit success rate / re-probe tuning
- Turn/merger/splitter belt synthesis (PR-1b)
- Stray / disconnected transport overlay suppression (connected-component guard) — follow-up hardening track

---

## Problem

After RTTP `incremental_commit`, the **commit domain snapshot** frame shows **confirmed miner/extension sprites** on the Lab map but **no committed belts / route path / FOT / output stub** overlays, while the frame `description` still lists `committed_ids` and `reserved_route_cells` textually.

**Observed pattern (user-confirmed):**

| Frame | Map | Inspector text |
|-------|-----|----------------|
| Selection (`RTTP genome selection snapshot`) | Many provisional placement overlays | `commit_order` (full genome order) |
| Commit (`RTTP commit domain snapshot`) | Equipment visible; **routes missing** | `committed_ids` + `commit_order` + conflicts |

**Root cause (code):**

`project_rttp_row_to_product_frame` calls `clip_overlay_cells_to_base_map_domain`, which keeps overlay cells **only** when `(x, y)` is in **mineable field anchors** derived from `full_cells` (`asteroid_*`, `mineable`). Committed route cells from `build_confirmed_placement_overlay_rows` → `_route_rows(reserved_route_cells)` lie on **void / trunk** coordinates outside those anchors and are **silently dropped** before Lab JS renders `overlay_cells`.

This is a **replay projection bug**, not a solver or commit logic failure.

```text
Replay is output-only.
The solver must never read replay to decide the next step.
```

---

## Goal

```text
RTTP compose (lab_rttp_snapshot_compose)
  → dual-channel clip
  → equipment = anchor-only clip
  → transport/route = dynamic replay render envelope (not fixed island bbox)
  → no incremental_commit / selection / route_probe changes
```

**Success criteria:**

1. On commit snapshot frames, `map_view.overlay_cells` includes `route.committed_path` (and confirmed FOT/stub rows) when those coords are in the dynamic render envelope defined below.
2. Equipment rows **never** appear on void cells outside mineable anchors (no regression).
3. **Bbox is dynamic:** committed transport/route/FOT/stub coords may extend the render envelope beyond asteroid `full_cells`, including exterior void connector routes. Stray suppression is not done by fixed bbox clipping in v1; it is deferred to a connected-component / domain hardening track.

---

## Algorithm non-goals (MUST)

```text
No solver changes.
No incremental_commit changes.
No candidate selection changes.
No route synthesis changes.
No validation repair.
Replay/output projection only.
```

---

## Approved architecture

### Touch surface

| Module | Change |
|--------|--------|
| `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py` | Dual-channel clip, classification helper, bbox helpers |
| `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py` | Normative clip tests (see § Tests) |
| `documents/ai/lab_map_rendering_contract.md` | Short cross-reference to dual-channel RTTP clip (optional, recommended) |

**No changes:**

- `incremental_commit`, `placement_overlay_projection` (payload generation stays as-is)
- `asteroid_miner_layout_lab.js` (wire rows already carry `tile_type` per PR-1)
- `rttp_replay_diagnostics` (except if tests need fixture imports only)

### Data flow

```text
:rttp row cell_overlay_json.cells (raw overlay, pre-clip)
  → project_rttp_row_to_product_frame
       → lab_anchors := mineable field anchors from full_cells
       → project every overlay/full_cell (ox,oy) → lab_xy (single coord frame)
       → lab_render_bbox := dynamic render envelope =
            bounds(projected full_cells ∪ projected raw overlay)  # pre-clip; expands for exterior routes
       → known_route_render_domain :=
            projected_full_cell_coords ∪ projected_transport_or_route_overlay_coords
       → clip_overlay_cells_to_base_map_domain(raw, base)
            → per row: lab_xy := project(ox, oy)
                 transport → keep iff lab_xy in lab_render_bbox AND lab_xy in known_route_render_domain
                 equipment → keep iff lab_xy in lab_anchors
  → map_view.overlay_cells (product frame)
  → Lab renderReplayFrame (unchanged)
```

---

## Normative clip contract

### 1. Clip classification helper (MUST)

String matching MUST NOT be duplicated across call sites. A single exported helper classifies overlay rows:

```python
def is_transport_or_route_overlay_row(row: Mapping[str, Any]) -> bool:
    ...
```

**Returns `True` iff any of:**

```text
cell_kind in {"space_belt", "space_pipe"}
OR kind startswith "route."
OR overlay_semantic_kind startswith "route."
OR kind in {
  "placement.confirmed_fixed_output_transport",
  "placement.confirmed_output_stub",
}
OR overlay_semantic_kind in {
  "placement.confirmed_fixed_output_transport",
  "placement.confirmed_output_stub",
}
```

**Notes:**

- `route.committed_path` is covered by `startswith "route."`.
- Confirmed FOT/stub semantics from PR-1 (`placement_overlay_projection`) are explicitly included so they use the transport channel even when `cell_kind` is `space_belt` / `space_pipe`.
- **Selection / candidate** placement rows (`placement.selected_*`, `placement.candidate_*`) remain **equipment channel** (anchor-only) unless they match the transport rules above (FOT/stub rows on confirmed commit payload only use the confirmed placement kind names).

### 2. Coordinate frame (MUST)

```text
bbox, known_route_render_domain, and clip membership MUST use the same projected lab (x, y).
```

For each wire overlay row and each `full_cells` entry, compute:

```python
lab_xy = project_overlay_coord_to_lab_xy(ox, oy, lab_anchors)
# (ox, oy) if already in lab_anchors else lab_xy_from_replay_cell(ox, oy)
```

**Forbidden:** building bbox/domain from raw `(ox, oy)` while testing membership on projected `lab_xy` (breaks when projection is non-identity).

### 3. Dynamic render envelope (`lab_render_bbox`) (MUST — no post-clip bbox)

`lab_render_bbox` is **not** a fixed asteroid / mineable clipping boundary. It is the **dynamic replay render envelope** — the spatial extent Lab must lay out for this frame:

```text
lab_render_bbox =
  axis-aligned bounds(
    projected full_cells
    ∪ projected raw overlay coords (all rows, pre-clip)
    ∪ optional known exterior connector / trunk coords (future; out of scope v1)
  )
```

Legitimate **exterior void** belt/pipe routes in the raw committed overlay **expand** this envelope. They must not be dropped solely because they lie outside mineable anchors or outside the pre-expansion `full_cells` bounds.

**Forbidden:**

```text
- Computing lab_render_bbox from overlay cells AFTER anchor-only clip
    → reproduces the same route dropout bug
- Treating base full_cells bounds as a fixed clipping boundary for transport/route rows
- Dropping exterior void transport only because it lies outside mineable anchors or asteroid full_cells
```

**Construction (normative):**

1. **Seed:** axis-aligned bounds of all projected `full_cells` coords (or `map_view.bbox` when present and consistent with projected `full_cells`). Empty `full_cells` with empty overlay → no envelope → transport rows dropped.
2. **Dynamic expansion:** union every projected `lab_xy` from the incoming raw `overlay_cells` list (before per-row keep/drop). Exterior connector routes in this payload widen the envelope.
3. **Optional padding:** `padding_cells: int = 0` default; may be `1` only if a regression test proves edge cells are lost at the envelope boundary.

### 4. Equipment channel — anchor-only (MUST)

```text
equipment / placement semantic rows (is_transport_or_route_overlay_row == False):
  keep iff coord in lab_anchors (after lab_xy_from_replay_cell projection)
```

`lab_anchors` = current `_base_map_overlay_anchors` (mineable / `asteroid_*` field cells in `full_cells`).

**Regression guard:** loosening this rule causes miner/extension sprites on void cells.

### 5. Transport / route channel — render bbox + domain membership (MUST)

```text
transport / route rows (is_transport_or_route_overlay_row == True):
  keep iff projected coord is inside lab_render_bbox
  AND projected coord is in known_route_render_domain
```

**Roles (do not conflate):**

| Construct | Role |
|-----------|------|
| `lab_render_bbox` | **Dynamic render envelope** in projected lab coords — widens with raw overlay (including exterior void routes) |
| `known_route_render_domain` | Explicit **membership set** in projected lab coords (union, v1) |

Transport/route overlay cells are allowed to **expand** `lab_render_bbox` beyond asteroid `full_cells` bounds. This is required for exterior connector belts/pipes and void trunk attachment visualization.

**Forbidden:**

```text
- Using base full_cells bbox alone as a fixed clipping boundary for transport/route rows
- Dropping exterior void transport only because it lies outside mineable anchors or asteroid full_cells
- Treating lab_render_bbox as an island guard (equipment channel uses lab_anchors for that)
```

**`known_route_render_domain` (normative):**

```text
known_route_render_domain =
  projected_full_cell_coords
  ∪ projected_transport_or_route_overlay_coords
```

- `projected_full_cell_coords` = `project_overlay_coord_to_lab_xy` for every `full_cells` entry (all kinds).
- `projected_transport_or_route_overlay_coords` = projected `lab_xy` for every raw overlay row where `is_transport_or_route_overlay_row(row)` is true.

**v1 membership (MUST):** No leave-one-out. Any transport row whose projected `lab_xy` is in `known_route_render_domain` may be kept (subject to `lab_render_bbox`). Stray coords present only in the raw overlay payload are **in domain** in v1; suppressing them requires a follow-up **connected-component guard** (out of scope).

Optional future extension (out of scope v1): `∪ known_external_trunk_coords` from base map metadata when available.

### 6. `clip_overlay_cells_to_base_map_domain` signature

Extend to accept precomputed `lab_render_bbox` or compute it once at the start of the function from `(base_map_view, overlay_cells_raw)` before the per-row loop.

`project_rttp_row_to_product_frame` MUST pass the full raw overlay list into clip exactly once per row projection.

---

## Relationship to selection vs commit counts

| Concept | Source | Replay map |
|---------|--------|------------|
| `commit_order` | Selection / genome | All IDs overlaid (provisional) |
| `committed_ids` | `incremental_commit` | Confirmed subset only |
| Conflicts | `CommitResult.conflicts` | Text in `description` only |

Dropping ~70% of `commit_order` at commit is **expected** when re-probe / route reservation conflicts occur. This spec does **not** change that behavior; it only fixes **missing route drawing** for successfully committed reservations.

---

## Tests (MUST)

Add to `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`:

| Test | Purpose |
|------|---------|
| `test_exterior_route_expands_dynamic_bbox_and_survives_anchor_clip` | Route at `(9, 0)` outside mineable anchor; dynamic envelope expanded by raw overlay → route kept |
| `test_equipment_outside_anchor_still_dropped` | Miner row on void coord outside `lab_anchors` → dropped |
| `test_route_outside_explicit_render_bbox_is_dropped` | Projected transport coord outside `lab_render_bbox_override` → dropped |
| `test_mixed_confirmed_overlay_keeps_equipment_and_route_by_channel` | Mixed payload: confirmed extractor + `route.committed_path` chain |
| `test_clip_helper_classifies_fot_and_output_stub_as_transport_route` | `is_transport_or_route_overlay_row` True for confirmed FOT/stub kinds |
| `test_lab_render_bbox_uses_projected_overlay_before_clip` | Dynamic envelope includes exterior route coords not covered by `full_cells` alone; pre-clip union |

Existing tests (`test_project_rttp_overlay_cells_clipped_to_base_map_domain`, etc.) MUST be updated to reflect dual-channel expectations where they assert route dropout.

**Test-first order (implementation plan):** red → green on compose tests only; then ruff on touched paths.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Stray transport in malicious overlay | v1: kept if in payload; follow-up connected-component guard |
| Raw vs projected coord mismatch | Single `project_overlay_coord_to_lab_xy` for bbox, domain, clip |
| Probe / `route_domain.*` overlays flood map | Only rows matching `is_transport_or_route_overlay_row`; diagnostic `probe.start` stays equipment channel unless classified |
| JS bbox still wrong | `lab_map_rendering_contract.md` already requires overlay coords in spatial targets; verify one integration scrub after fix |

---

## Self-review (inline)

| Check | Result |
|-------|--------|
| Placeholders / TBD | None |
| Internal consistency | `lab_render_bbox` (render) vs `known_route_render_domain` (membership) — no `base_domain_bbox` guard |
| Scope | Single compose module + tests; algorithm non-goals explicit |
| Ambiguity | v1: no leave-one-out; stray suppression deferred to follow-up spec |

---

## Follow-up track (out of scope v1)

**Stray / disconnected transport overlay suppression:** connected-component guard — transport coord kept only if 4-connected to `full_cells`, equipment anchor, or confirmed FOT/stub in the same overlay payload. Replaces naive leave-one-out (which drops legitimate isolated route cells such as `(9, 0)`).

---

## Implementation plan

[`docs/superpowers/plans/2026-05-30-rttp-replay-route-overlay-clip.md`](../plans/2026-05-30-rttp-replay-route-overlay-clip.md)
