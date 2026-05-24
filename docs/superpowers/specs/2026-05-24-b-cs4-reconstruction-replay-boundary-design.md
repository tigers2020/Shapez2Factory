# B-CS4 — Reconstruction / Lab Replay Boundary Audit (Design)

**Status:** CLOSED 2026-05-24 — evidence via `test_b_cs4_reconstruction_replay_boundary.py` + `scripts/test_reconstruction_narrow.ps1` (55 pytest)  
**Owner:** asteroid-lab / RTTP Axis B core closure  
**Track:** Boundary audit + narrow gate ownership (**Hybrid C** — formal CLOSED once, then standing regression owner)  
**Scope:** Step 2 reconstruction + Lab reconstruction replay plumbing + PR-C reconstruction/replay decontamination remainder  
**Prerequisite:** B-CS1–B-CS3 CLOSED; strip-solver GATE-1–3 green; `scripts/test_reconstruction_narrow.ps1` green today  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related:**

- [`2026-05-22-strip-solver-keep-recon-complete-design.md`](2026-05-22-strip-solver-keep-recon-complete-design.md) — GATE-1 (`reconstruction/` ↛ `optimization`)
- [`2026-05-24-b-cs3-validation-gate-audit-design.md`](2026-05-24-b-cs3-validation-gate-audit-design.md) — validation / PR-C validation portion (paired milestone)
- [`2026-05-24-repo-decontamination-authority-design.md`](2026-05-24-repo-decontamination-authority-design.md) — PR-C §9 outline
- [`2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md) — RTTP interleave (explicitly **out of scope**)
- [`2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md) — B-CS4 row
- [`documents/ai/contamination_policy.md`](../../../documents/ai/contamination_policy.md)

---

## Problem

Step 2 reconstruction and Lab reconstruction replay are protected mainly by `scripts/test_reconstruction_narrow.ps1` (six behavioral pytest modules + ruff). That harness is strong for **regression** but weak as a **formal Axis B milestone**:

| Area | Gap |
|------|-----|
| PR-C decontamination | Validation portion closed in B-CS3; **reconstruction/replay** portion not consolidated under one PASS authority |
| GATE-1 (strip-solver) | Documented in strip spec; not mirrored as a dedicated B-CS4 AST gate over full `reconstruction/**` |
| Persist ↔ replay ORM | `test_persistence_does_not_read_replay_frames.py` exists but is not the named B-CS4 closure artifact |
| Replay DTO import boundary | `test_unified_replay_modules_import_boundary` is fragment-based and scoped to three timeline modules only |
| Roadmap | B-CS4 marked “ongoing” blurs Axis B **formal closure** vs **standing quality gate** |

B-CS3 closed the validation assertion gate. B-CS4 closes the **reconstruction topology + Lab replay output** boundary with pytest/static evidence, without changing production solver behavior.

---

## Goal

```text
B-CS4 = Reconstruction / Lab Replay Boundary Formal Audit
      + Reconstruction Narrow Gate Standing Owner
```

**Formal audit (CLOSED once):** Prove via AST import guards and persist call sentinels that reconstruction and the audited replay surface cannot import optimization/solver paths, cannot use replay ORM reads on persist authority paths, and do not treat NDJSON / `solver_summary` as algorithm input.

**Standing owner (after CLOSED):** `scripts/test_reconstruction_narrow.ps1` must remain green on every change touching reconstruction/replay contracts (behavioral + B-CS4 boundary module).

---

## Non-goals

| Item | Rationale |
|------|-----------|
| RTTP replay / compose regression | `test_rttp_replay_*`, `lab_rttp_snapshot_compose.py`, `:rttp` interleave — B-CS3 / 3B-S / RTTP narrow `-k rttp` |
| Validation / catalog / commit logic | B-CS3 · D+ authority |
| `run_solver` ops smoke | B-CS2 |
| PR-B optimization contamination token gate (full) | Separate milestone (`test_optimization_contamination_gates.py`) |
| Replay persistence or 3B-S redesign | Output-only contract unchanged |
| Production behavior changes to pass tests | Audit only; leaks → `BLOCKED:` + separate bug PR |
| Including `test_rttp_replay_*` in `test_reconstruction_narrow.ps1` | Would expand B-CS4 beyond step 2 boundary |

