# Ubiquitous Language

This document defines the shared language used in this domain.  
It is generated from available source material and should be reviewed by domain owners.

## Scope

| Field | Value |
|---|---|
| Sources Scanned | Prior scan + full `documents/knowledge/wiki/concepts/*` (21 pages), `documents/knowledge/raw/algorithm/README.md`, `weighted_transport_route_domain.py`, `layer_04_transport_routing/route_domain.py`, `route_probe.py` |
| Domain Focus | shapez2 Factory Planner — Asteroid Lab solver, replay, game data, shape algebra |
| Glossary placement | `docs/ubiquitous-language.md` = evidence-backed term map for agents; `documents/knowledge/wiki/` = per-concept synthesis (cross-linked from wiki `Index.md`) |
| Mode | updated |
| Last Updated | 2026-06-12 |

## Canonical Terms

| Term | Category | Definition | Evidence | Boundary Exposure | Confidence |
|---|---|---|---|---|---|
| Asteroid Lab | Canonical Term | Django app + CLI stack for asteroid mining layout optimization, artifact-indexed solver runs, and replay viewer. Solver core is Django-free in `src/shapez2_factory/`. | `structure.md` § `django_apps/asteroid_lab/`; `documents/knowledge/wiki/concepts/asteroid-lab-algorithm.md` | Docs, UI (`/asteroid-miner-layout/`) | High |
| Copy JSON | Canonical Term | Decoded blueprint payload from a `SHAPEZ2-4-…` game paste; `BP.Entries` carry island-local `X`/`Y`/`R`. | `documents/knowledge/wiki/concepts/island-mechanics.md`; `django_apps/asteroid_lab/models.py` `AsteroidMapInput.copy_code` | Wire, Schema, UI | High |
| Island-local coordinates | Canonical Term | `X`/`Y`/`R` in copy JSON refer to the island blueprint grid, not asteroid world absolute positions. `X==0` is valid. | `documents/knowledge/wiki/concepts/island-mechanics.md`; `.cursor/rules/asteroid-lab-invariants.mdc` | Docs, Wire | High |
| World / reconstruction map | Canonical Term | Coordinate frame used for transport BFS and asteroid evidence; has no `x=0` column. Distinct from copy-local and island map grid. | `documents/knowledge/wiki/concepts/island-mechanics.md` | Docs, Internal Only | High |
| Coord | Canonical Term | Island map grid coordinate type at the lab optimization boundary; aligns with copy-local at ingest. | `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py`; wiki `island-mechanics` | Internal Only | High |
| Layer (L2–L5) | Canonical Term | Stacked solver phases: L2 mixed resource plan, L3 rim greedy placement, L4 interior routing, L5 transport routing. | `documents/knowledge/wiki/concepts/asteroid-lab-algorithm.md` | Docs, Wire (`solver_runtime_wires`) | High |
| ResourceKind | Canonical Term | Domain enum: `shape` or `fluid` — what a mining bundle produces. | `src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py` | Wire, Schema | High |
| TransportKind | Canonical Term | Domain enum: `space_belt` (shapes) or `space_pipe` (fluids). Maps 1:1 from `ResourceKind`. | `transport_kind.py`; `documents/knowledge/wiki/concepts/transport-system.md` | Wire, Schema, UI | High |
| Candidate | Canonical Term | Generated/probed placement option in the normal pool; probe-only semantics — no commit until finalized. | `.cursor/rules/asteroid-lab-invariants.mdc`; `BundleCandidate` in `candidates.py` | Internal Only | High |
| Commit | Canonical Term | Finalized placement that re-probes latest L3 route domain (`WeightedTransportRouteDomain`) before persist via `RouteDomainSnapshotBuilder`. | `.cursor/rules/asteroid-lab-invariants.mdc`; `commit_reprobe.py` | Internal Only | High |
| RouteDomainSnapshotBuilder | Canonical Term | Sole authority for constructing L3 `WeightedTransportRouteDomain` snapshots at candidate probe and commit re-probe. | `route_domain_snapshot_builder.py`; `candidate_gen.py`, `commit_reprobe.py`, `route_probe.py` | Internal Only | High |
| ReconstructedMap | Canonical Term | Persisted full_map lab copy after reconstruction+cleanup merge; ORM `ReconstructedAsteroidMap`. Not solver input. | wiki `reconstructed-map`; `reconstructed_map_persist_builder.py` | DB, UI | High |
| Artifact | Canonical Term | CLI output directory under `var/runs/<run_key>/` with atomic `manifest.json`, `output/replay_core.jsonl`, and indexed sidecars. Not solver algorithm input. | `structure.md` § `var/runs/`; `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` | Wire, Schema, Config | High |
| run_key | Canonical Term | Stable identifier for one solver execution and its artifact directory. | `django_apps/asteroid_lab/models.py` `SolverRun.run_key`; artifact spec | Wire, Schema, API, DB | High |
| manifest.json | Canonical Term | Atomic artifact index with content hashes, lifecycle status, and relative paths to output files. Immutable at `artifact_written` after finalize. | `run_status.py` module doc; artifact design spec | Wire, Schema | High |
| replay_core.jsonl | Canonical Term | Deterministic, one-JSON-object-per-line replay event stream emitted by CLI; Django enriches for UI only. | artifact design spec §3; `.cursor/rules/asteroid-lab-invariants.mdc` | Wire, Schema | High |
| Semantic DTO | Canonical Term | Frozen dataclass representing replay/solver meaning; authority for business semantics. | `documents/knowledge/wiki/concepts/asteroid-lab-wire-typing.md`; `timeline_dtos.py` | Internal Only | High |
| Wire | Canonical Term | Named `TypedDict` plus converters for serialized payloads; only legal path between semantic DTOs and JSON. | `asteroid-lab-wire-typing.md`; `overlay_wire_contract.py`, `replay_map_cell_wire.py` | Wire, Schema | High |
| EffectiveCellView | Canonical Term | UI merged cell read model combining occupancy and transport overlay for replay rendering. | `effective_cell_view.py`; wiki wire-typing authority map | Wire, UI | High |
| frame_index | Canonical Term | Monotonic replay timeline index; one product replay — no second optimization controller. | `.cursor/rules/asteroid-lab-invariants.mdc`; replay_core tests | Wire, Schema | High |
| Game Data | Canonical Term | Canonical Unity dump ORM in `django_apps/game_data/` imported via `GameDataImporter`; shapes, buildings, transport layouts, etc. | `structure.md` § `game_data`; wiki `game-data-manifest` | Schema, DB, Docs | High |
| Shape Hash | Canonical Term | Primary business key for a shape recipe in `shapes.json`; used for planner/research cost lookup. | `documents/knowledge/wiki/concepts/shape-data-model.md` | Schema, Docs | High |
| Shape recipe | Canonical Term | One of 1,170 entries in `shapes.json` with 4 quadrant slots, 1–4 layers, and unique `Hash`. | `shape-data-model.md` | Schema | High |
| Building group | Canonical Term | Taxonomy of 67 factory building families from game_data analysis. | wiki `building-definitions`, `building-groups` | Schema, Docs | Medium |
| Building variant | Canonical Term | One of 131 geometry/connector snapshots derived from a building group. | wiki `building-variants` | Schema, Docs | Medium |
| Genetic Sample | Canonical Term | Miner seed patterns and gene templates used to bootstrap L3 rim bundle candidates. | `django_apps/asteroid_lab/genetic_sample/`; `Layer03SkipReason.MISSING_GENETIC_SAMPLE_SEEDS` | Internal Only | Medium |
| Solver Runtime Wires | Canonical Term | Versioned JSON projection (`solver_runtime_wires_v1`) of layer outcomes for replay/Django ingest; forbidden as placement/routing input. | `runtime_wires/envelope.py`; wiki `asteroid-lab-algorithm` | Wire, Schema | High |
| Validation (solver) | Canonical Term | Read-only assertions on layout/routing; must not repair route, placement, or topology. | `.cursor/rules/asteroid-lab-invariants.mdc` | Docs | High |
| Fitness | Canonical Term | Predictive scoring for candidates; distinct from observed commit survivability. | `.cursor/rules/asteroid-lab-invariants.mdc` | Internal Only | High |
| WeightedTransportRouteDomain | Canonical Term | L3 bounded weighted install/search surface for exterior route probe; `walkable_cells` must not be promoted to stubs. **Not** the L4 transport network. | `weighted_transport_route_domain.py`; `route_probe.py`; `layer_04_transport_routing/route_domain.py` docstring | Internal Only | High |
| L4RouteSearchDomain | Canonical Term | L4 interior weighted route search domain over terrain kinds (`void`, `asteroid_field`, `e`, `m`); separate from L3 `WeightedTransportRouteDomain`. | `layer_04_transport_routing/route_domain.py` | Internal Only | High |
| Prefab | Canonical Term | Visual/mesh/transport prefab registry entry (764 records); `stable_id` PK; not a domain building name (`source_type_name` is always `UnityEngine.Object`). | wiki `prefabs.md`; `documents/game_data/prefabs.json` | Schema | High |
| Fluid (game data) | Canonical Term | One of 9 fluid definitions in `fluids.json`; RGB primaries at pump source; secondaries via Mixer. | wiki `fluid-data-model.md` | Schema | High |
| Material code | Canonical Term | Single-letter quadrant material in shape hash encoding: C/R/S/W/c/P/- (circle, rectangle, spike, diamond, crystal, pin, empty). | wiki `materials-data-model.md` | Schema, Docs | High |
| Item (game data) | Canonical Term | Gameplay subset of shape recipes (70 entries in `items.json`); all `Hash` values ⊆ full shapes catalog. | wiki `item-data-model.md` | Schema | High |
| Research unlock | Canonical Term | Island progression tree entry; 253 `ShapeHash` references into shapes catalog. | wiki `research-unlocks.md` | Schema | High |
| Transport capacity | Canonical Term | Solver-facing throughput caps: miner 30/min (480 max), pump 300 L/min (4.8 kL max), belt 5,760 shapes/min, pipeline 345.6 kL/min bottlenecks. | wiki `transport-capacity.md`, `transport-system.md` | Docs, Internal Only | High |
| file_hashes | Canonical Term | Manifest map of SHA256 per `documents/game_data/*.json`; import integrity gate. | wiki `game-data-manifest.md` | Schema, Config | High |
| stable_id | Canonical Term | Import-correlation primary key within a game_data JSON file (64-char hex for prefabs/building groups). | wiki `building-groups.md`, `prefabs.md` | Schema | Medium |

