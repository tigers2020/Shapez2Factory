# RTTP v0.2 Core Algorithm Recovery Design

**Document type:** Canonical recovery design spec  
**Status:** Approved (2026-05-30, amended) · **Gate A CLOSED** (2026-05-26) · **Gate B OPEN** · implementation checklist §13  
**Scope:** RTTP core algorithm correctness recovery (product-grade layout on representative maps)  
**Not in scope:** test decontamination PR-F3–F5, governance-only observability, macro unpause, full GA tuning, validation repair, replay/artifact as algorithm input  
**Queue authority:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md) — ACTIVE row required before implementation  
**Implementation plan:** [`docs/superpowers/plans/2026-05-30-rttp-v0-2-core-algorithm-recovery.md`](../plans/2026-05-30-rttp-v0-2-core-algorithm-recovery.md)  
**Roadmap:** supersedes v0.2 “ops-only stabilization” intent in [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) § v0.2 Intent (see §12)

**Korean title (reference):** RTTP v0.2 코어 알고리즘 복구 설계 정본

**Post-A6 transport contract:** [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md) (EVTC — separate from Task 6 A6 validation).

---

## §1 — Executive summary

v0.1 closed **architecture and partial fixtures** on `master`. Product-grade RTTP behavior on representative real maps is **not proven**. Observed failures on a **583 installable-cell** map include: **~23 extractor-only commits**, **no output belt/pipe at extractors**, **no extensions**, **no max-throughput-aware transport allocation**, and **no exterior-connected transport network**.

v0.2 is **repurposed** from governance/cleanup-first to **Algorithm Stabilization (v0.2A Core Recovery)**. This spec is the **canonical recovery design** — evidence, repair order, success gates, and forbidden shortcuts — before any implementation plan or code change.

**Primary success criterion (1st gate):** **A — Representative real-map recovery** on **primary Gate A fixtures** (see §3.1): `test_map.txt` import + `rttp-cert-candidate-recon-l0`. Success requires **materialized output transport and exterior-connected routes**, not extractor commit count alone.

**Secondary (2nd gate):** **B — Throughput utilization** on `rttp-cert-candidate-recon-l0` after transport/trunk recovery.

**Diagnostic (not product pass):** `copy-import-495e552c` — policy-separated T2 shortfall only; never used as Gate A product success evidence.

**Smoke guard:** `rttp-cert-candidate-tiny-passable-v2` — Gate C regression only.

---

## §2 — Problem statement (product observation)

On the current reference map class (~**583** shape-field / installable cells):

| Symptom | Expected (North Star + phase docs) | Observed |
|---------|--------------------------------------|----------|
| Committed bundles | Miners **with extensions** where topology allows; throughput-aware count toward budget | **~23 extractors** committed; extensions absent |
| Output transport | Belt/pipe at **fixed output transport** cell per bundle | **No transport** at extractor outputs |
| Extension use | Catalog/pattern extensions (0..3) when beneficial | **Extension absent** |
| Throughput policy | `reconstruction_max` / target drives **placement_goal** and transport demand | **No effective max-throughput transport distribution** |
| Exterior trunk | Route-feasible path to **exterior trunk**; committed route cells materialized | **No exterior-connected transport** |

These symptoms indicate **multiple pipeline stages** are broken or stubbed, not a single-line bug.

```text
reconstruction
→ catalog-native candidate generation
→ extension / output-transport bundle geometry
→ throughput-aware placement goal
→ route probe + reservation
→ incremental commit (re-probe)
→ route + equipment materialization (replay/Lab)
→ read-only validation
```

---

## §3 — Evidence freeze (A0 — normative)

Before code fixes, freeze **reproducible evidence** per slug:

