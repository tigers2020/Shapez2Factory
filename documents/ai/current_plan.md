# Current Plan

## Active Baseline

Asteroid Lab currently owns reconstruction, cleanup, replay, snapshot contracts,
and the fail-closed runtime entry. Deleted solver plans and archive material are
not implementation context.

Runtime authority:

```text
decode -> cleanup -> reconstruction -> ReconstructionCompleteMap -> persist -> replay
```

`shapez_solver` is a separate factory graph domain and is out of scope for
Asteroid Lab runtime decisions.

## Active Work — Asteroid Lab CLI-first extraction

**ACTIVE (PR-CLI-0…6).** Extracting the Asteroid Lab solver into a Django-free core
(`src/shapez2_factory/`) that runs as a CLI subprocess emitting a hash-verified artifact
directory (`var/runs/<run_key>/`); DB demotes to run registry / artifact index only.

- Contract: [`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) · [`ADR-006`](../../docs/adr/ADR-006-asteroid-lab-cli-first-artifact.md)
- Plan set + tracker: [`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](../../docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md)
- Done: PR-CLI-0 (spec/ADR/BA-1 purity gate) · PR-CLI-1 (scaffold + `AtomicArtifactWriter` BA-5 + ports/use-case stub). Next: PR-CLI-2a pure DTO move.

## Active Work — Layer 03 boundary-m-repack (PR-B)

**ACTIVE.** Algorithm enhancement: place the highest-yield canonical bundle `m3e_01` (miner + 3
extensions) along the outer rim with in-layout degradation 3→2→1, keeping all M/E equipment on the
field and using exterior void only for the output stub + transport route. Unblocks (gates) PR-CLI-2e.

- Design (SoT): [`docs/superpowers/specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../docs/superpowers/specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md)
- Plan + checklist: [`docs/superpowers/plans/2026-05-30-layer-03-boundary-m-repack-greedy/`](../../docs/superpowers/plans/2026-05-30-layer-03-boundary-m-repack-greedy/README.md)
- Status: algorithm body green (Gate A: `pytest tests/unit/asteroid_lab/layers/ -v` passed; combined layers+replay 173 passed); docs landed; Gate C manual DB smoke recorded not-reproducible (no deterministic project slug), covered by deterministic run-solver L3 runtime tests (7 passed). Not merged; no commit/PR yet.

## Authority Precedence

1. Code under `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`,
   `contracts/`, and `services/solver_runtime_entry.py`
2. This file for current queue and standing gates
3. [`documents/index/document_inventory.md`](../index/document_inventory.md)
4. Current `documents/Algorithm/asteroid_lab_*.md` files
5. Current tests

Deleted document content is not authority.

## Active Code Paths

```text
django_apps/asteroid_lab/reconstruction/
django_apps/asteroid_lab/cleanup/
django_apps/asteroid_lab/replay/
django_apps/asteroid_lab/contracts/
django_apps/asteroid_lab/genetic_sample/
django_apps/asteroid_lab/services/solver_runtime_entry.py
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