## Roles

| Role | Definition | Evidence | Boundary Exposure | Notes |
|---|---|---|---|---|
| AsteroidProject | One lab page / work unit owning map inputs and solver runs. | `django_apps/asteroid_lab/models.py` | DB, UI, API | Persistence role |
| AsteroidMapInput | Decoded blueprint and copy-code metadata for a project. | `models.py` `AsteroidMapInput` | DB, Wire | Carries `copy_code`, `decoded_json`, fingerprints |
| SolverRun (Asteroid Lab) | One GA/hybrid solver execution for an `AsteroidProject`; indexes artifacts and replay cache. | `models.py` `SolverRun` (asteroid_lab) | DB, UI, API | Distinct from `shapez_solver.SolverRun` |
| GameDataImporter | Deterministic importer for canonical game dump sections. | `structure.md` § `game_data/importers/` | Internal Only | Staff browse + ORM |
| CLI (`asteroid_solve`) | Django-free entry: `python -m shapez2_factory.interfaces.cli.asteroid_solve`; subprocess-only from Django. | `structure.md` § asteroid_lab | CLI, Wire | Thin execution adapter |

## Events

| Event | Definition | Trigger / Source | Evidence | Boundary Exposure |
|---|---|---|---|---|
| ARTIFACT_WRITTEN | Artifact lifecycle milestone; manifest becomes immutable. | CLI atomic finalize | `RunLifecycleStatus.ARTIFACT_WRITTEN` in `run_status.py` | Wire, Schema |
| ReconstructionTraceEvent | Trace event during map reconstruction from committed layout. | Reconstruction pipeline | `reconstruction/trace.py` | Internal Only |
| Replay frame | One timeline step in product replay; keyed by `frame_index`. | `replay_core.jsonl` emission | artifact spec; invariants | Wire |