| Field | Required |
|-------|----------|
| `slug` / map source | e.g. `copy-import-495e552c`, `rttp-cert-candidate-recon-l0`, import of `test_map.txt` |
| `solver_run_id` | DB run after `manage.py run_solver` |
| `run_key` | RTTP run key |
| `shape_field_cell_count` / `reconstruction_max` | From capacity envelope |
| `confirmed_count` / `committed_ids` length | Commit outcome |
| `visible_miner_cell_count` / `visible_extension_cell_count` | From `rttp.commit` step metrics |
| `reserved_route_cells` count | Commit route reservation |
| `placement_goal_plan` | `placement_goal_count`, caps, `bundles_needed_for_target` |
| `issue_codes` | Post-run issues |
| T0–T3 tier breakdown | Per [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) |
| Lab/replay frame | Optional screenshot or overlay export for “no transport visible” |

**Fixture note:** [`tests/fixtures/asteroid_lab/test_map.txt`](../../../tests/fixtures/asteroid_lab/test_map.txt) is a Shapez2-encoded map (same class as real imports). Use it as an **evidence import source**; register the imported slug in A0 evidence JSON.

**Do not** delete or weaken tests that capture this evidence while F-track decontamination is on HOLD.

### §3.1 — Gate A slug roles (approved)

| Slug / source | Role | Gate |
|---------------|------|------|
| [`tests/fixtures/asteroid_lab/test_map.txt`](../../../tests/fixtures/asteroid_lab/test_map.txt) → import slug `rttp-core-recovery-test-map` | **Primary failure reproduction** | **Required Gate A** |
| `rttp-cert-candidate-recon-l0` | Real/recon class regression (583-cell class) | **Required Gate A** |
| `copy-import-495e552c` | Diagnostic canon / T2 policy separation | **Auxiliary** — not product success |
| `rttp-cert-candidate-tiny-passable-v2` | Tiny pass-capable smoke | **Auxiliary** — Gate C only |

---

## §4 — Stage diagnosis map (A1)

Use existing step metrics; assign **first failing stage** per slug:

| Stage | Step / module | Proves | Failure signals |
|-------|---------------|--------|-----------------|
| S1 | Reconstruction | Installable terrain envelope | `reconstruction_max` vacuous or wrong class |
| S2 | Catalog specs | Bundle topology (extractor, extensions, FOT) | `extension_offsets` always empty; wrong FOT offset |
| S3 | Candidate pool | Reachable normal candidates | `normal_count` low; mass `NOT_REACHABLE` |
| S4 | Placement goal | Throughput-aware goal count | `placement_goal_count` ≪ `bundles_needed`; cap reasons |
| S5 | Selection | Order/quality of commit list | greedy ≡ evolution failure modes |
| S6 | Commit + re-probe | Route reservation growth | `confirmed_count` ≪ goal; FOT conflicts |
| S7 | Materialization | Visible miners, extensions, belts, route path | `visible_extension_cell_count` = 0; empty route overlay |
| S8 | Validation | Read-only layout assert | `rttp_validation_failed` (T1b) |

**Hypothesis A2-H1 (high confidence; confirm in A0/A2 evidence):** catalog topology normalization may drop extension geometry because `MinerPlacementTopology.extension_offsets` defaults to an empty tuple in `normalize_miner_placement_topology` (`django_apps/asteroid_lab/catalog/miner_placement_topology.py`). A2 must prove whether catalog slice / footprint projection can recover extension offsets, or whether v0.1 intentionally discarded them. **Do not** document as confirmed root cause until A2 evidence is recorded.

**Known code anchor (S7):** `build_confirmed_placement_overlay_rows` emits per-candidate FOT belt rows and `_route_rows` for `reserved_route_cells` minus bundle occupancy (`placement_overlay_projection.py`). If **`reserved_route_cells` is empty or disconnected**, UI will show **miners without exterior transport** even when FOT stub rows exist.

---

## §5 — Recovery tracks (ordered)

### A0 — Evidence freeze

- Run solver on frozen slugs; write JSON under `docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-*.json`
- Include before/after columns for each repair task

### A1 — Stage diagnosis

- Automate tier + step metric extraction (reuse slug certification scanner patterns)
- Publish **first-failure stage** per slug (table in report)

### A2 — Candidate / bundle geometry repair

**Goal:** Candidates carry **correct catalog topology**: extensions when catalog footprint implies them; valid **fixed output transport** offset; output stub alignment.

