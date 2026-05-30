# ADR-006: Asteroid Lab CLI-first artifact extraction

- **Status**: Accepted
- **Date**: 2026-05-30
- **Owner**: Asteroid Lab core extraction (`src/shapez2_factory/`)
- **Supersedes / relates to**: ADR-004 (game_data snapshot boundary), ADR-005 (L3 absorbs rim greedy placement)

## Context

The Asteroid Lab solver currently lives entirely inside `django_apps/asteroid_lab/**`. It is coupled
to Django ORM, settings, and the replay/web viewer layer. This blocks three goals:

1. **Determinism + reproducibility** — a run's solver state is entangled with DB rows, so re-running
   or auditing a run is not byte-reproducible.
2. **Isolation** — the solver hot path cannot be exercised without a Django environment, slowing
   tests and preventing a clean process/timeout boundary.
3. **Operability** — there is no atomic, hash-verified artifact a run produces; replay is rebuilt
   from DB-resident payloads.

A multi-PR plan set ([`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](../superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md))
and a normative spec ([`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md))
define the target. This ADR records the architectural decision and its constraints.

## Decision

1. **Pure core package** — extract the solver into `src/shapez2_factory/` (hexagonal: `domain`,
   `application`, `adapters`, `interfaces`, `bootstrap`). The core MUST NOT import `django`,
   `django_apps`, or `config` (BA-1). Shims point one direction only (Django → core).
2. **CLI-first artifact** — the core runs as a CLI subprocess and emits an atomic, hash-verified
   **artifact directory** under `var/runs/<run_key>/` with `manifest.json` written last (BA-5). The
   manifest schema, `replay_core.jsonl` line schema, run lifecycle enum, subprocess contract, and
   `game_data_snapshot.json` fail-closed rules are normative in the spec.
3. **DB demoted to index** — `SolverRun` and related tables become a **run registry / artifact index
   / option cache**, never the solver state source of truth (frozen decision FD-3). Django performs
   **enrichment + viewer** work only; it MUST NEVER rewrite `manifest.json`.
4. **Phased, non-monolithic migration** — moves are split across PR-CLI-2a … 2e (no single move PR,
   BA-2). L3–L6 + `stack_runner` relocate together in PR-CLI-2e, **gated** on the boundary-m-repack
   PRs landing green (BA-3). No `django_apps` bridge is ever left inside core.
5. **Subprocess-only target** — the end state (PR-CLI-6, Option A) removes in-process solver
   invocation from the request path entirely; the viewer has an import gate forbidding core imports.

## Consequences

### Positive

- Solver runs become byte-reproducible: the artifact directory + content hashes pin every output.
- The core is testable and runnable without Django; process/timeout/path-traversal boundaries are
  explicit (BA-7).
- Clear ownership: core owns the deterministic stream; Django owns enrichment, indexing, and viewing.

### Negative / constraints

- Adding any `django`/`django_apps`/`config` import into `src/shapez2_factory/**` requires amending
  this ADR and is blocked by `tests/unit/architecture/test_shapez2_factory_core_purity.py`.
- A migration window exists where shims re-export moved symbols; shim identity is asserted
  (`test_contract_shims_preserve_identity`, PR-CLI-2d) to prevent divergence.
- Two lifecycles coexist (artifact vs DB); the spec's authority split keeps them from conflicting.

### Trade-offs

- The subprocess hop adds latency and a log/exit-code surface, accepted in exchange for isolation and
  reproducibility.
- Artifact storage under `var/runs/` grows with run count; retention/cleanup is out of scope here and
  deferred to a later operational decision.

## Alternatives considered

- **Option 2 — neutral top-level package (not under `src/`)**: rejected for now to keep the existing
  `src/shapez2_factory/` hexagonal scaffold and tooling (`mypy src`, purity gate path) intact.
- **In-process extraction without a CLI/artifact boundary**: rejected — it would not deliver
  reproducible artifacts nor a clean process/timeout boundary, leaving the DB as de-facto SoT.
- **Single monolithic move PR**: rejected (BA-2) — too large to review safely and would force a
  `django_apps` bridge in core during the transition.

## References

- Spec: [`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md)
- Plan set: [`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md`](../superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md)
- Purity gate: `tests/unit/architecture/test_shapez2_factory_core_purity.py`
- Related: [`ADR-004-game-data-snapshot-boundary.md`](ADR-004-game-data-snapshot-boundary.md), [`ADR-005-layer03-absorbs-rim-greedy-placement.md`](ADR-005-layer03-absorbs-rim-greedy-placement.md)
- Asteroid Lab invariants: [`.cursor/rules/asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc)
- ADR template: [`ADR-0000-template.md`](ADR-0000-template.md)