---

## Milestone model (Hybrid C)

```text
B-CS4 formal audit     = Axis B reconstruction/replay PR-C absorption + boundary PASS proof
B-CS4 regression owner = scripts/test_reconstruction_narrow.ps1 stays green (not re-opened as ⬜)
```

When the standing gate fails after B-CS4 CLOSED, treat as **regression bug track** — do not revert B-CS4 milestone to ⬜ unless scope contract changes.

---

## North-star invariant

```text
Reconstruction produces topology authority (step 2); it does not import optimization.
Replay/trace toward Lab product is observability output, not algorithm input.
Reconstruction and persist paths do not read ReplayFrame ORM for map authority.
Audited replay DTO modules do not import optimization, solver_runtime, RTTP pipeline, or shapez_solver.
Narrow gate behavioral tests lock fixture topology, replay merge, island_bbox, snapshot contract.
```

Pairs with B-CS3: **validation is assertion gate** ↔ **reconstruction is topology gate; Lab replay is product output**.

---

## Audited surface

### Reconstruction (full tree)

`django_apps/asteroid_lab/reconstruction/**` (all `.py` modules under package; GATE-1 + trace/input contamination).

### Replay (narrow allowlist only)

```text
Replay audited surface:
  - replay/reconstruction_frames.py
  - replay/snapshot_map_replay.py
  - replay/timeline_dtos.py
  - replay/timeline_serialization.py
  - replay/event_types.py
  - replay/replay_enums.py
```

**Explicitly excluded from B-CS4 audit:**

- RTTP replay compose / interleave (`lab_rttp_snapshot_compose.py`, `optimization/replay_sink.py`, `replay_track_keys.py`)
- `replay/recorder.py`, `replay/timeline_composer.py`, `replay/lab_timeline_adapter.py` (RTTP/Lab unified timeline — covered by 3B-S / separate tests)
- `optimization/**`, `validation/**`

### Persist

- `services/reconstructed_map_persist_builder.py`
- `persist_reconstructed_asteroid_map` entry path (via existing integration test pattern)

### Secondary regression (behavioral; not sole PASS authority)

Existing narrow gate modules (unchanged ownership):

- `test_reconstruction_fixture_contract.py`
- `test_reconstruction_persist_full_map_bbox.py`
- `test_reconstruction_replay_merge.py`
- `test_island_bbox.py`
- `test_persistence_does_not_read_replay_frames.py` (superseded for PASS by B-CS4-3 sentinel; keep until equivalent)
- `test_replay_snapshot_contract.py`

**Explicitly excluded from `test_reconstruction_narrow.ps1`:**

```text
exclude test_rttp_replay_*
```

RTTP replay tests remain under RTTP narrow (`-k rttp`) and B-CS3 / 3B-S specs.

---

## PASS authority

```text
Primary (B-CS4 closure):
  - tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py (B-CS4-1 … B-CS4-10)
  - AST import inspection (not source substring alone)
  - Persist ReplayFrame ORM call sentinel (B-CS4-3)
  - scripts/test_reconstruction_narrow.ps1 green (includes test_b_cs4_* + six behavioral modules + ruff)

Secondary (regression, no new ops contract):
  - Existing six narrow pytest modules
  - Optional: python -m pytest tests/unit/asteroid_lab/ -k rttp and not macro_real_map (RTTP sanity; not B-CS4 gate)
```

```text
B-CS2 = ops evidence
B-CS3 = validation boundary evidence
B-CS4 = reconstruction / Lab replay boundary evidence
```

---

## Pass criteria

### B-CS4-1 — GATE-1: `reconstruction/**` ↛ `optimization`

Every `.py` file under `django_apps/asteroid_lab/reconstruction/` must not contain AST `import` / `from` of:

- `django_apps.asteroid_lab.optimization` (any submodule)
- `django_apps.shapez_solver` (legacy solver)

**Authority:** AST walk (same pattern as `test_b_cs3_validation_gate_boundary._forbidden_imports`).

### B-CS4-2 — Audited replay modules ↛ optimization / solver / RTTP pipeline

For each file in **Replay audited surface** (§ Audited surface):