| Task | Direction |
|------|-----------|
| A2-1 | Extend `normalize_miner_placement_topology` (or successor) to derive **extension_offsets** from catalog footprint / connector graph — not hard-coded empty |
| A2-2 | Ensure `CatalogPlacementSpec.extension_offsets` propagates to `BundleCandidate.pattern` |
| A2-3 | Regenerate or augment placement specs where single-cell miner variants should still admit **lin_* test patterns** only in tests (PR-3 boundary preserved) |

**Gate:** On evidence slug, `visible_extension_cell_count > 0` when map class supports extensions; candidate pool includes non-zero extension patterns where reachable.

### A3 — Output transport + route materialization repair

**Goal:** Every committed bundle has **output belt/pipe** at FOT; committed routes form a **connected exterior-facing** transport graph.

| Task | Direction |
|------|-----------|
| A3-1 | Verify FOT cell enters `committed_fixed_output_transport_cells` and is not dropped from overlay merge |
| A3-2 | Ensure `reserved_route_cells` includes path from FOT/stub to **trunk/goals** (not probe-only ghost path) |
| A3-3 | Align `RouteProbeStartPolicy` / `FixedOutputTransportPolicy` (`OUTWARD_FROM_RIM`) with exterior attachment on real maps |
| A3-4 | Materialize **inter-bundle** route segments in overlay/export (not only per-candidate FOT stub) |

**Gate:** Lab/replay shows **transport cells** on output faces **and** at least one **exterior-connected** route chain on evidence slug.

### A4 — Placement coverage goal + shortfall attribution (Task 4, 2026-05-26)

**Product goal (SoT):** `placement_goal_count = ceil(asteroid_field_cell_count × placement_target_percent / 100)` where `asteroid_field_cell_count` comes from **`ReconstructionCompleteMap`** via `asteroid_field_cell_count_for_placement(complete_map, transport_kind)` (shape/fluid platform count for active transport — not a hardcoded constant). Example: recovery test map @ 80% → 467 when that map has 583 shape field cells. Run-config key `throughput_target_percent` is a **legacy alias** for `placement_target_percent`.

**Diagnostic only (must not clamp product goal):** `route_feasible_candidate_cap`, `non_overlapping_anchor_cap`, `bundles_needed_for_target` (T2 budget). Evidence flag: `placement_goal_shortfall` (never `placement_goal_capped`). Shortfall reason tokens: `route_feasible_shortfall`, `candidate_generation_shortfall`, `anchor_capacity_shortfall`, `commit_shortfall`, `placement_goal_shortfall`.

**Out of scope Task 4:** expanding candidate pool to commit 467, A3.1 spine, extension synthesis.

| Task | Direction |
|------|-----------|
| A4-1 | ~~Diagnose why `placement_goal_count` stalls (~32)~~ **Done** — product goal now 467; commits still capped by route pool (~74) and commit conflicts |
| A4-2 | Selection must prefer bundles that increase **committed throughput** toward target (regret/evolution metrics tied to throughput_factor) |
| A4-3 | Separate **diagnostic shortfall** (expected on diagnostic canon) from **product failure** (evidence slug must improve utilization or explicit bounded shortfall reason) |

**Gate (B):** On `recon-l0` class slug, `actual_committed` moves materially toward target (exact ratio in implementation plan; not “tiny fixture only”).

### A5 — Commit / reservation repair

**Goal:** Commit-time re-probe uses **latest** domain; FOT + route reservations stay consistent (extends FL-06 class fixes).

| Task | Direction |
|------|-----------|
| A5-1 | No commit approval without route reservation when North Star requires trunk connection |
| A5-2 | Conflict reasons (`OUTPUT_STUB_NOT_RESERVED`, FOT conflicts) drive LNS/deferred-retry only within existing policy — **no validation repair** |

**Gate:** T1a + T1b pass on evidence slug after A2–A4; `rttp.commit.passed == true`.

### A6 — Product regression fixtures (standing gates)

Freeze **minimum 3** slug classes:

