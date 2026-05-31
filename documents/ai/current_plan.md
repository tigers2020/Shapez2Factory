# Current Plan

## Active Baseline

Asteroid Lab currently owns Django-side map input, artifact indexing, replay/viewer
adapters, and cache mirrors. Solver execution is owned by the Django-free
`src/shapez2_factory/` CLI subprocess path. Deleted solver plans and archive material
are not implementation context.

Runtime authority:

```text
Django request -> export game data snapshot -> CLI subprocess -> finalized artifact -> DB index/cache -> replay/viewer
```

`shapez_solver` is a separate factory graph domain and is out of scope for
Asteroid Lab runtime decisions.

## Active Work — Asteroid Lab CLI-first extraction

**ACTIVE (PR-CLI-0…6).** Extracting the Asteroid Lab solver into a Django-free core
(`src/shapez2_factory/`) that runs as a CLI subprocess emitting a hash-verified artifact
directory (`var/runs/<run_key>/`); DB demotes to run registry / artifact index only.

- Contract: [`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) · [`ADR-006`](../../docs/adr/ADR-006-asteroid-lab-cli-first-artifact.md)
- Plan set + tracker: [`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](../../docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md)
- Current status: PR-CLI-0..6 implementation on branch after merge with `origin/master` (#134 L3–L6,
  #135 pipeline). `subprocess_only` request path, artifact ingest, artifact-first replay, BA-9 terminal
  logs, replay viewer import gate. Artifact viewer compose reads stored artifact records only; Django no
  longer reruns L2/L3 to enrich replay. Remaining optional: shim import-path retirement; repo-wide mypy
  baseline.
- Done through PR-CLI-6 on branch; merged master through `b566d4f8`. Evidence:
  [`django-residue-audit.md`](../../docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/django-residue-audit.md).

## Active Work — Asteroid Lab replay renderer perf (PR-RENDER-0…6)

**PARTIAL (working tree; not merged).** Lab replay renderer perf PR-RENDER-0..5 landed; PR-RENDER-6
**not-triggered**. Functional sign-off (Run 7 browser); budget sign-off open (LOCK-2, rAF p95 ≤16.7ms).

- Plan set + tracker: [`docs/superpowers/plans/2026-05-31-asteroid-lab-replay-renderer-perf/`](../../docs/superpowers/plans/2026-05-31-asteroid-lab-replay-renderer-perf/README.md) — checklist status **PARTIAL**
- Approval locks: LOCK-1 OK · LOCK-2 partial (Run 3 ~563 touch) · LOCK-3 RENDER-6 skipped
- Runtime fixes: canvas wiring restored from `bc5071e2`; lazy prefetch/retry; `tone` in `renderFullMapCells`; `mountLabCanvasRenderer` on lazy hydrate
- Status: Run 9 — run 300 rAF p95 **13.8 ms** (budget met); LOCK-2 canvas hit-layer still partial (~2961 on resets)

## Active Work — Layer 03 algorithm reset (CLI-first stub)

**ACTIVE (spec APPROVED 2026-05-31).** Remove PR-B greedy/pass/append implementation; keep L3 stack
slot, DTO compatibility, and minimal replay stub (`reset_stub_v1` / `Layer03SkipReason.ALGORITHM_RESET`).
Replacement algorithm is a **separate** future spec. Implementation plan not started.

- Design (SoT): [`docs/superpowers/specs/2026-05-31-layer-03-algorithm-reset-design.md`](../../docs/superpowers/specs/2026-05-31-layer-03-algorithm-reset-design.md)
- Supersedes: PR-B boundary-m-repack greedy, directional segment-packing (never landed)
- Plan: [`docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/README.md`](../../docs/superpowers/plans/2026-05-31-layer-03-algorithm-reset/README.md) — checklist **NOT STARTED**

## Superseded — Layer 03 boundary-m-repack (PR-B)

**SUPERSEDED (2026-05-31).** Greedy algorithm removed per reset spec; historical reference only.

- Design: [`docs/superpowers/specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../docs/superpowers/specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md)
- Plan: [`docs/superpowers/plans/2026-05-30-layer-03-boundary-m-repack-greedy/`](../../docs/superpowers/plans/2026-05-30-layer-03-boundary-m-repack-greedy/README.md)

## Superseded — Layer 03 directional rim segment packing

**SUPERSEDED (2026-05-31, never implemented).** Replaced by L3 reset + future greenfield L3 spec.

## Authority Precedence

1. Code under `src/shapez2_factory/` for solver execution, plus Django request/index/viewer adapters
   under `django_apps/asteroid_lab/services/solver_runtime_entry.py`,
   `solver_subprocess_runner.py`, `artifact_ingest.py`, and `lab_replay_persisted_cache.py`
2. This file for current queue and standing gates
3. [`documents/index/document_inventory.md`](../index/document_inventory.md)
4. Current `documents/Algorithm/asteroid_lab_*.md` files
5. Current tests

Deleted document content is not authority.

## Active Code Paths

```text
src/shapez2_factory/interfaces/cli/asteroid_solve.py
src/shapez2_factory/application/asteroid_lab/
django_apps/asteroid_lab/services/solver_runtime_entry.py
django_apps/asteroid_lab/services/solver_subprocess_runner.py
django_apps/asteroid_lab/services/artifact_ingest.py
django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
django_apps/web/views/public_pages.py
```

## Verification

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_capacity_sot.ps1
```

Full gate: see [`AGENTS.md`](../../AGENTS.md).

## Next Focus

Open new work from current code, current tests, and
[`document_inventory.md`](../index/document_inventory.md). Add or update current
plans only when the task needs a written implementation plan.
