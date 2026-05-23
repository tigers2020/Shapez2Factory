# RTTP v1 MacroBundleT3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan **one PR slice at a time** (PR-A → PR-H). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement v1 MacroBundleT3 per [`2026-05-23-rttp-v1-macrobundle-t3-design.md`](../specs/2026-05-23-rttp-v1-macrobundle-t3-design.md) — three `BundleCandidate` footprints + shared lift/trunk intent as **one** selection/commit slot, without breaking v0.1 RTTP-G1~G8.

**Architecture:** Add `optimization/macros/` (DTOs, compiler, macro probe) beside existing `candidates/` / `selection/` / `commit/`. v0.1 single-bundle generator stays; v1 path is gated by **`macro_only_mode`** on pipeline config. Selection/regret/commit operate on **`macro_id`** only when flag is on — **no** mixing singleton `BundleCandidate` and `MacroBundleCandidate` in one genome (OD-MACRO-1 **locked No**).

**Tech Stack:** Python 3.12+, frozen dataclasses, `StrEnum`, pytest; CANON throughput [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md).

**Spec status:** Algorithm direction **approved** (2026-05-23). Locked decisions: OD-MACRO-1..5 in spec § Locked decisions.

**Baseline policy:** Before each PR merge, `python -m pytest tests/unit/asteroid_lab/ -k rttp` must stay green. v0.1 gates G1~G8 must not regress when `macro_only_mode=False` (default pipeline behavior).

**Out of v1:** DB `run_solver` + `:rttp` hardening (defer until PR-H merged or small hardening PR **before PR-A only** if replay schema drift blocks tests — not parallel to PR-A..H). Merger auto-place, trunk JPS, CP-SAT, 3-miner `BundlePattern`.

**Worktree (recommended):** `F:\Python_Projects\shapez2Factory\.worktrees\rttp-v1-macro` · branch `feature/rttp-v1-macrobundle-t3`

**Plan status:** Ready for execution (docs-only plan PR; code starts at PR-A)

---

## Spec → plan coverage

| Spec § | Plan slice |
|--------|------------|
| §1 DTOs | PR-A |
| §2–3 Child rules + disjoint occupancy | PR-B (compiler) |
| §4–5 Shared lift / ring intent | PR-B (compiler + probe), PR-E (commit) |
| §6 Macro generation | PR-B |
| §7 Equivalence | PR-C |
| §8 Score / regret | PR-D |
| §9–10 Atomic commit / rollback | PR-E |
| §6 pool + pipeline | PR-F (`macro_only_mode`) |
| §11 Replay metrics | PR-G |
| §12 Validation | PR-H |
| §13 RTTP-G9~G16 | Per-PR gate column below |

---

## Locked decisions (do not re-open without spec amendment)

| ID | Decision |
|----|----------|
| **OD-MACRO-1** | **No** mixed genome — v1 selection is **macro-only** when `macro_only_mode=True`. Single `BundleCandidate` ids never appear in `PlacementGenome.commit_order`. Config `allow_singleton_genome_slots` stays **false**; do not implement mixed-mode regret. |
| OD-MACRO-2 | `macro_throughput_factor` = **sum** of child throughput factors |
| OD-MACRO-3 | `max_macro_candidates: int = 64` on `RttpPipelineConfig` |
| OD-MACRO-4 | **No** new product `event_type`; enrich existing four `rttp.*` milestones only |
| OD-MACRO-5 | LNS **swaps macro slots**; compiler deterministic (no re-randomize children mid-LNS) |

---

## Target package layout (incremental)

```text
django_apps/asteroid_lab/optimization/
  macros/
    __init__.py
    macro_dtos.py              # MacroBundleT3, MacroBundleCandidate, SharedLiftStubPlan, SharedRingPortIntent
    macro_reject_reason.py     # MacroRejectReason StrEnum
    macro_compiler.py          # compile_macros(...) -> MacroGenerationResult
    macro_probe.py             # macro-level route probe (shared segment)
  selection/
    macro_equivalence.py       # MacroEquivalenceKey, dedupe_macros
    macro_greedy_regret.py     # select_macro_genome (macro pool only)
  commit/
    incremental_macro_commit.py  # incremental_commit_macro (atomic 3-child)
  input_contracts.py           # extend RttpPipelineConfig: macro_only_mode, max_macro_candidates, ...
  pipeline.py                  # branch: macro_only_mode → macro path
  rttp_replay_diagnostics.py   # macro metrics/overlays (PR-G)
  validation/final_validation.py  # macro layout asserts (PR-H)
```

