# Layer 02 — Spare Exterior Connectors (Reference @100%) — Design Spec

**Document type:** Solver / Lab contract (Layer 2 placement + observability)  
**Status:** **APPROVED (2026-05-28)** — Solver Contract Architect (user decision A + role-labeled unified list)  
**Work classification:** contract change · implementation change · UI change (Lab replay)  
**Scope:** `django_apps/asteroid_lab/layers/layer_02_exterior_transport/` · Lab timeline enrichment · `asteroid_miner_layout_lab.js`  
**Extends:** [`2026-05-28-layer-02-exterior-connector-placement-design.md`](2026-05-28-layer-02-exterior-connector-placement-design.md)

**Korean title (reference):** L2 필수 커넥터 + Reference@100% 예비(spare) 커넥터 2-pass 배치 및 Lab 색상 분리

---

## §1 — Problem

Lab summary already shows **Reference belts @100% terrain** (`external_connector_count` = `ceil(terrain_upper_bound / per_connector_capacity)`). Layer 2 only places **required** connectors sized from `planning_target = terrain_upper_bound × target%`. Operators cannot see where spare capacity could attach until a later layer connects.

## §2 — Count contract (normative)

```text
reference_connector_count = ceil(terrain_upper_bound_per_min / per_connector_capacity_per_min)
required_connector_count  = ceil(planning_target_per_min / per_connector_capacity_per_min)
spare_connector_count     = max(0, reference_connector_count - required_connector_count)
```

| Field | Sizing input | Meaning |
|-------|----------------|---------|
| `required_connector_count` | `planning_target_per_min` (C) | Target% satisfaction (unchanged) |
| `reference_connector_count` | `terrain_upper_bound_per_min` (A) | 100% terrain reference belts |
| `spare_connector_count` | derived | Additional candidates only |

```text
len(planned_connectors) = required_planned_count + spare_planned_count
required_planned_count <= required_connector_count
spare_planned_count <= spare_connector_count
required_planned_count + spare_planned_count <= reference_connector_count (when slots allow)
```

### 2.1 Wire count semantics (normative — breaking read of `planned_connector_count`)

Pre-v2 readers often treated `planned_connector_count` as “required connectors placed”. **v2 changes this:**

| Field | Meaning | Reader rule |
|-------|---------|-------------|
| `required_connector_count` | Sized from `planning_target` (C) | Target% requirement; unchanged |
| `reference_connector_count` | Sized from `terrain_upper_bound` (A) | 100% reference belts |
| `spare_connector_count` | `max(0, reference − required)` | Theoretical spare headroom |
| `required_planned_count` | Count of `planned_connectors` with `role=required` | **Use this** for “required placed” |
| `spare_planned_count` | Count with `role=spare` | Actual spare candidates on map |
| `planned_connector_count` | `required_planned_count + spare_planned_count` | **Total** markers on map |

```text
planned_connector_count = required_planned_count + spare_planned_count
```

When `throughput_target_percent == 100`: `spare_connector_count == 0`, `spare_planned_count == 0`, and `planned_connector_count == required_planned_count == required_connector_count` (matches pre-change behavior).

When spare slots are insufficient: `spare_planned_count < spare_connector_count` is **success** (`unmet_reason = None`) as long as `required_planned_count == required_connector_count` and `total_slots >= required_connector_count`.

### 2.2 Zero throughput target (`throughput_target_percent == 0`)

```text
planning_target_per_min = 0
required_connector_count = 0
reference_connector_count = ceil(terrain_upper_bound / cap)  # unchanged
spare_connector_count = reference_connector_count
```

**Normative:** Pass 1 places zero required connectors. Pass 2 may place **spare-only** markers up to `reference_connector_count` (subject to slot availability). `unmet_reason = None` when `total_slots >= 0` (always) and required demand is satisfied (`required_planned_count == 0`).

**L2 run success (observability):** `unmet_reason is None` and `required_planned_count >= required_connector_count` — not `required_planned_count > 0`.

## §3 — Placement (2-pass, normative)

**Pass 1 (required):** Existing `EDGE_WEIGHTED_EVEN_SPACING_V1` on full `candidate_slots_by_edge`; each connector `role = required`.