| Class | Slug (current) | Role |
|-------|----------------|------|
| Pass-capable tiny | `rttp-cert-candidate-tiny-passable-v2` | Regression guard (do not break) |
| Diagnostic real-map | `copy-import-495e552c` | Stage diagnosis + policy-separated T2 |
| Representative installable | `rttp-cert-candidate-recon-l0` and/or `test_map.txt` import | **Primary A gate** — 583-cell class |

Add pytest or ops script gate (implementation plan) — **not** `validation_passed` alone.

---

## §6 — Success criteria (normative)

### Gate A — Representative real-map (primary)

On **both** primary fixtures (`rttp-core-recovery-test-map` and `rttp-cert-candidate-recon-l0`), all of the following must hold (commit count alone is **insufficient**):

```text
committed_extractors > 0
AND committed_output_transport_cells > 0
AND committed_route_cells > 0
AND exterior_connected_route_count > 0
AND validation_passed == true
```

When output transport or exterior connectivity is absent, the run must **fail closed**:

```text
validation_passed == false
AND issue_codes includes missing_output_transport and/or missing_exterior_route
(equivalent stable tokens — see implementation plan Task 6)
```

Additional checks:

1. **Extensions** — `visible_extension_cell_count >= 1` where catalog topology supports extensions (after A2)  
2. **Commit scale** — `confirmed_count` consistent with `placement_goal_count` unless documented cap in `placement_goal_plan`  
3. **Determinism** — two consecutive runs (fixed config): same `committed_ids` order and counts  

