# FL-06 Output Stub / Route Reservation Alignment — Design Spec

**Date:** 2026-05-30  
**Status:** CLOSED (implementation on branch `feat/rttp-fl06-output-stub-reservation`; pending merge)  
**Owner:** RTTP Validation / commit routing domain  
**Scope name:** **FL-06 Output Stub / Route Reservation Alignment**  
**Parent (E-track CLOSED):** [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md) · report [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md`](../reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Executable plan:** [`../plans/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment.md`](../plans/2026-05-30-rttp-fl06-output-stub-route-reservation-alignment.md)

Commit-time route reservation must either **include** `output_stub` in the committed reservation set or **reject** the candidate if `output_stub` cannot be legally reserved. The fix must not blindly union `output_stub` into `reserved_route_cells` when fallback routing proves the stub is not a valid transport start.

**Approval record (2026-05-30):**

1. Primary hypothesis ranking: **H1a > H1b > H3 > H4 > H2** (validation relaxation forbidden).  
2. Investigation before implementation — prove `probe_start`, `probe.path`, and `route_cells` for the FL-06 candidate.  
3. Recommended fix stance: **Option B investigation first** (attachment through stub), not naive Option A.  
4. T2 (throughput) remains deferred until T1b FL-06 resolved.

---

## §1 — Problem

E-track investigation closed T1b as **FL-06**:

```text
reserved_route_cells is non-empty
AND committed candidate.output_stub ∉ reserved_route_cells
```

Run 108 primary failing candidate:

```text
candidate_id: -1,-14:cat_canon_manual_Layout_ShapeMiner_N:shape_belt
output_stub: (-1, -16)
committed_count: 32
conflict_count: 0
```

Catalog audit passed 32/32 with mismatch 0; pipeline composition anomaly was false. This is **not** a catalog footprint mismatch. It is a **route reservation / output_stub alignment contract failure** between incremental commit and final layout validation.

---

## §2 — Evidence

| Evidence | Result |
|----------|--------|
| E-track primary FL | **FL-06** |
| E-track commit | [`90fba2ed`](https://github.com/tigers2020/Shapez2Factory/commit/90fba2ed) |
| SolverRun (canon probe) | **108** |
| Catalog audit | PASS, 32/32, mismatch 0 |
| Pipeline anomaly | false |
| T2 causality | **T2_independent** |
| First failing candidate | `ShapeMiner_N:shape_belt`, stub `(-1,-16)` |

---

## §3 — Current contract (code)

### Validation (FL-06)

[`final_validation.py`](../../../django_apps/asteroid_lab/optimization/validation/final_validation.py):

```python
if candidate.output_stub not in reserved_route_cells and reserved_route_cells:
    return False
```

Normative meaning:

```text
If any route cells were reserved for the committed layout,
every committed candidate.output_stub must appear in reserved_route_cells.
```

### Commit reservation accumulation

[`incremental_commit.py`](../../../django_apps/asteroid_lab/optimization/commit/incremental_commit.py):

```python
probe_start = resolve_route_probe_start(
    anchor_coord=candidate.anchor_coord,
    output_stub=candidate.output_stub,
    domain=current_domain,
    policy=route_probe_start_policy,
)
probe = probe_route(current_domain, probe_start, goals, ...)
route_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
# route_cells merged into committed_route_cells → CommitResult.reserved_route_cells
```

Where:

```python
def _route_cells_from_path(path, occupied):
    return frozenset(cell for cell in path if cell not in occupied)
```

### Probe start resolution (fallback)

[`route_probe_start.py`](../../../django_apps/asteroid_lab/optimization/routing/route_probe_start.py):

```python
if output_stub not in domain.blocked_cells and initial_phase(domain, output_stub) is not None:
    return output_stub
if policy is RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED:
    if initial_phase(domain, anchor_coord) == "platform":
        return anchor_coord
return None
```

### Pipeline default policy

[`pipeline.py`](../../../django_apps/asteroid_lab/optimization/pipeline.py) — normal RTTP with `OUTWARD_FROM_RIM` FOT:

```text
route_probe_start_policy = PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
```

### Potential gap (normative)

```text
probe_start may be output_stub OR fallback anchor (platform).
probe.path is restored from probe_start → goals.
route_cells = path − occupied (stub may be omitted if not on path).
If probe_start ≠ output_stub and stub ∉ path, FL-06 fails at validation despite conflict-free commit.
```

---

## §4 — Non-goals

| Forbidden | Reason |
|-----------|--------|
| Relax / bypass `validate_final_layout` FL-06 | Validation is read-only contract gate |
| Change catalog placement validation | E.2 confirmed pass; separate axis |
| Throughput policy (Track D) | T2_independent |
| Canon slug / map mutation | Diagnostic canon unchanged |
| Replay / solver_summary / NDJSON as algorithm input | Standing forbidden shortcut |
| Introduce route cells through validation module | Layer boundary |
| Option A blind stub union without legality proof | May hide topology bugs |

---

## §5 — Hypothesis ranking

| Rank | ID | Hypothesis | Likelihood | Owner |
|------|-----|------------|------------|-------|
| 1 | **H1a** | Commit-time probe starts from fallback platform/anchor → `probe.path` omits `output_stub` | **Highest** | commit / `resolve_route_probe_start` |
| 2 | **H1b** | Reservation records `probe.path − occupied` but never explicitly ensures stub membership | **High** | `_route_cells_from_path` / commit merge |
| 3 | **H3** | Candidate `output_stub` ≠ commit-time resolved `probe_start` | Investigate | candidate → commit handoff |
| 4 | **H4** | N-direction FOT/stub offset geometry drift (`ShapeMiner_N`) | Check | placement geometry / pattern |
| 5 | **H2** | Validation expects wrong boundary | **Low** — do not weaken validation | — |

---

## §6 — Required questions (pre-implementation)

| ID | Question | Evidence path |
|----|----------|---------------|
| **Q1** | For the FL-06 candidate, what was commit-time `probe_start`? | Instrument `_attempt_commit_one` in narrow test or diagnostic harness |
| **Q2** | Was `probe_start == candidate.output_stub`? | Compare coords |
| **Q3** | Did `probe.path` contain `candidate.output_stub`? | Capture `probe.path` |
| **Q4** | Did `_route_cells_from_path(...)` remove stub from reservation? | `path` vs `route_cells` diff |
| **Q5** | Was `PLATFORM_FALLBACK_WHEN_STUB_BLOCKED` active? | Pipeline / runtime config |
| **Q6** | Are N-direction FOT and stub offsets correct for this candidate? | Pattern + `fixed_output_transport_cell` |

---

## §7 — Fix options

### Option A — Union `output_stub` into `route_cells`

```python
route_cells = frozenset({candidate.output_stub}) | _route_cells_from_path(...)
```

| Pros | Cons |
|------|------|
| Directly satisfies FL-06 wording | Invalid if stub blocked and fallback was intentional |
| Minimal diff | May reserve non-traversable cell |

**Gate:** only if Q1–Q4 prove stub is legal reserved transport cell.

### Option B — Fallback must attach through `output_stub` (recommended investigation target)

If fallback start is used, reservation must include a legal attachment segment:

```text
output_stub → FOT / platform / lift / trunk path
```

| Pros | Cons |
|------|------|
| Preserves validation semantics | More routing / geometry work |
| Rejects illegal stub rather than faking reservation | Direction-specific fixtures |

### Option C — Split reservation DTOs

Separate `reserved_route_cells` vs `attachment_cells`; validation checks stub ∈ attachment set.

| Pros | Cons |
|------|------|
| Semantically precise | Larger contract + replay drift |

---

## §8 — Recommended direction

**Start with Option B investigation, not Option A implementation.**

Spec stance:

```text
commit-time route reservation must either include output_stub in the committed
reservation set OR reject the candidate if output_stub cannot be legally reserved.
```

If Q1–Q4 show stub was valid and simply omitted from path aggregation → minimal **Option A** may apply **after** legality proof. If stub was blocked and fallback used → **Option B** attachment reservation or commit rejection.

---

## §9 — Acceptance criteria

- [ ] Narrow unit/integration fixture reproduces FL-06 (or documents equivalent stub omission)
- [ ] Diagnostic captures `probe_start`, `output_stub`, `probe.path`, `route_cells` for failing candidate
- [ ] Root cause classified (H1a / H1b / H3 / H4)
- [ ] Regression: committed layout with non-empty `reserved_route_cells` ⇒ every stub ∈ reserved
- [ ] Canon slug replay: FL-06 gone; catalog audit still PASS
- [ ] No validation relaxation
- [ ] `current_plan` + roadmap updated on close

---

## §10 — References

- [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md`](../reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md)
- [`harness/investigation/rttp_final_layout_assert_probe.py`](../../../harness/investigation/rttp_final_layout_assert_probe.py)
- [`tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py`](../../../tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py)
- [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md) (if present)
