# Document Inventory

As of: 2026-06-12
Scope: Current document authority under `documents/` and `docs/`.

Status enum follows [`document_lifecycle.md`](document_lifecycle.md). Deleted
archive and outdated documents are not valid implementation context.

## Canonical Documents

| Document | Status | Kind | Canonical | Notes |
|---|---|---|---|---|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | Routing, gates, approval boundaries |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | `CANON` | rule | YES | Cursor rule surface |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context selection |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | On-demand manuals by work type |
| [`documents/index/document_lifecycle.md`](document_lifecycle.md) | `CANON` | document governance | YES | Current-only document policy |
| [`documents/index/document_inventory.md`](document_inventory.md) | `CANON` | document governance | YES | Current authority map |
| [`docs/adr/`](../../docs/adr/) | `CANON` | architecture decisions | YES | Accepted ADRs |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 rules and solver domain abstraction |
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) | `CANON` | domain throughput | YES | Asteroid Miner/Pump and Space Belt/Pipe rates |

## Active Work

| Document | Status | Kind | Canonical | Notes |
|---|---|---|---|---|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | Current queue and gates |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | Progress state and verification gates |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | Current or pending implementation plans |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | Scoped implementation plans |
| [`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) | `ACTIVE` | design spec | YES | CLI-first artifact contract (BA-1…8, manifest/replay_core schema); paired [ADR-006](../../docs/adr/ADR-006-asteroid-lab-cli-first-artifact.md) |
| [`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](../../docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md) | `ACTIVE` | plan set | NO | Per-PR plan set (PR-CLI-0…6) + master `checklist.md` |

## Asteroid Lab Authority By Topic

When documents disagree, use current code and the topic row below. Deleted plans,
deleted specs, and archive history are not authority.

| Topic | Authority for implementation | Notes |
|---|---|---|
| Runtime entry / Run Solver | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Fail-closed runtime |
| Reconstruction topology | `django_apps/asteroid_lab/reconstruction/` | Coordinate and topology contract |
| Replay timeline | [`docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`](../../../../docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md) + `django_apps/asteroid_lab/replay/timeline_dtos.py` | Product replay; former `asteroid_lab_09` → [`authority-redirect.md`](../algorithm/authority-redirect.md) |
| Replay wiring | `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py` + CLI-first artifact spec | Output-only replay; former `asteroid_lab_12` → redirect ledger |
| Algorithm doc routing | [`authority-redirect.md`](../algorithm/authority-redirect.md) + wiki `algorithm-doc-authority` | Replaces deleted `documents/Algorithm/` tree |
| Terminology map | [`docs/ubiquitous-language.md`](../../../../docs/ubiquitous-language.md) | Canonical / alias / ambiguous terms |
| Game data snapshot | `django_apps/asteroid_lab/contracts/game_data_snapshot*.py` + [`docs/domain/asteroid_game_data_snapshot.md`](../../docs/domain/asteroid_game_data_snapshot.md) | Boundary DTO contract |
| `shapez_solver` | `django_apps/shapez_solver/` | Separate factory graph domain |

## Research And Reports

| Document | Status | Kind | Canonical | Notes |
|---|---|---|---|---|
| [`project_harness_research.md`](../../project_harness_research.md) | `RESEARCH` | harness design | NO | Agent operations research |
| [`documents/research/`](../research/) | `RESEARCH` | evidence | NO | Current research only |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | Current report routing |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | Current debug evidence |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | Current notes |
| [`raw/algorithm/README.md`](../algorithm/README.md) | `ACTIVE` | algorithm index | YES | Current tree; only `asteroid_lab_11` ACTIVE — see redirect ledger |
| [`raw/algorithm/authority-redirect.md`](../algorithm/authority-redirect.md) | `ACTIVE` | redirect ledger | YES | Stale `documents/Algorithm/` link recovery |
| `documents/Algorithm/` (deleted) | `REMOVED` | — | NO | Git history only; do not cite |

## Removed Context Policy

- Archive trees are deleted, not retained.
- Deleted solver algorithms and old plans are git history only.
- Tests that exist only to exercise removed archive/quarantine policy are deleted.
- New work should add or update current `CANON`/`ACTIVE` docs, not recreate an
  archive bucket.