- Must not import `django_apps.asteroid_lab.optimization`, `django_apps.asteroid_lab.services.solver_runtime_entry`, `django_apps.asteroid_lab.services.solver_runtime_pipeline`, `django_apps.shapez_solver`, `django_apps.shapez_core`, `lab_rttp_snapshot_compose`, `optimization.replay_sink`.

**Phase / event string constants:**

```text
Allowed replay phase references are inert string constants only.
They must not import optimization, solver_runtime, RTTP pipeline, or shapez_solver modules.
```

Examples:

- `"optimization_input"`, `"rttp"` as enum/string phase labels — **allowed** when they are literal constants with no optimization module import.
- `from django_apps.asteroid_lab.optimization...` — **forbidden** even if the symbol name contains `"rttp"`.

**Authority:** AST import inspection per audited file.

### B-CS4-3 — Persist ↛ `ReplayFrame` ORM reads

`persist_reconstructed_asteroid_map` (and `reconstructed_map_persist_builder` if it touches ORM) must not invoke common `ReplayFrame.objects` read APIs during persist authority.

```text
PASS authority is call sentinels on ReplayFrame.objects.filter, .get, and .all —
proving those ORM read entrypoints are not invoked during persist.
Source substring checks are supplementary only.
```

**Proof:** `unittest.mock.patch.object` on `m.ReplayFrame.objects.filter`, `.get`, and `.all` during `persist_reconstructed_asteroid_map` — assert each mock was not called (absorb/enhance `test_persistence_does_not_read_replay_frames` in `test_b_cs4_*`).

### B-CS4-4 — Timeline DTO import boundary (PR-C partial)

Consolidate `test_unified_replay_modules_import_boundary` forbidden fragments for:

- `timeline_dtos.py`
- `timeline_serialization.py`
- `replay_enums.py`

Forbidden import prefixes (AST PASS authority — `_TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES` in plan):

- `django_apps.asteroid_lab.models`
- `django_apps.asteroid_lab.services.replay_service`
- `django_apps.asteroid_lab.services.optimization_replay_persist`
- `django_apps.asteroid_lab.services.solver_runtime_pipeline`
- `django_apps.asteroid_lab.services.solver_runtime_entry`
- `django_apps.asteroid_lab.services.runtime_replay_recorder`

Timeline DTO AST test must union `_REPLAY_FORBIDDEN_IMPORT_PREFIXES` **and** `_TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES`. Legacy fragment scan (`_TIMELINE_DTO_FORBIDDEN_FRAGMENTS`) is **supplementary only**.

### B-CS4-5 — `reconstruction_frames` / `snapshot_map_replay` ↛ optimization adapter

Audited replay frame builders must consume reconstruction results only — no direct import of `optimization.reconstruction_adapter` or `optimization/**`.

**Authority:** AST.

### B-CS4-6 — Reconstruction trace ↛ debug algorithm input

`reconstruction/trace.py` (and `pipeline.py` if it reads external debug) must not import NDJSON readers, `solver_summary` parsers, or `:rttp` replay buffer readers as **inputs** to topology decisions.

**Authority:** AST forbidden import prefixes (supplementary source scan allowed, not sole PASS).

### B-CS4-7 — Behavioral narrow gate green

All six existing narrow pytest modules pass without semantic change.

**Authority:** pytest (secondary to B-CS4-1–6, 9; required for B-CS4-8).

### B-CS4-8 — `test_reconstruction_narrow.ps1` closure script

Script runs:

1. Six behavioral modules (unchanged list)
2. `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`
3. ruff on `reconstruction/`, `replay/` (audited replay files + package), `snapshots/island_bbox.py`, `reconstructed_map_persist_builder.py`

**Must not add:** `test_rttp_replay_*` or RTTP compose modules.

### B-CS4-9 — PR-C closure (reconstruction/replay portion)

```text
B-CS4 absorbs the PR-C reconstruction/replay contamination boundary portion only.
B-CS3 already closed the PR-C validation/replay contamination portion.
PR-B (optimization tokens), PR-D (quarantine moves), PR-E (dead code) remain separate.
```

When B-CS4-9 passes, no **additional** PR-C milestone is required **for reconstruction/replay import boundaries and persist↛replay ORM** only.

### B-CS4-10 — No production behavior change