## States

| State | Applies To | Definition | Evidence | Boundary Exposure |
|---|---|---|---|---|
| `queued` / `running` / `artifact_writing` | Run lifecycle (artifact) | Pre-finalize orchestration states before manifest freeze. | `RunLifecycleStatus` in `run_status.py` | Wire, DB |
| `artifact_written` | Run lifecycle (artifact) | Manifest finalized; Django must not rewrite `manifest.json`. | `run_status.py` docstring | Wire |
| `indexed` / `succeeded` / `failed` | Run lifecycle (DB) | Post-ingest `SolverRun` / index states only. | `RunLifecycleStatus` | DB |
| `pending` / `running` / `completed` / `partial` / `failed` / `cancelled` | Asteroid Lab `SolverRun.RunStatus` | ORM execution status for lab UI and ops. | `models.py` `SolverRun.RunStatus` | DB, UI |
| `succeeded` / `failed` / `skipped_budget` / … | RouteProbeStatus | Outcome of exterior route probe for a candidate. | `candidates.py` `RouteProbeStatus` | Internal Only |
| `completed` / `partial_budget` / `skipped` / `failed` | LayerOutcome | Per-layer runtime wire outcome. | `runtime_wires/envelope.py` `LayerOutcome` | Wire |

## Commands / Actions

