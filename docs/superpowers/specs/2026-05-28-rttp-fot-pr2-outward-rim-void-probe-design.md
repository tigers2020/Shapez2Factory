# RTTP FOT PR-2 — Outward Rim, Void Attach Surface, Probe Start — Design Spec

**Date:** 2026-05-28
**Status:** Approved (user 2026-05-28)
**Work classification:** contract change · implementation change
**Parent:** [`2026-05-28-rttp-fixed-output-transport-outside-mineable-design.md`](2026-05-28-rttp-fixed-output-transport-outside-mineable-design.md) (PR-1 CLOSED in workspace; PR-2 this spec)

**Related:**

- [`documents/Algorithm/solver_runtime/00_core_principles.md`](../../../documents/Algorithm/solver_runtime/00_core_principles.md) §0.2 (no global void pre-install)
- [`2026-05-24-b2-t3-transport-aware-route-domain-design.md`](2026-05-24-b2-t3-transport-aware-route-domain-design.md) — void ∈ blocked; goals excepted
- [`2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md`](2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md) — `external_void_cells` UI only

**Implementation plan:** [`../plans/2026-05-28-rttp-fot-pr2-outward-rim-void-probe.md`](../plans/2026-05-28-rttp-fot-pr2-outward-rim-void-probe.md)

---

## Problem (PR-2 closes PR-1 gap)

PR-1 blocks `fixed_output_transport ∈ mineable_cells` but leaves two product gaps:

1. **Inward rim rotations** still enter the pool when policy is `ALLOW` (tests) or fail en masse under `OUTSIDE_MINEABLE` on small maps without outward survivors.
2. **Outward topology** places FOT on `external_void_cells`, but `output_stub` is often **two steps into void**, so `probe_route(domain, output_stub, …)` hits `start ∈ blocked_cells` and returns `NOT_REACHABLE` — **no normal candidates**, overlay shows no void belt.

There is **no** existing `transport_installable_in_void` flag. Void is modeled as:

- `external_void_cells` in topology / Lab rim highlight
- `blocked_cells` in `RouteCellDomain` (not trunk-walkable)
- `route_goals` at external margin (goals unblocked for **termination**, not BFS start)

This spec defines a **derived attach surface** and a **probe-start resolver** without violating §0.2 (no “paint void network first”).

---

## Non-goals

- New persisted DB flag `transport_installable_in_void`
- Pre-installing full route through void before commit (§0.2 forbidden)
- Changing `blocked = mineable ∪ void` globally to traversable
- PR-3 regret / ring alignment scoring (separate)
- Moving extractor anchor off `mineable_cells`

---

## Terminology (no `output_stub == FOT`)

| Cell | Offset from anchor | Role |
|------|-------------------|------|
| FOT | `+1 × unit(output_dir)` | First belt/pipe semantic; overlay `placement.*_fixed_output_transport` |
| `output_stub` | `+2 × unit(output_dir)` | Catalog probe anchor; often **inside void** when outward |

```text
output_stub = FOT + unit(output_dir)
FOT ∉ mineable (PR-1 + PR-2)
```

---

## Derived attach surface (not a new OptimizationInput flag)

**Normative derived set** (computed at candidate generation from existing inputs):

```python
def transport_attach_surface_cells(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    return frozenset(inp.external_void_cells | skeleton.ring_cells)
```

| Cell kind | In attach surface? | In mineable? | Notes |
|-----------|-------------------|--------------|-------|
| `asteroid_*_field` | No | Yes | Extractor only |
| `external_void` | Yes | No | Outward FOT target |
| `ring_cells` (bbox frame) | Yes | No | Export / trunk frame |
| `trunk_mask` / lift | No* | No | Route materialization, not FOT |

\*PR-3 may **prefer** FOT adjacent to trunk; not required for PR-2 admission.

### INV-FOT-10 (PR-2, `OUTWARD_FROM_RIM` at rim)

When `anchor_coord ∈ inp.rim_cells` and policy is `OUTWARD_FROM_RIM`:

```text
fixed_output_transport_cell(candidate) ∈ transport_attach_surface_cells(inp, skeleton)
```

Equivalently for rim anchors: FOT neighbor is **not** mineable and lies on void or ring frame.

### INV-FOT-11 (PR-2 outward direction)

```text
output_dir ∈ outward_dirs(anchor, inp, skeleton, domain)
```

**`outward_dirs`** (normative): cardinal direction `d` with unit vector `u` where `neighbor = anchor + u` satisfies **all**:

1. `neighbor ∉ inp.mineable_cells`
2. `neighbor ∉ inp.blocked_incompatible_transport_cells` (wrong-kind transport)
3. `neighbor ∈ transport_attach_surface_cells(inp, skeleton)` OR `neighbor ∈ probe_goal_coords(inp, skeleton)`
   (void margin **or** ring port / margin goal — attach/export intent)

**Do not** treat “non-mineable neighbor” alone as outward (concave rim false positives without attach/goals check).

---

## Route probe start resolver (PR-2 core)

### Problem

```52:58:django_apps/asteroid_lab/optimization/routing/lift_lane_domain.py
    blocked = frozenset(
        (inp.mineable_cells | inp.external_void_cells)
        - platform_cells - trunk_mask - lift_coords - goal_coords
    )
```

`output_stub` in void ⇒ `start ∈ blocked_cells` ⇒ unreachable **even when FOT on void is correct**.

### Policy: `RouteProbeStartPolicy` (new, PR-2)

```python
class RouteProbeStartPolicy(StrEnum):
    OUTPUT_STUB_ONLY = "output_stub_only"          # diagnostic / legacy compare
    PLATFORM_FALLBACK_WHEN_STUB_BLOCKED = "platform_fallback_when_stub_blocked"  # PR-2 default
```