B-CS4 closes only when tests and docs change. Any required production fix for a confirmed leak uses `BLOCKED:` and a **separate** bug PR.

---

## PASS / FAIL summary (closure gate)

**PASS when all hold:**

- `reconstruction/**` AST-clean vs optimization imports (B-CS4-1).
- Six audited replay modules AST-clean vs optimization/solver/RTTP compose (B-CS4-2), with inert phase strings only.
- Persist path proven by **call sentinels** on `ReplayFrame.objects.filter`, `.get`, `.all` (B-CS4-3).
- Timeline DTO boundary consolidated (B-CS4-4).
- Frame builders ↛ optimization adapter (B-CS4-5).
- Reconstruction trace ↛ NDJSON/`solver_summary` algorithm input (B-CS4-6).
- Six behavioral narrow tests + `test_b_cs4_*` + narrow.ps1 + ruff green (B-CS4-7, 8).
- PR-C reconstruction/replay statement satisfied (B-CS4-9).

**FAIL / BLOCKED when any hold:**

- `reconstruction/` imports `optimization`.
- Audited replay module imports optimization, `solver_runtime_*`, `lab_rttp_snapshot_compose`, or `replay_sink`.
- Persist invokes replay ORM reads (sentinel fires).
- Production change attempted inside B-CS4 PR to weaken criteria.
- `test_rttp_replay_*` added to narrow.ps1 (scope leak).

---

## Allowed changes

| Artifact | Allowed |
|----------|---------|
| `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py` (new) | Yes |
| `scripts/test_reconstruction_narrow.ps1` | Add `test_b_cs4_*` only |
| `tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py` | Keep until B-CS4-3 superset proven |
| `tests/unit/asteroid_lab/test_replay_timeline_dto.py` | Keep; B-CS4-4 AST supersedes for PASS |
| `docs/superpowers/specs/`, `plans/` | Yes |
| `documents/ai/current_plan.md`, roadmap | On CLOSED |
| `django_apps/asteroid_lab/reconstruction/**`, audited `replay/**` production | **No** (unless BLOCKED leak fix) |

---

## Forbidden (hard)

- Adding `test_rttp_replay_*` to `test_reconstruction_narrow.ps1`
- Auditing all of `replay/**` (scope creep into RTTP compose)
- Weakening B-CS3 validation boundaries
- Deleting narrow behavioral tests or persistence test before B-CS4 superset passes
- Source-substring-only PASS for persist↛replay (sentinel required)
- Treating RTTP `-k rttp` pytest as primary B-CS4 gate
- Solver / reconstruction logic changes to green tests without separate approval

---

## Deliverables

| Artifact | Action |
|----------|--------|
| This spec | B-CS4 pass/fail authority |
| Implementation plan | [`docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md`](../plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md) |
| Pytest guard suite | B-CS4-1 … B-CS4-10 |
| `scripts/test_reconstruction_narrow.ps1` | Include `test_b_cs4_*` |
| `documents/ai/current_plan.md` | B-CS4 **CLOSED** + **Maintenance / Standing Gates** section |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | B-CS4 ✅; Axis B formal milestones complete |

No application-code PR for B-CS4 unless audit discovers a **confirmed leak**.

---

## If audit finds a leak

```text
BLOCKED:
- missing context: <module, call path>
- risky change: reconstruction/replay reaches optimization or replay ORM authority
- recommended next step: separate bug PR; do not weaken B-CS4 criteria
```

---

## Self-review

| Check | Status |
|-------|--------|
| No TBD / placeholder gates | Pass |
| Hybrid C (formal CLOSED + standing owner) explicit | Pass |
| RTTP replay excluded from narrow.ps1 | Pass |
| Replay audited surface narrow allowlist (not `replay/**`) | Pass |
| B-CS4-2 inert phase strings vs RTTP module import | Pass |
| B-CS4-3 sentinel PASS (`filter` / `get` / `all`) | Pass |
| B-CS4-4 timeline DTO AST prefix union | Pass |
| B-CS1–B-CS3 milestone pattern aligned | Pass |
| PR-C split vs B-CS3 documented | Pass |
| No production behavior change default | Pass |
| Distinguishes B-CS2 ops vs B-CS4 pytest authority | Pass |