| Command | Actor | Effect | Evidence | Boundary Exposure |
|---|---|---|---|---|
| Run Solver | Django / user | Export game-data snapshot, subprocess CLI, ingest artifact, serve replay. | `structure.md` § asteroid_lab `subprocess_only` | UI, CLI |
| Probe (route) | L3 candidate generator | Reachability/geometry check without commit semantics. | invariants "Candidate: generate/probe/reachable pool only" | Internal Only |
| Commit (placement) | L3 finalize | Re-probe latest route domain and persist committed equipment. | invariants "Commit: re-probe latest route_domain" | Internal Only |
| Ingest artifact | Django service | Parse manifest, index paths, update `SolverRun` cache fields. | `artifact_ingest.py`, `artifact_manifest_reader.py` | Internal Only |
| Compose replay frames | Django replay | Build renderable lab frames from artifact; never algorithm input. | `artifact_replay_viewer_compose.py` | API, UI |

## Rules / Invariants

| Rule | Applies To | Evidence | Boundary Exposure | Notes |
|---|---|---|---|---|
| Runtime wire forbidden as algorithm input | L2–L5 solver | `.cursor/rules/asteroid-lab-invariants.mdc`; wiki algorithm | Docs, Wire | Metrics/NDJSON/artifacts likewise excluded |
| `coord_system` required on layout DTOs | Map/replay DTOs | invariants DTO bullet | Wire, Schema | Layout v2 island bbox-normalized |
| Dense anchor export only at export boundary | Copy/export pipeline | invariants Export bullet | Wire | Not mid-solver |
| Seeded/stable RNG only | Solver | invariants RNG bullet | Internal Only | No unseeded `random` / `uuid4` |
| One product replay; monotonic `frame_index` | Replay timeline | invariants Timeline bullet | Wire | No second optimization controller |
| Use enums/constants for failure/event/issue codes | All layers | invariants Codes bullet | Wire, Schema | No free-form codes |
| Semantic → frozen dataclass; Wire → TypedDict | Replay typing | `asteroid-lab-wire-typing.md` | Docs, Code | Converters only legal crossing |