**North Star alignment:** extractors committed without exterior-connected transport violate “everything provisional until connected to exterior trunk” ([`asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)).

### Gate B — Throughput (secondary)

On `rttp-cert-candidate-recon-l0` (or successor):

- `actual_committed_output_per_min` / `throughput_target_min` ratio improves vs A0 baseline OR shortfall attributed to explicit `ThroughputShortfallReason` with non-zero best bundle throughput

### Gate C — Tiny pass-capable (guard)

- `rttp-cert-candidate-tiny-passable-v2` remains certified pass-capable (PR #101/#102 class)

---

## §7 — Forbidden shortcuts (recovery)

| Forbidden | Reason |
|-----------|--------|
| Validation repair / auto-fix in `final_validation` | B-CS3 contract |
| Lowering `throughput_target_percent` on evidence slug to fake pass | Hides product failure |
| Reclassifying product failure as `expected_diagnostic_shortfall` | Track D is for diagnostic canon only |
| Weakening FOT / route-domain guards | Masks trunk disconnect |
| Using replay/NDJSON/solver_summary as algorithm inputs | Contamination policy |
| PR-F3–F5 test deletes while A0–A2 open | May destroy failure evidence |
| Declaring v0.2 CLOSED on tiny fixture only | Gate A requires representative map |

---

## §8 — Relationship to paused / held work

| Item | Disposition |
|------|-------------|
| **PR-F3–F5** decontamination | **HOLD** until Gate A passes: `test_map` import tracked as regression fixture; FOT/transport materialized; ≥1 exterior-connected route; extensions represented when catalog supports; validation fails when transport/exterior absent |
| **D-PR #99** T2 observability | Merge only if **pure summary fields**; do not merge policy that blurs diagnostic shortfall vs algorithm failure |
| **v0.2 C-track** tier taxonomy | **Keep** — use as diagnosis language |
| **v0.2 Track A (old)** throughput campaigns | **Subsumed** by A4/B gates here |
| **Macro unpause** | Remains **PAUSED** |
| **Full GA** | Remains **v0.3+** |

---

## §9 — Documentation corrections (roadmap language)

Replace overstated v0.2 / v0.1 closure phrasing:

```text
Before (overstated):
  v0.1 proved route-feasible RTTP + catalog-native candidates

After (accurate):
  v0.1 established RTTP architecture, catalog input canon, and partial
  route-feasible fixtures; product-grade algorithm correctness is not yet proven.
  v0.2 is repurposed to Algorithm Stabilization (this spec) before further
  governance cleanup or test decontamination F3–F5.
```

---

## §10 — Authority and layer boundaries

| Layer | Recovery work allowed |
|-------|------------------------|
| `catalog/` · `adapters/` | Topology spec derivation, extension offsets, FOT |
| `optimization/candidates/` | Generator admission, geometry validation |
| `optimization/commit/` | Re-probe, reservation (no validation repair) |
| `optimization/materialization/` | Overlay/export rows (output-only) |
| `services/placement_goal.py` | Throughput goal policy |
| `documents/Algorithm/asteroid_lab_*.md` | Update phase contracts when behavior changes |

**Domain:** no I/O in pure optimization modules; runtime entry orchestrates only.

---

## §11 — Verification (design-level)

Narrow (during recovery tasks):

```powershell
python -m pytest tests/unit/asteroid_lab/ -k rttp
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/catalog django_apps/asteroid_lab/adapters
```

Evidence runs (manual / ops, recorded in A0 JSON):

```powershell
python manage.py run_solver --slug <evidence-slug>
```

Standing gates remain required on touch:

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_optimization_contamination.ps1
```

---

## §12 — Approval checklist (pre-implementation)

Design and queue gates before code work. **Implementation progress:** §13.  
**Legend:** ✅ done · ⬜ open

- ✅ Gate A primary fixtures: `test_map.txt` import + `rttp-cert-candidate-recon-l0`; diagnostic canon auxiliary only  
- ✅ PR-F3–F5 HOLD until Gate A (materialization + validation fail-closed)  
- ✅ D-PR merge observability-only (no blur of diagnostic vs algorithm failure)  
- ✅ Implementation plan: `2026-05-30-rttp-v0-2-core-algorithm-recovery.md`  
- ✅ `current_plan.md` ACTIVE row + roadmap v0.2 intent updated  
- ✅ Gate A success requires transport + exterior routes, not commit count alone  

---

## §13 — Implementation progress checklist

**Last updated:** 2026-05-30  
**Evidence SoT:** [`docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-*.json`](../reports/) (suffix = milestone)  
**Executable plan:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery.md`](../plans/2026-05-30-rttp-v0-2-core-algorithm-recovery.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Legend:** ✅ done · ⬜ open  

Update this section when a recovery task closes or evidence is recaptured. Do **not** mark Gate B or v0.2A program close until §6 Gate B criteria are met on `recon-l0` class evidence.

### Normative success gates (§6)

| Gate | Status | Evidence / test | Notes |
|------|--------|-----------------|-------|
| **A** — Representative real-map (primary) | **CLOSED** 2026-05-26 | [`after-a6.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a6.json) · `test_rttp_core_recovery_gate_a.py` | Both primary slugs: transport + exterior route + `validation_passed=true`; 62 commits (shortfall is diagnostic, not Gate A fail) |
| **B** — Throughput utilization (secondary) | **OPEN** | Same after-a6 row | `committed=62` / `placement_goal=467`; `throughput_target_shortfall`; needs material move toward target or explicit bounded shortfall attribution per §6 |
| **C** — Tiny pass-capable guard | **CLOSED** | Track B PR #101/#102 · auxiliary tiny row in A0 JSON | `rttp-cert-candidate-tiny-passable-v2` regression guard only |

#### Gate A criteria (per primary slug)

- ✅ `committed_extractors > 0`
- ✅ `committed_output_transport_cells > 0`
- ✅ `committed_route_cells > 0`
- ✅ `exterior_connected_route_count > 0`
- ✅ `validation_passed == true`
- ✅ Fail-closed issue codes `missing_output_transport` / `missing_exterior_route` when transport absent (A6)
- ✅ **Extensions (visibility):** `visible_extension_cell_count >= 1` on primary slugs after **S2b-1** — [`after-s2b1.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-s2b1.json) (`58` on both primaries). ⬜ **Conditional (§6):** ext≥1 route-feasible **and** committed — not Gate A block; tracked with Gate B / A2 track gate.
- ✅ Determinism — covered by Gate A pytest + evidence capture contract
- ⬜ **Commit scale vs goal:** `confirmed_count` toward `placement_goal_count` — **partial** (62/467); tracked under Gate B / `placement_goal_shortfall`, not Gate A block

### Recovery tracks (§5)

#### A0 — Evidence freeze

- ✅ Evidence schema + slug constants (`rttp_recovery_evidence.py`)
- ✅ Read-only extractor + `exterior_connected_route_count` (`rttp_recovery_evidence.py`, `rttp_route_connectivity.py`)
- ✅ `capture_rttp_recovery_evidence` management command
- ✅ `import_rttp_core_recovery_test_map.py` → `rttp-core-recovery-test-map`
- ✅ Baseline JSON + MD — [`baseline.json`](../reports/2026-05-30-rttp-core-recovery-evidence-baseline.json) (signature: ~23 extractors, 0 route/exterior, false-positive validation)
- ✅ Unit tests `test_rttp_recovery_evidence.py`
- ✅ Solver semantics unchanged (evidence tooling only)

#### A1 — Stage diagnosis

- ✅ `rttp_recovery_stage_diagnosis.py` (S1–S8 first-failure map)
- ✅ Evidence rows emit `first_failing_stage`, `blocking_stages`, `diagnostic_flags`, `primary_symptom`
- ✅ Tests `test_rttp_recovery_stage_diagnosis.py`
- ✅ Baseline diagnosis published (primary: **S2** first; `route_cells_zero_but_validation_passed` at baseline)

#### A2 — Candidate / bundle geometry (hypothesis A2-H1)

- ✅ **A2-1** Derive `extension_offsets` from footprint (`miner_placement_topology.py`, `_extension_offsets_from_footprint`, INV-R-03)
- ✅ **A2-2** Propagate to `CatalogPlacementSpec` / `BundleCandidate.pattern`
- ✅ **A2-3** `lin_*` patterns test-only (PR-3 boundary preserved)
- ✅ After-A2 evidence — [`after-a2.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a2.json)
- ✅ Tests `test_miner_placement_topology_extensions.py`
- ✅ **A2 track gate (visibility):** `visible_extension_cell_count > 0` — **CLOSED 2026-05-30 (S2b-1)** — [`after-s2b1.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-s2b1.json). Spec/plan: [`2026-05-30-rttp-extension-topology-synthesis-design.md`](2026-05-30-rttp-extension-topology-synthesis-design.md) · [`2026-05-30-rttp-extension-topology-synthesis.md`](../plans/2026-05-30-rttp-extension-topology-synthesis.md). ⬜ Conditional ext≥1 route-feasible **and** committed; S2b-2 N/S arm families if evidence requires.

#### A3 — Output transport + route materialization

- ✅ **A3-1** FOT in `committed_fixed_output_transport_cells` + overlay merge
- ✅ **A3-2** `reserved_route_cells` includes path toward trunk/goals (`_augment_route_cells_with_output_spine`)
- ✅ **A3-3** `RouteProbeStartPolicy` / `OUTWARD_FROM_RIM` aligned on real maps (FOT PR-2 class)
- ✅ **A3-4** Inter-bundle route segments in overlay/export
- ✅ After-A3 evidence — [`after-a3.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a3.json)
- ✅ **A3.1** Route spine sharing / minimal reservation — [`after-a31.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a31.json) · report [`task-31-spine-sharing.md`](../reports/2026-05-30-rttp-task-31-spine-sharing.md)
- ✅ **Task 3.5** Spine conflict diagnosis (evidence-only) — [`task-35-spine-conflict-diagnosis.md`](../reports/2026-05-30-rttp-task-35-spine-conflict-diagnosis.md)
- ✅ Tests `test_rttp_exterior_route_materialization.py` (and related commit/overlay tests)

#### A4 — Placement coverage goal + shortfall attribution (Task 4)

- ✅ **A4-1** Product `placement_goal_count` from `ReconstructionCompleteMap` × `placement_target_percent` (not ~32 cap)
- ⬜ **A4-2** Selection prefers throughput toward target (regret/evolution tied to `throughput_factor`) — **OPEN** for Gate B
- ✅ **A4-3** Diagnostic shortfall tokens separated from product failure (`placement_goal_shortfall`, not `placement_goal_capped`)
- ✅ Plan slice — [`2026-05-30-rttp-task-4-placement-goal-coverage.md`](../plans/2026-05-30-rttp-task-4-placement-goal-coverage.md)
- ✅ After-A4 evidence — [`after-a4.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a4.json)
- ✅ Tests `test_placement_goal_coverage.py`, `test_placement_goal.py`

#### A5 — Commit / reservation repair

- ✅ **A5-1** No commit without route reservation when trunk required (FL-06 class)
- ✅ **A5-2** `OUTPUT_STUB_NOT_RESERVED` / FOT conflicts → LNS/deferred-retry only (no validation repair)
- ✅ After-A5 evidence — [`after-a5.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a5.json) (62 commits, 0 `output_stub_not_reserved`)
- ✅ Tests `test_rttp_a5_output_stub_reservation.py`

#### A6 — Product regression fixtures + fail-closed validation

- ✅ Issue codes `missing_output_transport`, `missing_exterior_route` (`rttp_layout_issue_codes.py`)
- ✅ Read-only `layout_connectivity_validation.py` wired into pipeline validation
- ✅ Gate A pytest `test_rttp_core_recovery_gate_a.py` + `scripts/test_rttp_core_recovery_gate_a.ps1`
- ✅ `test_rttp_layout_connectivity_validation.py`
- ✅ After-A6 evidence — [`after-a6.json`](../reports/2026-05-30-rttp-core-recovery-evidence-after-a6.json) (`gate_a_passed=true` both primaries)
- ✅ Three slug classes frozen (tiny smoke · diagnostic canon · representative installable)

### Related contracts (outside A0–A6 numbering)

| Item | Status | Notes |
|------|--------|-------|
| **EVTC** exterior-void transport capacity | **In progress** (separate spec) | [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md) · after-evtc: 22 commits, `gate_a_passed=false` on branch experiment — not v0.2A close evidence |
| **D-PR #99** T2 diagnostic observability | **OPEN PR** | Observability-only merge; no blur diagnostic vs algorithm failure (§8) |
| **PR-F3–F5** decontamination | **HOLD** | Gate A materialization met; resume only via `PR_F_*` registry + standing `test_quarantine_registry.ps1` |
| **Macro unpause / full GA** | **PAUSED** | §8 · v0.3+ |

### Program close (v0.2A)

- ✅ Tasks 0–6 implementation plan executed (see plan Task headers)
- ✅ Gate A regression green on primary slugs
- ⬜ Gate B throughput materially improved vs A0 baseline on `rttp-cert-candidate-recon-l0`
- ✅ A2b extensions visible on representative map (S2b-1: `visible_extension_cell_count=58` after-s2b1) · ⬜ ext≥1 committed+route-feasible conditional
- ⬜ Full repo gate (`scripts/test_full.ps1` + mypy + black) on recovery merge branch
- ⬜ Mark **RTTP v0.2A Core Recovery** CLOSED in `current_plan.md` + roadmap language (§9)

### Forbidden shortcuts — ongoing verification (§7)

- ✅ No validation repair in `final_validation`
- ✅ No lowered `throughput_target_percent` on Gate A slugs to fake pass
- ✅ No reclassifying product failure as `expected_diagnostic_shortfall` on primary slugs
- ✅ No weakened FOT / route-domain guards for pass
- ✅ No replay/NDJSON/solver_summary as algorithm inputs
- ✅ No PR-F3–F5 deletes while core recovery evidence at risk
- ✅ No v0.2 CLOSED on tiny fixture only

---

## §14 — References

| Doc | Relevance |
|-----|-----------|
| [`2026-05-30-rttp-ops-authority-tier-design.md`](2026-05-30-rttp-ops-authority-tier-design.md) | T0–T3 diagnosis |
| [`2026-05-30-rttp-tiny-passable-ops-fixture-design.md`](2026-05-30-rttp-tiny-passable-ops-fixture-design.md) | Why tiny pass ≠ product proof |
| [`2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md`](2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md) | Catalog-native candidate path |
| [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md) | Trunk connection principle |
| [`2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md`](2026-05-30-rttp-fl06-output-stub-route-reservation-alignment-design.md) | Prior commit/FOT alignment |