`Coord` import rule unchanged: only via `optimization/coords.py`.

---

## Config contract (PR-A stub, PR-F wire)

Add to `input_contracts.py` (or dedicated `pipeline_config.py` if file grows):

```python
@dataclass(frozen=True, slots=True)
class RttpPipelineConfig:
  macro_only_mode: bool = False          # v1 tests + greenfield macro pipeline use True
  allow_singleton_genome_slots: bool = False  # OD-MACRO-1: must stay False in v1
  max_macro_candidates: int = 64
  # existing v0.1 fields preserved ...
```

- **`macro_only_mode=False`:** Current `pipeline.py` behavior (G1~G8 regression path).
- **`macro_only_mode=True`:** Generate children → compile macros → dedupe → macro regret → macro commit → validation. **Never** call `select_genome` on `normal_candidates` for genome slots.

---

## Test file (single home for G9+)

Create once in PR-B (expand through PR-H):

```text
tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py
tests/support/macro_triple_greenfield_fixture.py   # small grid, 3 non-overlapping anchors + shared lift
```

Narrow gate after each PR:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py -v
python -m pytest tests/unit/asteroid_lab/ -k rttp
```

---

## PR-A — Macro DTOs + `MacroRejectReason` (no runtime wiring)

**Gate:** Types importable; StrEnum stable; **no** `pipeline.py` / `solver_runtime_entry` changes.

**Files:**

- Create: `optimization/macros/__init__.py`, `macro_dtos.py`, `macro_reject_reason.py`
- Create: `tests/unit/asteroid_lab/test_rttp_macro_dtos.py` (frozen, hash, `macro_id` charset smoke)
- Modify: none of `pipeline.py`, `candidate_generator.py` wiring

**`MacroRejectReason` (minimum set — extend only with spec + test):**

```python
class MacroRejectReason(StrEnum):
    CHILD_OCCUPANCY_OVERLAP = "child_occupancy_overlap"
    RING_PORT_MISMATCH = "ring_port_mismatch"
    SHARED_LIFT_UNREACHABLE = "shared_lift_unreachable"
    CHILD_NOT_IN_NORMAL_POOL = "child_not_in_normal_pool"
    TRANSPORT_KIND_MISMATCH = "transport_kind_mismatch"
    PROTECTED_CORRIDOR_CONFLICT = "protected_corridor_conflict"
    EXCEEDS_MAX_MACRO_CANDIDATES = "exceeds_max_macro_candidates"
