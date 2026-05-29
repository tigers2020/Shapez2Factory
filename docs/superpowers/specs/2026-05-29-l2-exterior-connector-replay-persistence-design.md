# L2 Exterior Connector Replay Persistence — Design Spec

**Document type:** Asteroid Lab replay / timeline contract  
**Status:** **APPROVED (2026-05-29)** — Replay Contract Architect (blocking amendments applied)  
**Work classification:** contract change · UI change  
**Scope:** `django_apps/asteroid_lab/replay/` · `django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py` · `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`  
**Extends:** [`2026-05-28-central-solver-runtime-replay-assembler-design.md`](2026-05-28-central-solver-runtime-replay-assembler-design.md) · [`2026-05-28-layer-03-full-pool-windowed-replay-design.md`](2026-05-28-layer-03-full-pool-windowed-replay-design.md)

---

## §1 — Problem

During Layer 03 rim bundle scan (and Layer 04 placement), Lab replay and raw `solver_runtime_replay_frames` can drop **planned exterior connector** observability. Users lose L2 transport spot context while reviewing candidate pools — making L3 observation meaningless.

Root causes (both must be fixed):

1. **Assembler / L3 segment:** `layer03_segment._timeline_frame` assigns `overlay_cells = transient_only`, wholesale replacing any L2 connector rows.
2. **Lab lazy UI:** `applyLoadedLabReplayPayload()` does not refresh `replayTrackMetrics`, so `frozen_exterior_connector_plan` may be missing after lazy fetch.

---

## §2 — Overlay layer contract (normative)

### 2.1 Persistent observability

| `overlay_role` | SoT |
|----------------|-----|
| `planned_exterior_connector` | `exterior_connector_plan.planned_connectors[].void_coord` (wire dict) |

```text
persistent_connector_overlays MUST be rebuilt from exterior_connector_plan wire.

L2 frame map_view.overlay_cells MAY be used only as fallback/debug when wire is unavailable.
```

L2 frame overlay is observability output, not SoT.

### 2.2 Transient observability

| Layer | Overlay kinds (`kind` / role) | Events |
|-------|------------------------------|--------|
| L3 | `candidate_miner`, `candidate_transport_stub`, `candidate_route_path` | `layer03_rim_bundle_scan_*`, `layer03_rim_bundle_pool_*` |
| L4 | `miner`, `extension`, `transport_stub`, `overlap_conflict` | `layer04_rim_*` |

### 2.3 Composition order

```text
structural overlay (non-connector rows from reconstruction base, if any)
→ persistent planned_exterior_connector (from wire)
→ transient L3 or L4 overlay
```

### 2.4 Forbidden

```text
MUST NOT wholesale-replace map_view.overlay_cells with transient-only rows
MUST NOT drop planned_exterior_connector on L3/L4 runtime frames when exterior_plan_wire is available
MUST NOT use replay / NDJSON / metrics as solver algorithm input
```

### 2.5 Coexistence and dedupe

Different roles at the same `(x, y)` MAY coexist.

**Exact duplicate removal only:**

| Layer | Duplicate key |
|-------|----------------|
| Connector | `(overlay_role, x, y, connector_id)` |
| Candidate | `(overlay_role, kind, x, y)` plus `candidate_id` when present on wire row, plus `transport` when present |
| Structural | `(overlay_role, kind, x, y)` when `overlay_role` is set |

---

## §3 — Authority split (normative)

### 3.1 `replay/overlay_composition.py`

```python
compose_replay_overlay_cells(
    *,
    structural_overlay_cells: Sequence[Mapping[str, object]],
    persistent_overlay_cells: Sequence[Mapping[str, object]],
    transient_overlay_cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]
```

Operates on **wire-shaped dict rows** (preserves `overlay_role`, `connector_role`, `connector_id`).

Persistent rows are produced by reusing `lab_timeline_exterior_connector_enrichment._planned_connectors(plan_wire)` (or a thin re-export in `replay/`).

### 3.2 Layer 03 / 04 segments — transient only

```text
L3/L4 segment builders MUST emit transient overlay cells + segment metrics only.
They MUST NOT accept base_map_view for overlay composition.
They MUST NOT attach planned_exterior_connector.
```

Introduce `ReplaySegmentFrameSpec` (frozen dataclass): `event_type`, `phase`, `title`, `description`, `metrics`, `inspector`, `transient_overlay_cells`.

### 3.3 `solver_runtime_assembler.py` — final authority

Owns:

- `structural_base_map_view` (reconstruction or post-L2 `full_cells`; **L4 algorithmic base** unchanged)
- `persistent_connector_overlays` from `exterior_plan_wire` when available
- Per-frame `compose_replay_overlay_cells(...)`
- `metrics.exterior_connector_plan` attachment when wire available
- Final `ReplayTimelineFrame` / wire JSON with composed `map_view.overlay_cells`

```text
For every runtime frame emitted after exterior_plan_wire becomes available,
frame.metrics[METRICS_KEY] MUST include the plan wire dict.
```

(`METRICS_KEY` = `exterior_connector_plan`.)

Product enricher `enrich_lab_timeline_frames_with_exterior_connector_plan` remains **belt-and-suspenders**; primary fix is runtime assembler.

---

## §4 — Pool summary overlay semantics (amendment)

**Deprecated assert:** `pool_summary.map_view.overlay_cells == []`

**Normative:**

```text
pool_summary MUST NOT include L3 candidate observation overlays.
pool_summary MAY include persistent planned_exterior_connector overlays when exterior_plan_wire is available.
```

---

## §5 — Lab UI (lazy replay)

### 5.1 `applyLoadedLabReplayPayload`

When `payload.replay_track_metrics` is present, assign `replayTrackMetrics = payload.replay_track_metrics`.

### 5.2 `replaceLabReplayPayload` lazy branch

Before early return, apply `replay_track_metrics` from POST body (solver already sends it in `entry_result_to_json_dict`).

### 5.3 Connector plan resolve order (display)

```text
1. frame.metrics.exterior_connector_plan
2. replayTrackMetrics.frozen_exterior_connector_plan
3. map_view.overlay_cells rows with overlay_role=planned_exterior_connector (display-only recovery)
```

```text
overlay_cells fallback is display-only recovery.
It MUST NOT become the canonical exterior connector plan source.
```

---

## §6 — Wire / DTO note

`ReplayOverlayCell` currently drops `overlay_role` on DTO round-trip. Persistent connector rows MUST be composed as **wire dicts** at assembler finalize time (not inferred from stripped DTO overlays). Transient candidate rows may continue using `ReplayOverlayCell` + `kind` field.

---

## §7 — Testing (normative)

| Test module | Covers |
|-------------|--------|
| `tests/unit/asteroid_lab/replay/test_overlay_composition.py` | Dedupe keys, ordering, role coexistence |
| `tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py` | L3 scan/probe/summary + metrics |
| `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py` | Update pool_summary test; L4 persistence |
| `tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py` | JS contract strings for lazy metrics refresh |

Regression:

```text
Given exterior_plan_wire and L3 probe_window with candidate overlay:
  planned_exterior_connector visible
  candidate overlay visible
  frame.metrics.exterior_connector_plan present
```

---

## §8 — Out of scope

- Enricher-only fix (approach 2 alone)
- UI-only fallback (approach 3 as sole fix)
- Solver algorithm changes
