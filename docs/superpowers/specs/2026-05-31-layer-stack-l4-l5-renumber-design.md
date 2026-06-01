# Layer stack L4/L5 renumber — Normative Design

**Status:** APPROVED (2026-05-31; contract correction — slug canon + stack order; implementation via PR-1 then optional PR-2)
**Date:** 2026-05-31
**Owner:** `shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs`, `stack_runner`, Lab/replay surfaces
**Amends:** [`2026-05-31-layer-03-rim-placement-v2-design.md`](2026-05-31-layer-03-rim-placement-v2-design.md), [`2026-05-31-layer-04-transport-routing-design.md`](2026-05-31-layer-04-transport-routing-design.md)
**Supersedes (ordering only):** prior implicit canon “L4 = transport, L5 = inner fill”

---

## Process gate

This is a **layer contract correction**, not an order-only tweak. No production behavior change lands until this spec is approved and a phase plan exists (`writing-plans`).

**Staged delivery:**

| Phase | Scope |
| ----- | ----- |
| **PR-1** | Canonical slug rename, deprecated aliases, active stack order, Lab/replay labels, docs, tests. Physical package paths **unchanged** except thin shims if required. |
| **PR-2** (optional) | Directory/module relocation `layer_04_transport_routing/` ↔ `layer_05_inner_pattern_fill/` when reference inventory is small and shims are explicit. |

---

## Decision record

| Choice | Value |
| ------ | ----- |
| Option | **A — Canon rename** with transitional aliases (not B order-only, not C big-bang in PR-1) |
| Pipeline rule | **Transport routes after inner fill**, not before |
| L3 | `layer_03_rim_greedy_placement` — rim committed placements / `m_output_stub` / throughput |
| L4 | `layer_04_inner_pattern_fill` — interior fill / internal occupancy (non-transport) |
| L5 | `layer_05_transport_routing` — final belt/pipe commit, trunk connection, transport replay authority |
| L6 | `layer_06_commit_validate` — final validation |
| Deprecated L4 rim bundle | `layer_04_rim_bundle_placement` remains deprecated; does not return to active stack |

**Normative sentence:**

```text
Interior fill fixes occupancy and shape first; transport routing commits belt/pipe against that fixed state.
```

---

## Canonical slugs and aliases

### Active stack (normative)

```text
LAYER_02_EXTERIOR_TRANSPORT
LAYER_03_RIM_GREEDY_PLACEMENT
LAYER_04_INNER_PATTERN_FILL      # layer_04_inner_pattern_fill
LAYER_05_TRANSPORT_ROUTING       # layer_05_transport_routing
LAYER_06_COMMIT_VALIDATE
```

`LAYERS_02_TO_06_ACTIVE` MUST list slugs in execution order above.

`layer_index` observability map:

| Index | Slug |
| ----: | ---- |
| 4 | `layer_04_inner_pattern_fill` |
| 5 | `layer_05_transport_routing` |

### Python constants (normative)

```python
LAYER_04_INNER_PATTERN_FILL = "layer_04_inner_pattern_fill"
LAYER_05_TRANSPORT_ROUTING = "layer_05_transport_routing"
```

### Deprecated slug strings (read-compat only)

Persisted artifacts, old JSONL, and one-release tests may still contain **misnumbered slug literals**. They MUST NOT remain canonical constants.

| Deprecated slug literal | Resolves to role |
| ----------------------- | ---------------- |
| `layer_04_transport_routing` | L5 transport routing |
| `layer_05_inner_pattern_fill` | L4 inner pattern fill |
| `layer_04_rim_bundle_placement` | deprecated rim bundle (inactive) |

PR-1 adds `resolve_canonical_layer_slug(slug: str) -> str` (or equivalent registry) used by Lab summary, replay coverage, and artifact readers. New writers emit only canonical slugs.

Remove the old `layer_slugs.py` block that set `LAYER_04_INNER_PATTERN_FILL = LAYER_05_INNER_PATTERN_FILL` without making L4 the primary inner-fill string.

**Hard rule:** New code, new docs, and new tests use **only** canonical slug constants. Deprecated literals appear only in the resolver map, shim modules, and explicit backward-compat tests.

---

## DTO and runner contracts (PR-1)

Physical directories may stay misnumbered until PR-2; **public contracts** still renumber.

| Artifact | Old (misnumbered) | New canonical | Deprecated alias |
| -------- | ----------------- | ------------- | ---------------- |
| Transport route plan DTO | `Layer04RoutePlan` | `Layer05RoutePlan` | `Layer04RoutePlan = Layer05RoutePlan` |
| Transport plan version key | `layer04_route_plan_v1` | `layer05_route_plan_v1` | accept old version in `from_payload` one release |
| Transport runner entry | `run_layer_04_transport_routing` | `run_layer_05_transport_routing` | shim `run_layer_04_transport_routing = run_layer_05_transport_routing` |
| Inner fill runner entry | `run_layer_05_inner_pattern_fill` | `run_layer_04_inner_pattern_fill` | shim `run_layer_05_inner_pattern_fill = run_layer_04_inner_pattern_fill` |

### Stack dataflow (normative)

```text
L3  IntegratedRimGreedyResult
      ↓
L4  inner fill (provisional_overlay + complete_map; NO transport plan input)
      ↓  interior occupancy / fill result (stub today; contract slot required)
L5  transport routing (rim + exterior + interior occupancy; catalog; commit tiles)
      ↓
L6  commit & validate
```