## Aliases

| Alias | Canonical Term | Status | Evidence | Notes |
|---|---|---|---|---|
| copy_code | Copy JSON (paste text) | Active alias | `AsteroidMapInput.copy_code`; wiki uses "Copy JSON" for decoded semantics | Paste string vs decoded payload — context-dependent |
| space_belt / SpaceBelt_* | TransportKind.SPACE_BELT | Active alias | `transport-system.md`; layout IDs vs enum | Layout ID prefix vs cell_kind |
| space_pipe / SpacePipe_* | TransportKind.SPACE_PIPE | Active alias | `transport-system.md` | Fluids only |
| GA hybrid / `ga_hybrid` | SolverRun algorithm_label default | Active alias | `models.py` `algorithm_label` default | Label not layer slug |
| layer_03_rim_mining_bundles | L3 / Layer 03 | Active alias | `Layer03Slug` in `candidates.py` | Slug is wire/config identity |
| BP.Entries | Copy JSON entries array | Active alias | `island-mechanics.md` | Game export structure |
| Building definition group | Building group | Active alias | wiki `building-definitions` vs `building-groups` | 67 groups in both analyses |
| ShapeItem | Item (game data) | Active alias | `item-data-model.md` `display_name_key` | All 70 items share label |
| MetaShapeMaterial | Material code | Active alias | `materials-data-model.md` | Enum name in dump |
| cell_kind | TransportKind wire value | Active alias | `transport-system.md` | `space_belt` / `space_pipe` on wire |

## Deprecated / Legacy Terms

| Deprecated Term | Replacement | Still Accepted? | Evidence | Notes |
|---|---|---|---|---|
| `django_apps.shapez_asteroid` | `django_apps.asteroid_lab` | No (removed) | `structure.md` boundary tests | Must not reintroduce dependency |
| Legacy mining layout solver packages | Asteroid Lab CLI + `src/shapez2_factory` layers | No | `structure.md` § asteroid_lab | Enforced by architecture tests |
| `EffectiveCellView.to_wire()` | Dedicated wire converters | No (removed) | wiki wire-typing Phase 4 | PR #283 |
| `dict[str, Any]` at replay boundaries | Named TypedDict + converters | No (campaign complete) | wiki `any_token_total=0` @597cdaf2 | Decode/import boundaries may still use raw JSON types |
| `documents/Algorithm/asteroid_lab_*.md` | `documents/knowledge/wiki/concepts/asteroid-lab-*` + `documents/knowledge/raw/algorithm/` | No (paths absent) | `raw/algorithm/README.md`; stale links in `raw/index/document_inventory.md` | Do not cite missing `documents/Algorithm/` paths |

## Ambiguous Terms

