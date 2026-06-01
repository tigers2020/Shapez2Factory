# grill-me-shapez2 — invariant checklist (reference)

Use during adversarial review. **CANON spec / ADR beats this table** when they conflict.

## Governance · workflow

| Check | Source |
|---|---|
| Spec-first SDD; not test-driven design alone | [AGENTS.md](../../../../AGENTS.md), [workflow.mdc](../../../rules/workflow.mdc) |
| One PR · one purpose | [workflow.mdc](../../../rules/workflow.mdc) |
| Superseded / deleted docs ≠ implementation authority | [START_HERE.md](../../../../documents/ai/START_HERE.md) |
| Contract change → spec amendment → acceptance tests → production | [testing.md](../../../../documents/ai/manuals/testing.md) |
| No production before contract brief (non-trivial behavior) | [protocols/README.md](../../../../protocols/README.md) stage 4 |

## Asteroid Lab · solver (expanded)

| Topic | Challenge if plan… |
|---|---|
| **ReconstructionCompleteMap** | Treats replay/artifact/layout export as solver terrain/capacity input |
| **Layer 3/4 reset** | Cites retired greedy Layer 3/4 plans as authority |
| **Decontamination** | Revives RTTP/MEG or paths removed with tests/docs |
| **Coordinates** | Reintroduces server-coords bridge or wrong frame for persist/fingerprint |
| **Replay** | Feeds metrics/NDJSON/artifact into algorithm; splits timeline against CANON |
| **Route domain** | Patches `route_domain` outside `RouteDomainSnapshotBuilder`; skips commit re-probe |
| **Candidates** | Commits from candidate pool order or uses reachable as final proof |
| **Validation** | Repairs topology/routes in validation |
| **Fitness vs survivability** | Uses commit survivability or replay in GA/solver input |
| **Enums** | Adds free-form failure/event/issue strings |
| **Evolution RNG** | Unseeded random for forced mutation slots |
| **Export** | Changes solver semantics via export-only layers without contract |

Rule file: [asteroid-lab-invariants.mdc](../../../rules/asteroid-lab-invariants.mdc)

Algorithm CANON index:

- [asteroid_lab_01_optimization_input.md](../../../../documents/Algorithm/asteroid_lab_01_optimization_input.md)
- [asteroid_lab_03_candidate_generator.md](../../../../documents/Algorithm/asteroid_lab_03_candidate_generator.md)
- [asteroid_lab_07_incremental_commit.md](../../../../documents/Algorithm/asteroid_lab_07_incremental_commit.md)
- [asteroid_lab_08_validation.md](../../../../documents/Algorithm/asteroid_lab_08_validation.md)
- [asteroid_lab_09_replay_timeline.md](../../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)

Active reset / layer direction (verify `docs/superpowers/specs/` and [current_plan.md](../../../../documents/ai/current_plan.md) — do not assume from memory):

- Layer 3 algorithm reset specs under `docs/superpowers/specs/2026-05-31-layer-03-*`
- Layer 3 rim placement plans under `docs/superpowers/plans/2026-05-31-layer-03-*`

## Tests · gates

| Check | Source |
|---|---|
| Regression: reproducer on HEAD before fix | [AGENTS.md](../../../../AGENTS.md) |
| No `-q` / `--quiet` / `--tb=no` on pytest | [shapez2-core.mdc](../../../rules/shapez2-core.mdc) |
| No green-by-deleting/weakening tests only | [testing.md § Forbidden shortcuts](../../../../documents/ai/manuals/testing.md) |

## Optional deep docs (open when plan touches topic)

- Void belt/pipe exterior installation — search CANON under `docs/superpowers/specs/` and game rules
- M extractor outer-rim anchor — layer-03 plans and reconstruction docs
- CLI boundary — [cli-boundary](../../cli-boundary/SKILL.md) when adding execution entrypoints