```

- [ ] **Step 1:** Implement DTOs per spec §1 (`MacroBundleT3`, `MacroBundleCandidate`, `SharedLiftStubPlan`, `SharedRingPortIntent`).
- [ ] **Step 2:** Implement `macro_id` helper (deterministic hash of sorted child ids + canonical JSON of shared plans).
- [ ] **Step 3:** DTO tests — overlap detection helper on `combined_occupancy` is compile-time only (no compiler yet).
- [ ] **Step 4:** `python -m ruff check django_apps/asteroid_lab/optimization/macros tests/unit/asteroid_lab/test_rttp_macro_dtos.py`
- [ ] **Step 5:** `python -m pytest tests/unit/asteroid_lab/ -k rttp` (full rttp — must pass; new file only additive).
- [ ] **Step 6:** Commit `feat(rttp): macro DTOs and MacroRejectReason (PR-A)`

---

## PR-B — Macro compiler red tests + minimal compiler — **RTTP-G9**, **RTTP-G10**

**Gate:** Valid triple → one `MacroBundleCandidate`; overlapping footprints → `CHILD_OCCUPANCY_OVERLAP`; missing shared lift → `SHARED_LIFT_UNREACHABLE`.

**Files:**

- Create: `optimization/macros/macro_compiler.py`, `macro_probe.py`
- Create: `tests/support/macro_triple_greenfield_fixture.py`
- Create: `tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py` (compiler + probe cases)
- Modify: `optimization/macros/__init__.py` exports

- [ ] **Step 1:** Red — `test_macro_compiler_emits_one_candidate_for_valid_triple` (RTTP-G9).
- [ ] **Step 2:** Red — `test_macro_compiler_rejects_overlap` → `CHILD_OCCUPANCY_OVERLAP`.
- [ ] **Step 3:** Red — `test_macro_probe_rejects_unreachable_shared_trunk` (RTTP-G10).
- [ ] **Step 4:** Green — minimal `compile_macros(normal_candidates, skeleton, inp, config) -> MacroGenerationResult` with `macro_normal` / `macro_rejected` pools.
- [ ] **Step 5:** Cap enumeration at `max_macro_candidates` (OD-MACRO-3).
- [ ] **Step 6:** pytest macro file + `pytest -k rttp`; commit `feat(rttp): macro compiler and probe (PR-B)`

---

## PR-C — Macro equivalence / dedupe — **RTTP-G11**

**Gate:** Duplicate macro keys collapse deterministically (lowest `macro_id` wins).

**Files:**

- Create: `optimization/selection/macro_equivalence.py`
- Modify: `test_rttp_macro_bundle_t3.py`

- [ ] **Step 1:** Red — `test_macro_equivalence_dedupe_deterministic` (same triple permutations → one survivor).
- [ ] **Step 2:** Green — `MacroEquivalenceKey` + `dedupe_macros` mirroring `equivalence.dedupe_candidates`.
- [ ] **Step 3:** pytest + ruff; commit `feat(rttp): macro equivalence dedupe (PR-C)`

---

## PR-D — Macro regret selector, macro-only genome — **RTTP-G12**

**Gate:** `select_macro_genome` returns `commit_order` of **`macro_id`** only; regret uses macro pool; **no** code path adds `BundleCandidate.candidate_id` to genome when `macro_only_mode=True`.

**Files:**

- Create: `optimization/selection/macro_greedy_regret.py`
- Modify: `test_rttp_macro_bundle_t3.py`
- Modify: `input_contracts.py` — add `RttpPipelineConfig` fields if not done in PR-A

- [ ] **Step 1:** Red — `test_macro_regret_commit_order_uses_macro_ids_only` (RTTP-G12).
- [ ] **Step 2:** Red — assert `allow_singleton_genome_slots=False` rejects singleton slot injection (guard test).
- [ ] **Step 3:** Green — `select_macro_genome(macro_normal, domain, config) -> PlacementGenome` with `macro_throughput_factor` sum (OD-MACRO-2).
- [ ] **Step 4:** Do **not** wire pipeline yet (PR-F).
- [ ] **Step 5:** pytest + ruff; commit `feat(rttp): macro-only greedy regret (PR-D)`

---

## PR-E — Atomic macro commit red → green — **RTTP-G13**

**Gate:** Success commits all three child ids; reprobe failure commits **zero**; domain version increments once per macro.

**Files:**

- Create: `optimization/commit/incremental_macro_commit.py`
- Modify: `candidate_dtos.py` or `commit` types only if `CommitConflictReason` needs `MACRO_CHILD_CONFLICT` (spec-allowed)
- Modify: `test_rttp_macro_bundle_t3.py`

- [ ] **Step 1:** Red — `test_macro_commit_all_or_nothing_success`.
- [ ] **Step 2:** Red — `test_macro_commit_reprobe_failure_rolls_back` (0 of 3 children committed).
- [ ] **Step 3:** Green — `incremental_commit_macro` wraps three internal `incremental_commit` calls in snapshot/rollback; external API macro-only.
- [ ] **Step 4:** pytest + ruff; commit `feat(rttp): atomic macro commit (PR-E)`

---

## PR-F — Pipeline `macro_only_mode` — **RTTP-G14**

**Gate:** `run_rttp_pipeline(..., config=macro_only_config)` deterministic across two runs; v0.1 default config unchanged and G1~G8 green.

**Files:**

- Modify: `optimization/pipeline.py`
- Modify: `optimization/input_contracts.py` — `RttpPipelineConfig`
- Create: `tests/unit/asteroid_lab/test_rttp_pipeline_macro_greenfield.py` (or extend macro test module)
- Do **not** change default `ASTEROID_LAB_RTTP_ENABLED` behavior to macro-only until explicitly requested

- [ ] **Step 1:** Red — `test_macro_only_pipeline_deterministic` (RTTP-G14) using `macro_triple_greenfield_fixture`.
- [ ] **Step 2:** Green — pipeline branch: skeleton → `generate_candidates` → `compile_macros` → `dedupe_macros` → `select_macro_genome` → macro commit loop → validation.
- [ ] **Step 3:** Red — `test_v01_pipeline_unchanged_when_macro_only_false` (smoke: existing greenfield test config).
- [ ] **Step 4:** `python -m pytest tests/unit/asteroid_lab/ -k rttp`
- [ ] **Step 5:** Commit `feat(rttp): macro-only pipeline mode (PR-F)`

---

## PR-G — Replay metrics / overlay enrichment — **RTTP-G15**

**Gate:** `PipelineResult` identical with replay sink on/off; four `rttp.*` types unchanged; metrics per spec §11.

**Files:**

- Modify: `optimization/rttp_replay_diagnostics.py`, `replay_sink.py` call sites in `pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_replay_parity.py` or macro test — extend G8 pattern

- [ ] **Step 1:** Red — `test_macro_pipeline_replay_parity` (RTTP-G15): same committed ids / macro_ids replay on vs off.
- [ ] **Step 2:** Green — add `macro_normal_count`, `committed_macro_ids`, shared lift overlay on `rttp.candidate_pool_snapshot` / `rttp.commit_domain_snapshot` per spec table.
- [ ] **Step 3:** Confirm Lab compose tests still pass: `test_lab_rttp_snapshot_compose.py` (no new `event_type`).
- [ ] **Step 4:** Commit `feat(rttp): macro replay metrics enrichment (PR-G)`

---

## PR-H — Validation, import boundary, G9~G16 sweep — **RTTP-G16** + doc sync

**Gate:** Read-only validation for macro layout; `optimization/` does not import `lab_rttp_snapshot_compose`; all G9~G16 green; `asteroid_lab_10` v1 gate row updated.

**Files:**

- Modify: `optimization/validation/final_validation.py` (or `validate_macro_layout` wrapper)
- Modify: `documents/Algorithm/asteroid_lab_10_development_sequence.md` — v1 MacroBundleT3 gates
- Modify: `documents/ai/current_plan.md` — v1 implementation in progress / done

- [ ] **Step 1:** Red — validation rejects disjoint violation post-commit (assert-only).
- [ ] **Step 2:** Red — `test_optimization_import_boundary_no_lab_compose` (RTTP-G16) — `rg` forbidden import.
- [ ] **Step 3:** Run full macro gate file + `pytest -k rttp`.
- [ ] **Step 4:** Optional: one reconstruction fixture line through `macro_only_mode=True` (P1 smoke) — only if fixture reliably yields ≥3 normal children; else defer.
- [ ] **Step 5:** Commit `test(rttp): macro validation and G9-G16 sweep (PR-H)`

---

## Merge checklist (each PR)

| Item | Command / evidence |
|------|-------------------|
| RTTP-G1~G8 | `python -m pytest tests/unit/asteroid_lab/ -k rttp` with default pipeline |
| RTTP-G9+ (slice) | `python -m pytest tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py -v` |
| reconstruction boundary | `rg "from django_apps\.asteroid_lab\.optimization" django_apps/asteroid_lab/reconstruction` → no matches |
| ruff | `python -m ruff check django_apps/asteroid_lab/optimization` |
| mypy | `python -m mypy django_apps/asteroid_lab/optimization` when package stable |
| Forbidden | No `BundlePattern` with 3 miners; no mixed genome (OD-MACRO-1) |

---

## DB integration (explicitly deferred)

Do **not** start DB hardening in parallel with PR-A..H.

Allowed **before PR-A** only: tiny PR that fixes broken fixture persistence blocking tests (no macro code).

After **PR-H**: small PR — `run_solver` on fixture → `SolverRun` → `:rttp` track → four canonical frames → Lab interleaved timeline (no `inherited_snapshot`).

---

## Execution handoff

Plan: `docs/superpowers/plans/2026-05-23-rttp-v1-macrobundle-t3.md`

**Choose execution mode:**

1. **Subagent-driven (recommended)** — one subagent per PR slice (A→H), review between merges
2. **Inline** — this session runs PR-A pre-flight + DTOs with checkpoints

Reply with `PR-A` to start implementation, or review plan PR first.