**L4 MUST NOT** require `Layer05RoutePlan` (or deprecated `Layer04RoutePlan`) as input.

**L5 MUST** run after L4 in `stack_runner` and MUST treat L3 `route_probe_path` as witness-only (unchanged from transport spec).

**L5** replaces the incorrect dependency where inner fill accepted `layer04_route_plan` before fill existed.

### Interior fill stub (PR-1)

Until fill algorithm lands, `run_layer_04_inner_pattern_fill` keeps signature:

```python
def run_layer_04_inner_pattern_fill(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    provisional_overlay: ProvisionalLayoutOverlay,
    budget_ctx: LayerBudgetContext,
) -> Layer04InnerFillResult:  # new empty/stub DTO or None per existing stub policy
```

Remove `layer04_route_plan` from L4 signature. Emit post-summary metrics under slug `layer_04_inner_pattern_fill`.

### Transport (PR-1)

`run_layer_05_transport_routing` retains current routing logic; `stack_runner` invokes it **after** L4.

Interior occupancy passed into L5 when available (stub may pass empty `frozenset` until fill produces cells).

---

## Replay and Lab surfaces

### Replay event types

Canonical wire strings:

```text
layer05_transport_routing_begin
layer05_transport_routing_complete
```

Register deprecated aliases (same handlers / same segment builder):

```text
layer04_transport_routing_begin   → alias of layer05_*
layer04_transport_routing_complete
```

Persisted artifact frames MAY contain old event types; Lab adapter MUST resolve both for one release.

Inner fill replay phase: `layer_04_inner_pattern_fill` (new segment when fill has observability; stub may emit single begin/complete pair).

### Lab UI layer cards

| Index | Title (EN) | Slug |
| ----: | ---------- | ---- |
| 4 | Inner pattern fill | `layer_04_inner_pattern_fill` |
| 5 | Transport routing | `layer_05_transport_routing` |

Greedy L3 path MUST NOT show “L4 Rim bundle placement superseded” as the transport row; transport is L5.

### Artifact / JSONL

- Post-summary JSONL filenames follow **canonical** slug: `layer_04_inner_pattern_fill.jsonl`, `layer_05_transport_routing.jsonl`.
- Readers accept deprecated filenames one release via alias map in observability loader only.

Replay compose order in `solver_runtime_assembler`: L2 → L3 → **L4 fill frames (when present)** → **L5 transport frames**.

Equipment persistent overlay policy unchanged: committed rim equipment remains visible through transport replay frames.

---

## Amendments to existing specs

### L3 v2 (`2026-05-31-layer-03-rim-placement-v2-design.md`)

Replace references “interior fill (L5)” → **L4**; “final transport (L4)” → **L5**. Transport authority paragraph MUST cite `layer_05_transport_routing`.

### L4 transport routing (`2026-05-31-layer-04-transport-routing-design.md`)

Add header amendment: **normative owner slug is now `layer_05_transport_routing`**; document body may keep historical “L4” mentions as deprecated labels until editorial pass. Algorithm requirements unchanged.

---

## Non-goals (PR-1)

- Physical directory rename (PR-2 only).
- Changing L3 rim greedy algorithm.
- Using replay frames or artifacts as solver routing input.
- Renumbering L1–L3 or L6.
- Migrating historical DB `SolverRun` rows (read old slugs via alias only).

---

## Acceptance (PR-1)

| ID | Given | When | Then |
| -- | ----- | ---- | ---- |
| A1 | Active stack run | layers 02–06 execute | `completed_layer_slugs` order includes fill slug before transport slug |
| A2 | `layer_slugs` | imported | canonical constants match table; deprecated aliases resolve to swapped values |
| A3 | `run_layer_04_inner_pattern_fill` | called from stack | no `Layer05RoutePlan` / `Layer04RoutePlan` parameter |
| A4 | Transport replay segment | built | event_type is `layer05_transport_routing_*` (alias test for `layer04_*`) |
| A5 | Lab summary for greedy run | rendered | layer index 4 = inner fill, 5 = transport routing |
| A6 | Golden / unit stack test | L3→L4→L5 | transport runner receives rim after fill hook invoked |

---

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| Wide grep churn | PR-1 limited to contract surfaces; shims at django delegate `run.py` |
| Stale docs | Amend two specs + plan README banner; `documents/ai/manuals/environment.md` slug list |
| Artifact replay with old event types | Dual-register event types; adapter tests |
| `Layer04RoutePlan` name in 40+ files | Type alias + re-export; rename in PR-2 optional |

---

## PR-2 trigger checklist (physical rename)

Proceed only when:

1. `rg 'layer_04_transport_routing|layer_05_inner_pattern_fill'` import count is bounded and listed.
2. Shim modules exist for every old import path used by django_apps and tests.
3. PR-1 alias tests green.

Target layout:

```text
layers/layer_04_inner_pattern_fill/   # moved from old layer_05
layers/layer_05_transport_routing/    # moved from old layer_04
```

---

## References

- [`AGENTS.md`](../../../AGENTS.md) — contract-first, one PR purpose
- [`2026-05-31-layer-04-transport-routing-design.md`](2026-05-31-layer-04-transport-routing-design.md) — transport algorithm (slug amended)
- [`docs/superpowers/plans/2026-05-31-layer-04-transport-routing/README.md`](../plans/2026-05-31-layer-04-transport-routing/README.md) — add banner pointing to this renumber spec before further transport tasks
