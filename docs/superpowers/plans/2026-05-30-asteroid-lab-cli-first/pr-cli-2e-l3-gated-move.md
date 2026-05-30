# PR-CLI-2e — L3..L6 + stack_runner Move (GATED on boundary-m-repack stability)

**Type:** refactoring (relocation)
**Depends on:** PR-CLI-2d **AND** L3 boundary-m-repack PR-B/C merged & green
**Enables:** PR-CLI-3b (full pure CLI)
**Branch (suggested):** `feat/asteroid-cli-first-l3-stack-move`

---

## GATE (BA-3) — do not start until ALL true

```text
[ ] 2026-05-30-layer-03-boundary-m-repack-greedy PR-B merged to master
[ ] PR-C (if separate) merged or explicitly out of scope
[ ] Lab gate green on master with new L3
[ ] No open PR currently editing layer_03_rim_mining_bundles/**
```

If the gate cannot be met but the initiative must proceed, the **only** alternative is to move L3 as
**legacy-only** with a retirement banner docstring + tracking issue — never mix algorithm edits here.

## Goal

Relocate `layer_03..layer_06` **and** `stack_runner` into core **in one PR**, so that the moment
stack_runner enters core it already calls in-core L3–L6. This guarantees **no `django_apps` bridge ever
exists in core** — BA-1 is preserved at every committed state.

> **Structural amendment (2026-05-30):** `stack_runner` move was pulled out of PR-CLI-2d into this PR.
> Reason: stack_runner transitively needs L3–L6; moving it earlier forced a `django_apps` bridge that
> violated BA-1. By moving L3–L6 + stack_runner together, core never imports `django_apps`.

## Behavior contract

- L3 greedy / boundary-m-repack behavior identical to post-PR-B master (pure relocation).
- `stack_runner` in core; `run_full_from_cleanup_recon` produces identical `StackRunResult`.
- Zero `django_apps` imports reachable from core; purity gate has no exceptions.

## Non-goals

- No algorithm tuning.
- No CLI (3a already shipped; full run is 3b).

---

## Move set

| From | To |
|------|-----|
| [`layers/layer_03_rim_mining_bundles/`](../../../../django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/) | `application/asteroid_lab/layers/layer_03_rim_mining_bundles/` |
| `layers/layer_04_rim_bundle_placement/` | `application/asteroid_lab/layers/layer_04_rim_bundle_placement/` |
| `layers/layer_05_inner_pattern_fill/` | `application/asteroid_lab/layers/layer_05_inner_pattern_fill/` |
| `layers/layer_06_commit_validate/` | `application/asteroid_lab/layers/layer_06_commit_validate/` |
| [`layers/stack_runner.py`](../../../../django_apps/asteroid_lab/layers/stack_runner.py) | `application/asteroid_lab/stack_runner.py` |

**`stack_runner` clock/flags:** inject `now_fn` + post-summary `enabled` flag so it stays pure;
Django callers pass settings-derived values (the settings-bound `layer_post_summary_log` session remains Django).

## Tasks

- [ ] **Step 0:** Verify GATE checklist; record merged boundary-m-repack SHA in PR description.
- [ ] **Step 1:** Move L3–L6; rewrite imports to core paths; shim originals in `django_apps`.
- [ ] **Step 2:** Move `stack_runner`; point at in-core L3–L6; inject clock/flags.
- [ ] **Step 3:** Confirm **no** `_l3_l6_bridge` exists anywhere; purity gate asserts zero `django_apps` exceptions.
- [ ] **Step 4:** Full layer + stack_runner budget + L3 repack tests.
- [ ] **Step 5:** ruff + mypy + reconstruction gates.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/layers/ -v
python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m mypy django_apps config src
```

## Risks

- `invariant:` 60s budget owned solely by stack_runner; injected clock keeps `LayerBudgetContext` semantics.
- `invariant:` L3 emits `PROVISIONAL_PLACED` + overlay; no `replay/*` import, no L6 commit.
- `invariant:` commit-time latest `route_domain` re-probe; `RouteDomainSnapshotBuilder` sole owner.
- Merge conflict risk if L3 track reopens — keep PR small/fast after gate opens.

## Done criteria

- L3–L6 + stack_runner all in core; no bridge; purity gate clean; behavior identical to master; gates green.