| Term | Meaning A | Meaning B | Evidence | Recommendation |
|---|---|---|---|---|
| SolverRun | Asteroid Lab ORM: one GA/hybrid lab execution with `run_key` and artifacts | shapez_solver ORM: persisted factory recipe-graph solver run | `django_apps/asteroid_lab/models.py` vs `django_apps/shapez_solver/models.py` | Qualify as **Asteroid Lab SolverRun** vs **Recipe Graph SolverRun** |
| Solver | Asteroid mining layout optimizer (L2–L5) at `/asteroid-miner-layout/` | Factory recipe/macro pattern planner in `shapez_solver` at `/solver/` | `structure.md` app split | See **Solver (cross-app)** below — never bare "solver" |
| Project | `AsteroidProject` (lab work unit) | `SolverProject` (recipe graph persistence) | respective `models.py` files | Never use bare "project" in cross-app docs |
| Lifecycle status | `RunLifecycleStatus` on artifact manifest | `SolverRun.lifecycle_status` DB mirror | `run_status.py` vs `models.py` | Manifest is artifact authority; DB field is cache mirror |
| Status | `SolverRun.RunStatus` (execution) | `RouteProbeStatus` (probe) | enums in models vs candidates | Namespace by enum type |
| Pattern | `PatternTemplate` / `PatternVariant` (asteroid_lab lab templates) | Macro pattern / recipe graph pattern (shapez_solver) | `models.py` comments | asteroid_lab "Pattern" ≠ shapez_solver macro pattern |
| Map | Island map grid (`Coord`) | Reconstructed world map | `island-mechanics.md` three frames | State coordinate frame explicitly |
| Validation | Solver read-only assertions (no repair) | Django `manage.py check` / CI gates | invariants vs `AGENTS.md` | "Solver validation" vs "repo validation" |
| Route domain | L3 `WeightedTransportRouteDomain` (exterior probe) | L4 `L4RouteSearchDomain` (interior fill) | `weighted_transport_route_domain.py` vs `route_domain.py` | Prefix with layer: L3 route domain vs L4 route domain |
| Transport route domain | L3 weighted probe surface | L4/L5 transport routing network | layer module docstrings | Never use bare "route domain" cross-layer |

## Solver (cross-app)

Bare **solver** is ambiguous. Always qualify:

| Qualifier | App | Primary URL | Domain |
|---|---|---|---|
| **Asteroid Lab solver** | `django_apps/asteroid_lab` + `src/shapez2_factory` | `/asteroid-miner-layout/` | Mining layout L2–L5, artifacts, replay |
| **Recipe graph solver** | `django_apps/shapez_solver` | `/solver/`, `/solver/pattern-lab/` | Factory recipe DAG, macro patterns, demand planning |

| Shared collision | Asteroid Lab | Recipe graph |
|---|---|---|
| `SolverRun` | `asteroid_lab.SolverRun` — `run_key`, artifacts | `shapez_solver.SolverRun` — `result_graph` |
| `Project` | `AsteroidProject` | `SolverProject` |
| `Pattern` | `PatternTemplate` / `PatternVariant` | Macro pattern / recipe graph node |

## Candidate Terms

| Term | Possible Meaning | Evidence | Missing Evidence | Suggested Classification |
|---|---|---|---|---|
| Gene / gene_key | Genetic-sample miner seed identity for bundle candidates | `BundleCandidate.gene_key`; genetic_sample package | Formal gene-topology doc in wiki | Internal Term |
| BundleCellRole | Per-cell role in L3 bundle: miner, extension, transport_stub, route_reserved | `candidates.py` `BundleCellRole` | UI/replay exposure mapping | State / Internal Term |
| layout_t | Game layout identifier string on placed cells | `BundlePlacement.layout_t` | Mapping table to game_data layouts | Boundary Term attribute on Wire |
| lab_replay_cache | Django JSON cache of composed replay for UI | `SolverRun.lab_replay_manifest_summary_json` | Schema version contract | Internal Term |
| Macro pattern | shapez_solver stored factory macro | `structure.md` shapez_solver | Out of asteroid-lab scope | External Term (shapez_solver bounded context) |
| Recipe graph | shapez_solver persisted recipe DAG | `structure.md` | — | External Term (separate app) |
| Golden fixture | Deterministic regression dataset under `tests/golden/` | `structure.md` | Which layers each golden covers | Rule / test artifact |
| subgraph / community (graphify) | Code graph clustering for architecture queries | wiki `graphify-architecture-map` | — | External Term (tooling) |

## Terminology Risks