**Pass 2 (spare):** `remaining_slots_by_edge` = slots not used in pass 1; same distribution/spacing for `spare_connector_count` (or fewer if remaining slots insufficient). Each connector `role = spare`.

**Priority:** Required pass failure → `NO_FEASIBLE_CONNECTOR_SITES` (unchanged). Partial spare placement when `total_slots >= required` but `< reference` is **success** (`unmet_reason = None`); observability uses `spare_planned_count < spare_connector_count`.

**Forbidden:** Spare pass reusing a `void_coord` from required pass.

## §4 — DTO and wire

```python
class ExteriorConnectorRole(StrEnum):
    REQUIRED = "required"
    SPARE = "spare"
```

`ExteriorConnector` adds `role: ExteriorConnectorRole`.

`ExteriorConnectionPlan` adds `reference_connector_count`, `spare_connector_count` (required fields).

Wire `exterior_connector_plan` version **`exterior_connector_plan.v2`**.

**Wire shape:** additive fields (`role`, `*_planned_count`, `reference_connector_count`) — old parsers may ignore unknown keys.

**Semantic read (breaking for v1 consumers):** `planned_connector_count` is **total** markers (`required_planned_count + spare_planned_count`), not “required placed only”.

**Reader fallback:** v1 wire (no per-connector `role`, no `*_planned_count`) remains valid for legacy replay; treat all connectors as `role=required` and `planned_connector_count` as required-only.

Per-connector wire: `"role": "required" | "spare"`. Missing/unknown role normalizes to `"required"` in Lab enrichment and JS (`strip().lower()`; values outside `required`|`spare` → `required`).

Lab overlay (compatibility):

```text
overlay_role = planned_exterior_connector
connector_role = required | spare
```

## §5 — Lab UI

| Role | Highlight |
|------|-----------|
| `required` | Existing white inset (`lab-planned-exterior-connector`) |
| `spare` | Cyan/blue inset (`lab-planned-exterior-connector-spare`) |

Paint from `metrics.exterior_connector_plan.planned_connectors` (SoT), not overlay alone.

## §6 — Layer boundaries (out of scope)

```text
L2 spare connectors are visualization/planning candidates only.
They must not be exported, committed, or counted as connected capacity
unless a later layer creates an explicit route reservation.
```

| Layer | Responsibility |
|-------|----------------|
| L2 | Plan + visualize required + spare (not commit/export) |
| L3+ | Route probe; prefer required; spare optional |
| L5 | Commit only connectors with route reservation |
| Validation | Unconnected **spare** is not failure; unconnected **required** remains a problem |

**Forbidden:** Using spare/replay overlay as solver algorithm input; treating spare as committed/export capacity in L2.

## §7 — Tests (minimum)

- `spare_connector_count` formula and zero at 100% target
- **Zero target:** `throughput_target_percent == 0` → `required_connector_count == 0`, all planned roles `spare`, `spare_connector_count == reference_connector_count`
- Disjoint void coords between required and spare
- 2-pass does not move required slots when spare_count > 0
- **Partial spare (mandatory asserts, no conditional skip):** fixture or monkeypatch forces `total_slots >= required_connector_count` and `total_slots < reference_connector_count`; then `unmet_reason is None`, `required_planned_count == required_connector_count`, `spare_planned_count < spare_connector_count`
- Wire v2: `required_planned_count` / `spare_planned_count` derived from `planned_connectors` roles (not from sizing counts alone)
- Wire: `planned_connector_count == required_planned_count + spare_planned_count`
- Enrichment passes `connector_role`; unknown role → `required`
- JS/CSS contract for spare tone; `overlayCellsFromMapView` preserves `connector_role`

---

## Approval record

```text
2026-05-28: User / Solver Contract Architect — Approach A,
  unified planned_connectors with role labels, 2-pass placement,
  spare highlight distinct, L3/L5 exclusion deferred.

2026-05-28 (review): Spec approved; plan v1.1 amendments —
  planned_connector_count semantics, partial spare test,
  wire/overlay/JS connector_role preservation.

2026-05-28 (review): Plan v1.2 — mandatory partial spare fixture,
  zero% spare-only contract, run_success >= required_connector_count.
```