**Default (PR-2 production):** `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED`

### Resolver (shared: generation probe + commit reprobe)

```python
def resolve_route_probe_start(
    *,
    anchor_coord: Coord,
    output_stub: Coord,
    domain: RouteCellDomain,
    skeleton: RttpSkeleton,
    policy: RouteProbeStartPolicy,
) -> Coord | None:
```

**Algorithm (normative order):**

1. If `output_stub ∉ domain.blocked_cells` and `_initial_phase(domain, output_stub)` is not None → return `output_stub`.
2. If policy is `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` and `anchor_coord` is a lift `platform_coord` (`LiftEdge.platform_coord`) and `_initial_phase(domain, anchor_coord) == "platform"` → return `anchor_coord`.
3. Otherwise → return `None` (caller maps to `NOT_REACHABLE` or generation reject `ROUTE_PROBE_START_BLOCKED`).

**Forbidden:**

- Starting BFS inside arbitrary void cells without platform/trunk phase
- Using replay metrics to pick start
- Different resolver at commit vs generation (must share helper module)

### Reconciliation with §0.2

| §0.2 forbidden | PR-2 allowed |
|----------------|--------------|
| Install belt/pipe network across void **before** commit | Single FOT overlay cell on void margin per bundle |
| Void-first routing policy | Probe **enters** via rim `platform_coord` (mineable), then lift → trunk → goals |
| Global void traversable | Only **start coord** exception when stub blocked |

Materialized route after commit remains on `trunk_mask` / lift / reserved path — not a void fill.

---

## Candidate generator changes (Layer 2)

**Order** (extends PR-1 list; still before admitting normal pool):

1. PR-1 geometry rejects (occupied, mineable FOT, incompatible transport).
2. If `OUTWARD_FROM_RIM` and `anchor ∈ rim_cells`: `OUTPUT_DIR_NOT_OUTWARD_FROM_RIM`, `FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE` (new reject) if FOT ∉ attach surface.
3. `start = resolve_route_probe_start(...)`; if `None` → reject `ROUTE_PROBE_START_BLOCKED` (new) **before** `probe_route`.
4. `probe_route(domain, start, goals)` — **start may be `anchor_coord`**, not always `output_stub`.
5. Store on `BundleCandidate` (optional PR-2 fields): `route_probe_start: Coord` for replay/debug parity; default `output_stub` for backward compat in tests that construct DTOs manually.

**`generate_candidates` defaults after PR-2:**

```python
fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM
route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
```

**`run_rttp_pipeline`:** pass both policies explicitly (same pattern as PR-1 `OUTSIDE_MINEABLE`).

---

## Commit / reprobe (Layer 7)

`attempt_commit_candidate` must call the **same** `resolve_route_probe_start` with the **latest** `RouteCellDomain` before `probe_route`.

Defense in depth unchanged: FOT ∉ `mineable_cells` at commit.

---

## Overlay / Lab (Surface B)

When PR-2 admits outward rim candidates:

```text
placement.confirmed_fixed_output_transport at coord ∈ external_void_cells  (allowed)
placement.confirmed_output_stub may also show belt semantic on void (existing rows)
committed route cells remain on trunk_mask (unchanged)
```

Acceptance: at least one fixture (narrow corridor or greenfield with outward survivor) shows FOT overlay on void after PR-2.

---

## Reject reasons (add)

| Enum | Value | When |
|------|-------|------|
| `FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE` | `fixed_output_transport_not_on_attach_surface` | Rim + `OUTWARD_FROM_RIM`; FOT ∉ attach surface |
| `ROUTE_PROBE_START_BLOCKED` | `route_probe_start_blocked` | `resolve_route_probe_start` returned `None` |

Defer `FIXED_OUTPUT_TRANSPORT_NOT_IN_ROUTE_DOMAIN` unless needed after outward + platform fallback still insufficient.

---

## Tests (normative)

| Test | Asserts |
|------|---------|
| `test_outward_fot_on_external_void_not_mineable` | Rim anchor W; FOT ∈ void; ∉ mineable |
| `test_outward_rejects_inward_rim_rotation` | E from west rim → `OUTPUT_DIR_NOT_OUTWARD_FROM_RIM` |
| `test_probe_uses_platform_fallback_when_stub_in_void` | `output_stub` blocked; probe still reachable via anchor platform |
| `test_resolve_route_probe_start_matches_commit_reprobe` | Same start coord generation vs `attempt_commit_candidate` |
| `test_overlay_shows_fot_on_void_coord` | Confirmed rows include FOT on `external_void_cells` |
| `test_narrow_corridor_normal_pool_with_outward_policy` | ≥1 normal under `OUTWARD_FROM_RIM` |

Update `NARROW_CORRIDOR_*` IDs only if platform-fallback changes committed order (unlikely).

---

## Phasing

| Slice | Delivers |
|-------|----------|
| **PR-2a** | `transport_attach_surface_cells`, outward_dirs, attach-surface reject |
| **PR-2b** | `resolve_route_probe_start` + generator + commit + tests |
| **PR-2c** | Pipeline defaults `OUTWARD_FROM_RIM` + replay `route_probe_start` field |

PR-3 ring scoring remains separate.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Concave rim multiple outward dirs | `outward_dirs` is a set; catalog rotation must match one |
| Platform fallback masks bad topology | Log `route_probe_start != output_stub` in replay metrics (output-only) |
| §0.2 misread as void routing | Document § reconciliation table above |
| Greenfield still empty pool | Expect outward+platform only on maps with rim+void+lift; document in ops notes |

---

## Approval

- [x] User approved PR-2 direction (2026-05-28)
- [ ] Implementation plan reviewed
- [ ] Code implementation