| Risk | Terms Involved | Evidence | Impact | Recommendation |
|---|---|---|---|---|
| Meaning collision | SolverRun | Two Django models same name, different apps | Import confusion, wrong replay/ingest paths | Always qualify with app: `asteroid_lab.SolverRun` |
| Boundary mismatch | Copy JSON vs world map | `island-mechanics.md`; invariants | Silent coordinate bugs in routing | Mandate frame label in APIs and logs |
| Legacy leakage | shapez_asteroid | structure boundary tests | Broken imports if revived | Keep architecture test gate |
| Canon conflict (historical raw) | Algorithm doc paths | Old plans/manuals may still href `documents/Algorithm/` | Agents follow stale links in unmigrated raw | Use `authority-redirect.md`; do not bulk-edit raw bodies |
| Layer name collision | Route domain | L3 and L4 both use "route domain" vocabulary | Cross-layer refactor bugs | Use `WeightedTransportRouteDomain` vs `L4RouteSearchDomain` explicitly |
| Framework leakage | Service, Handler, Manager | Widespread in Django/adapters | Domain docs may mirror implementation nouns | Map to bounded-context terms above |
| Concept cluster | Artifact lifecycle + SolverRun status | `run_status.py` split authority | Ops bugs if manifest rewritten after finalize | Enforce manifest immutability in ingest code reviews |

## Open Questions

_None — items from 2026-06-12 pass resolved (builder implemented, solver cross-app section, reconstructed-map wiki, transport alias table, manifest SHA anchors)._

## Source Index

| Source | Relevance |
|---|---|
| `structure.md` | Repository map, app ownership, artifact paths |
| `AGENTS.md` | Process authority; layer boundaries |
| `.cursor/rules/asteroid-lab-invariants.mdc` | Solver/replay/DTO invariants |
| `documents/knowledge/wiki/Index.md` | Synthesized domain concepts index |
| `documents/knowledge/wiki/concepts/*.md` | Game data, transport, island coords, wire typing, layers |
| `django_apps/asteroid_lab/models.py` | Lab persistence entities and statuses |
| `src/shapez2_factory/application/asteroid_lab/layers/contracts/` | Layer enums, candidates, transport kinds |
| `src/shapez2_factory/adapters/asteroid_lab/run_status.py` | Artifact lifecycle enum |
| `src/shapez2_factory/adapters/asteroid_lab/runtime_wires/envelope.py` | Runtime wire versions and layer outcomes |
| `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` | Artifact layout, replay_core contract |
| `docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md` | Wire typing rollout authority |
| `documents/knowledge/raw/algorithm/README.md` | Current algorithm doc authority (post-archive) |
| `documents/knowledge/raw/algorithm/authority-redirect.md` | Stale `documents/Algorithm/` → wiki/code/spec redirect ledger |
| `documents/knowledge/wiki/concepts/algorithm-doc-authority.md` | Wiki hub linking raw ledger + this glossary |
| `documents/knowledge/wiki/concepts/building-definitions.md` | 67 building groups, factory I/O |
| `documents/knowledge/wiki/concepts/building-groups.md` | Group taxonomy, 131 embedded variants |
| `documents/knowledge/wiki/concepts/building-variants.md` | Variant snapshots |
| `documents/knowledge/wiki/concepts/fluid-data-model.md` | 9 fluids, RGB constraint |
| `documents/knowledge/wiki/concepts/materials-data-model.md` | C/R/S/W/c/P/- codes |
| `documents/knowledge/wiki/concepts/item-data-model.md` | 70-item gameplay subset |
| `documents/knowledge/wiki/concepts/research-unlocks.md` | Island progression ShapeHash refs |
| `documents/knowledge/wiki/concepts/prefabs.md` | 764 prefab registry |
| `documents/knowledge/wiki/concepts/game-data-manifest.md` | Dump metadata, file_hashes |
| `documents/knowledge/wiki/concepts/transport-capacity.md` | Solver throughput bottlenecks |
| `src/.../weighted_transport_route_domain.py` | L3 route probe domain |
| `src/.../layer_04_transport_routing/route_domain.py` | L4 route search domain |
| `src/.../route_domain_snapshot_builder.py` | L3 route domain builder |
| `documents/knowledge/wiki/concepts/reconstructed-map.md` | ReconstructedMap lifecycle |
