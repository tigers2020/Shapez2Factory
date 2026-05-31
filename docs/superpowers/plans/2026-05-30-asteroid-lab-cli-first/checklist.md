# Asteroid Lab CLI-first Split — Master Execution Checklist

**Status:** ACTIVE (derived from [`README.md`](README.md), 2026-05-30 2nd-review plan set)
**Scope:** Single source of execution truth across PR-CLI-0 … PR-CLI-6. Each PR's own file remains the
detailed contract; this file is the cross-PR progress tracker.
**Closing rule:** No commit / push / PR / merge / `CLOSED` without explicit user request ([`AGENTS.md`](../../../../AGENTS.md)).

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[-]` skipped (document reason).

---

## 0. Frozen decisions (must hold in every PR)

- [x] FD-1 package root = `src/shapez2_factory/`
- [x] FD-2 hybrid now → subprocess/artifact default later (`subprocess_only` = target)
- [x] FD-3 DB = run registry / artifact index / option cache only (not solver state SoT)

## 1. Blocking amendments (cross-cutting; verified per touching PR)

- [x] BA-1 `src/shapez2_factory/**` imports no `django`, `django_apps`, `config`, ORM, settings, web/replay UI (one-direction shims only)
- [x] BA-2 no monolithic move PR; 2a–2e (+2f) split + CLI as own PR
- [x] BA-3 no active L3 relocation during boundary-m-repack PR-B/C; PR-CLI-2e gated — GATE opened after PR #133 (`895a5ecb`) merged; 2e executed post-merge (#134, #135)
- [x] BA-4 `output/replay_core.jsonl` is core/deterministic; Django enrichment only; no web-ready core payload
- [x] BA-5 atomic write `.tmp/<run_key>` → hash → manifest last → rename; DB ingest after `ARTIFACT_WRITTEN`
- [x] BA-6 Phase D manifest parsing via `artifact_manifest_reader.py` (Option 1, no core import)
- [x] BA-7 subprocess: `shell=False`, list args, `sys.executable`, fixed cwd, timeout, log capture (+ BA-9 parent tee), traversal guard, typed exit codes
- [x] BA-8 `game_data_snapshot.json` fail-closed; ORM → export → JSON adapter single path
- [x] BA-9 console observability — stderr start/end one-liners; verbose opt-in; subprocess parent tee + `logs/subprocess.log` ([`obs-console-log.md`](obs-console-log.md))

## 2. Structural amendments (2nd review)

- [x] SA-1 PR-CLI-2d drops `stack_runner` move (L2 + shared + contracts only)
- [x] SA-2 `stack_runner` moves in PR-CLI-2e together with L3–L6 (no bridge ever) — done via Approach A (core returns records; Django wrapper writes); core has zero `django_apps` imports
- [x] SA-3 PR-CLI-3 split into 3a (artifact shell) + 3b (full run) — 3a landed; 3b done on branch
- [x] SA-4 PR-CLI-2c gains blocking `display_map` pure/viewer split
- [x] SA-5 PR-CLI-6 uses Option A (in-process removed from request path entirely)
- [x] SA-6 PR-CLI-2f inserted before 3b — decode/cleanup/reconstruction pipeline move to core (#135); 3b depends on 2f

## 3. Cross-cutting guards (land in listed PR, stay green after)

- [x] Guard A — schema version reject (`test_manifest_rejects_unknown_schema_version`) — PR-3a (`parse_manifest_checked` fail-closed)
- [x] Guard B — replay monotonic (`test_replay_core_rejects_non_monotonic_frame_index`) — PR-3b
- [x] Guard C — artifact root + run_key safety (`test_run_key_safety`, sibling-prefix variant) — PR-3a (reused PR-4); `resolve_artifact_dir` via `Path.relative_to`, `fullmatch` anchor
- [x] Guard D — JSONL streaming-only (`test_ssr_does_not_inline_full_replay`) — PR-3b policy, enforced PR-5
- [x] Guard E — `replay_core` no django replay import (`test_replay_core_does_not_import_django_replay`) — PR-3b
- [x] run_key collision writer-level (`test_artifact_writer_rejects_existing_dir`) — PR-1 (+ `--replace-existing` PR-3a)
- [x] shim identity (`test_contract_shims_preserve_identity`) — PR-2d
- [x] replay loader iterator (`test_artifact_replay_loader_returns_iterator`) — PR-5

---

## PR-CLI-0 — Spec + ADR + AST gate skeleton
Depends: — · File: [`pr-cli-0-spec-and-gates.md`](pr-cli-0-spec-and-gates.md)

- [x] Step 1 — write spec (all 10 normative sections); cite asteroid-lab invariants
- [x] Step 2 — write ADR-006 (verify next free ADR number first → 006 free)
- [x] Step 3 — update `structure.md` + `current_plan.md` ACTIVE row + `document_inventory.md`
- [x] Step 4 — add `test_shapez2_factory_core_purity.py` (empty-dir tolerant, green+active)
- [x] Verify: `pytest tests/unit/architecture/test_shapez2_factory_core_purity.py -v` + `ruff check`
- [x] Done: spec + ADR merge-ready; structure/inventory/current_plan updated; purity gate green

## PR-CLI-1 — `shapez2_factory` scaffold + manifest writer skeleton
Depends: CLI-0 · File: [`pr-cli-1-core-scaffold.md`](pr-cli-1-core-scaffold.md)

- [x] Step 1 (TDD) — `test_manifest_dto.py` round-trip; implement `ArtifactManifest`
- [x] Step 2 (TDD) — `test_artifact_atomic_write.py` (no final dir until finalize; manifest last; hashes match; staging removed)
- [x] Step 3 (TDD) — collision tests: `test_artifact_writer_rejects_existing_dir`, `_existing_staging`, `test_content_hashes_excludes_manifest`
- [x] Step 4 — define ports + stub `RunStackUseCase` (empty result)
- [x] Step 5 — purity gate scans populated package, green
- [x] Step 6 — `ruff` + `mypy src`
- [x] Done: pure package imports clean; BA-1 gate green on real modules; atomic write + manifest tests pass

## PR-CLI-2a — Pure DTO move (coord / grid / snapshot contracts)
Depends: CLI-1 · File: [`pr-cli-2a-dto-move.md`](pr-cli-2a-dto-move.md)

- [x] Step 1 — per module: confirm zero django import; copy to `domain/asteroid_lab/`; adjust intra-core imports
- [x] Step 2 — replace originals with shim re-exports (explicit names, not `*`)
- [x] Step 3 — run import-matrix + reconstruction tests, no breakage
- [x] Step 4 — `test_dto_importable_without_django.py` (subprocess, `DJANGO_SETTINGS_MODULE` unset)
- [x] Step 5 — purity gate + ruff + mypy (`mypy src` clean; repo-wide mypy red at pre-existing baseline only)
- [x] Done: DTOs in core; shims green; `tests/unit/asteroid_lab` unchanged; BA-1 green

## PR-CLI-2b — `GameDataRulesPort` + JSON snapshot adapter (L2 decouple)
Depends: CLI-2a · File: [`pr-cli-2b-game-data-port.md`](pr-cli-2b-game-data-port.md)

- [x] Step 1 (TDD) — `test_layer_02_capacity_snapshot.py` (fixture JSON via adapter + `resolve_per_connector_capacity`)
- [x] Step 2 — implemented adapter + domain `ExteriorCapacityRow`; `capacity.py` takes injected port; `plan.py` default wiring
- [x] Step 3 — `export_game_data_snapshot` command; `orm_game_data_rules.py` single path (export → JSON adapter)
- [x] Step 4 — parity tests ORM export → adapter == EVTC service (shape 5760 / fluid 345600 confirmed)
- [x] Step 5 — fail-closed tests (missing / unsupported / mismatch / malformed + hash-match accept)
- [x] Step 6 — ruff clean; `mypy src` clean; full mypy +0 new; purity gate green; FIX-1 missing-row rewritten
- [x] Done: `capacity.py` ORM-decoupled (port-injected); no-db + ORM-parity green; export works; fail-closed covered

## PR-CLI-2c — cleanup + reconstruction move + `complete_map` serializer
Depends: CLI-2a · File: [`pr-cli-2c-reconstruction-move.md`](pr-cli-2c-reconstruction-move.md)

**Slice 1 (done):** prereq DTO/snapshots/leaf move + `display_map` pure split + parity. **Slice 2 (done):** `complete_map` + `acceptance_topology` + `rim_topology` move + serializer.

- [x] Step 1 — audited all 20 `reconstruction/*.py` + 3 `cleanup/*.py`; allowlist below (no wildcard)
- [x] Step 2 (BLOCKING) — split `display_map.py` → pure `complete_map_merge.py` (core) + viewer `display_map.py` (Django); `snapshot_map_replay` transforms relocated to core; `test_complete_map_merge.py` parity (no-db)
- [x] Step 3 (Slice 1 subset) — moved pure leaves to core + shimmed: `DecodedCellDTO`, `asteroid_map_coords`, `transport_components`, `reconstruction/{grid,result,evidence}`, `cleanup/result`.
- [x] Step 3b (Slice 2) — moved `reconstruction/{complete_map,acceptance_topology,rim_topology}` to core + shimmed; `complete_map` now depends on pure core `complete_map_merge` (no `display_map`/`replay`). Test helper `reconstruction_complete_map_fixtures.py` repointed to core for private helpers.
- [x] Step 4 (TDD, Slice 2) — `test_complete_map_serializer.py` round-trip (4 tests) + new `adapters/asteroid_lab/complete_map_serializer.py`
- [x] Step 5 — full `asteroid_lab` suite parity green (719 passed, 1 xfailed)
- [x] Step 6 — purity gate + import-matrix gates + ruff + `mypy src` green (42 files). Also fixed pre-existing PR-CLI-2b import-matrix violations (game_data↔asteroid_lab) + `structure.md` `var/runs/` governance.
- [x] Done: pure recon in core; display/persist stay Django; serializer round-trips; recon gates green

## PR-CLI-2d — L2 + shared + contracts move (NO stack_runner)
Depends: CLI-2b, CLI-2c · File: [`pr-cli-2d-l2-shared-contracts-move.md`](pr-cli-2d-l2-shared-contracts-move.md)

- [x] Step 1 — move contracts (+ `genetic_sample.enums` prereq); rewrite intra-core imports; shim (re-export, not redefine). Deferred to 2e: `rim_placement`, `layer04_disabled` (import `services.dto`)
- [x] Step 2 — move L1 `output.py` + full L2 + shared (ceildiv, route_probe, equivalence_key); wire L2 port via `rules`-required core + ORM default in django plan/run shim. L1 `run.py`/`__init__` stay Django (game_data ORM dep)
- [x] Step 3 — split observability: 6 pure metric builders + behavior catalog → core; settings/timezone/file-I/O session + `build_layer04` (rim_placement dep) stay Django
- [x] Step 4 (TDD) — `tests/unit/architecture/test_contract_shim_identity.py` (15 parametrized symbols `is`-identical; required 6 + Direction covered)
- [x] Step 5 — `stack_runner` (still Django) unchanged; full asteroid_lab suite 719 passed (stack_runner skeleton green via django shim default rules)
- [x] Step 6 — purity gate green with ZERO `django_apps` exceptions (no bridge); `mypy src` clean (83 files). Added `src/shapez2_factory/py.typed` (PEP 561) → django↔core imports type-checked instead of `import-untyped` (review fix)
- [x] Step 7 — layer + budget + recon gates 169/719 passed; ruff clean; mypy src clean
- [x] Done: contracts + L1 output + L2 + shared + pure observability in core, pure; shim identity green; stack_runner still Django; no bridge. Note: full-gate `mypy django_apps config src` has ~1025 pre-existing unrelated errors (baseline)

## PR-CLI-2e — L3..L6 + stack_runner move (GATED)
Depends: CLI-2d AND L3 boundary-m-repack PR-B/C merged+green · File: [`pr-cli-2e-l3-gated-move.md`](pr-cli-2e-l3-gated-move.md)

GATE (BA-3) — all verified OPEN (2026-05-30):
- [x] boundary-m-repack PR-B merged to master — **PR #133** (`895a5ecba7f2022adfa97fd584bc84eedaf9b8f6`)
- [x] PR-C merged or explicitly out of scope — no separate PR-C; m3e_01 fully in #133 (out of scope)
- [x] Lab gate green on master with new L3 — layers+replay 173 + core 85 green @ `895a5ecb`
- [x] no open PR editing `layer_03_*` — `gh pr list --state open` = []

GATE evidence: opened after PR #133 (m3e_01 inward-chain greedy) merged to master `2026-05-30T22:21:45Z`.
Active L3 is `layer_03_rim_greedy_placement` (12 files); legacy `layer_03_rim_mining_bundles` + `layer_04`
are stubs. Design/plan: [`../2026-05-30-layer-03-boundary-m-repack-greedy/`](../2026-05-30-layer-03-boundary-m-repack-greedy/README.md).
Merge integration SHA on this branch: `b566d4f8` (includes #134 L3–L6 + #135 pipeline).

Tasks:
- [x] Step 0 — GATE verified OPEN; SHA `895a5ecb` recorded (#133)
- [x] Step 1 — moved L3 greedy(12)+legacy+L4/L5/L6; shims at all originals
- [x] Step 2 — `stack_runner` in core; Django wrapper owns L1/session/settings/write
- [x] Step 3 — no `_l3_l6_bridge`; core zero `django_apps`/`from django` imports; purity gate green
- [x] Step 4 — full layer + stack_runner budget + L3 repack tests green
- [x] Step 5 — ruff + mypy + recon gates
- [x] Done: L3–L6 + stack_runner in core; no bridge; purity clean; behavior identical to master

## PR-CLI-2f — Decode / Cleanup / Reconstruction pipeline core move
Depends: CLI-2e · File: [`pr-cli-2f-decode-cleanup-reconstruction-move.md`](pr-cli-2f-decode-cleanup-reconstruction-move.md) · PR [#135](https://github.com/tigers2020/Shapez2Factory/pull/135)

Inserted 2026-05-30 (SA-6) to unblock 3b's "no Django" full run. Audit found decode (`decode_adapter`),
cleanup (`cleanup/pipeline`), reconstruction (`reconstruction/pipeline`) algorithm bodies still in
`django_apps`; core had DTO + `complete_map` merge only.

- [x] Step 1 (audit) — DONE 2026-05-30: **15-module** move set confirmed (decode/input 5: `decode_adapter`, `normalization`, `decoded_blueprint_snapshot`, `cell_classifier`, `copy_json_coords`; cleanup 1: `cleanup/pipeline`; reconstruction 9: `pipeline`, `confidence`, `fill`, `flood_fill`, `island`, `perimeter_closing`, `shell`, `trace`, `topology_contract`). Zero direct django/ORM/settings in bodies; boundary side-effect = 3 emit sites; DTOs + `display_map` helpers already core. No stop condition.
- [x] Step 2 (TDD, tests-first → red) — 5 target tests added; RED-for-right-reason confirmed pre-move
- [x] Step 3 (BLOCKING) — core `BoundaryTraceSink` Protocol (default no-op); `summarize_cell_kind_transitions` in core; 3 emit sites rewired; `DJANGO_BOUNDARY_SINK` adapter
- [x] Step 4 (move) — 15 modules in core; intra-core imports; lazy `display_map`→`complete_map_merge`; explicit shims
- [x] Step 5 (TDD, parity) — 19 target tests green; Django-free subprocess full-pipeline green
- [x] Step 6 — `pytest tests/unit/asteroid_lab tests/unit/architecture`: 791 passed, 1 xfailed; purity + shim-identity gates green
- [x] Step 7 — ruff + `mypy src` + black clean
- [x] Done: decode+cleanup+reconstruction in pure core; observability via injected sink; shims preserve surface; parity + Django-free subprocess green; purity zero `django_apps` exceptions

## PR-CLI-3a — CLI artifact shell + `validate-artifact`
Depends: CLI-1 (+CLI-2a) · File: [`pr-cli-3a-artifact-shell.md`](pr-cli-3a-artifact-shell.md)

- [x] Step 1 (TDD) — `test_run_key_safety.py` (traversal/separator/dot/trailing-newline/empty rejected; sibling-prefix variant; 6 tests). `fullmatch` anchor closes `$`+`\n` bypass
- [x] Step 2 (TDD) — `test_manifest_schema_version.py` (guard A): `parse_manifest_checked` rejects unknown/missing/non-int schema_version + non-dict top-level; malformed JSON → `JSONDecodeError` (6 tests). Lenient `from_json` left intact
- [x] Step 3 (TDD) — `test_validate_artifact.py` (12 tests): hash mismatch / missing payload / lifecycle != ARTIFACT_WRITTEN / unknown schema / missing manifest / malformed JSON / bad lifecycle enum / missing required field all → VALIDATION_FAILED (branch pinned via `capsys` stderr substring)
- [x] Step 4 — CLI shell `interfaces/cli/asteroid_solve.py` + `__main__.py` + `scripts/asteroid_solve.ps1`; `ExitCode` IntEnum (OK=0/VALIDATION_FAILED=10/STACK_UNAVAILABLE=20, 2 reserved for argparse); `run` enforces Guard C then returns typed STACK_UNAVAILABLE; `--allowed-root` default = configured sandbox `var/runs` (containment active by default)
- [~] Step 5 — `--replace-existing` flag exposed on `run`; delete-then-rename collision policy already lives in `AtomicArtifactWriter` (PR-1). CLI flag is parsed/forwarded but inert in the 3a stub — real write-path wiring lands in PR-3b
- [x] Step 6 — ruff clean; `mypy src` clean (87 files); black clean; purity + import-matrix + shim-identity gates green (51 passed)
- [~] Done: CLI shell + validate-artifact fully fail-closed + core-pure; run_key/root/schema guards green; writer-level collision green (PR-1). Deferred to 3b: `--replace-existing` real wiring through CLI `run`

### PR-CLI-3a amend — BA-9 console (pure CLI shell)

Contract: [`obs-console-log.md`](obs-console-log.md)

- [x] Step A1 (TDD) — `test_cli_console.py` (18 tests): formatter shape/field-order/null-omission/bool-lowercase + env gate ON default / OFF for `0`/`false`/`no` (case-insensitive) + no-op when disabled. Verbose gate deferred to 3b (out of amend scope)
- [x] Step A2 — `cli_console.py` (stdlib-only `emit_cli_line` + `console_logging_enabled`, BA-1) + wired `validate-artifact` / `run` stub start/end stderr lines (end carries `exit`/`elapsed_ms`/`ok`, `run` carries `run_key`; end reflects exit code even on `ArtifactPathError` path)
- [x] Step A3 — extended `test_validate_artifact.py` (3 `capsys` tests: success start/end `exit=0 ok=true`; failure `exit=10 ok=false`; disabled → no `asteroid_cli` line)

## PR-CLI-3b — Full pure CLI `run` (decode → stack → artifacts)
Depends: CLI-2e AND CLI-2f AND CLI-3a · File: [`pr-cli-3b-full-run-stack.md`](pr-cli-3b-full-run-stack.md)

- [x] Step 1 (TDD) — `test_cli_run_artifact.py` (final dir only after success; manifest hashes; outputs present; JSONL parses per line)
- [x] Step 2 — implement `run_stack` use case (decode/cleanup/recon/in-core stack_runner + JSON snapshot adapter)
- [x] Step 3 — implement `replay_core` emitter (core event construction only; Django enrichment left behind)
- [x] Step 4 (TDD) — `test_replay_core_monotonic.py` (B) + `test_cli_exit_codes.py` (BA-7) + `test_replay_core_no_django_replay.py` (E)
- [x] Step 5 (BA-9) — `--verbose` on `run`; `layer_done` stderr lines from stack (see [`obs-console-log.md`](obs-console-log.md)); no change to layer-stack JSONL files
- [x] Step 6 — ruff + mypy + purity gate
- [x] Done: full pure CLI produces valid atomic artifact incl. streaming JSONL; exit codes mapped; no Django reachable; BA-9 verbose path green

## PR-CLI-4 — Django subprocess mode + artifact ingest
Depends: CLI-3b · File: [`pr-cli-4-django-subprocess-ingest.md`](pr-cli-4-django-subprocess-ingest.md)

- [x] Step 1 — add `ASTEROID_LAB_SOLVER_MODE` setting + mode dispatch in `solver_runtime_entry`
- [x] Step 2 (TDD) — `artifact_manifest_reader` validation + no-core-import AST test (BA-6)
- [x] Step 3 (TDD) — `solver_subprocess_runner` (mock: `shell=False`, list args, timeout, traversal rejected) (BA-7)
- [x] Step 4 (TDD) — `artifact_ingest` (hash mismatch fail-closed; partial rejected; index-only writes) (BA-5)
- [x] Step 5 — wire HTTP/management opt-in flags (`config.solver_mode=subprocess` for HTTP JSON; `manage.py run_solver --subprocess --artifact-root --cli-verbose`)
- [x] Step 5b (BA-9) — `cli_invoke_trace` + `ASTEROID_LAB_CLI_*` settings; verbose in layer02; `subprocess_stream_tee` in runner; tests ([`obs-console-log.md`](obs-console-log.md))
- [x] Step 6 — integration test subprocess mode end-to-end (small fixture)
- [~] Step 7 — ruff + mypy + full gate (full pytest/ruff/black green; source-focused mypy green; repo-wide mypy remains baseline-red)
- [~] Done: both modes work; subprocess produces + ingests safely; index-only DB writes; integration green; BA-9 HTTP + subprocess tee green. Repo-wide mypy baseline remains open.

## PR-CLI-5 — DB demotion + artifact-first replay
Depends: CLI-4 · File: [`pr-cli-5-db-demotion-replay.md`](pr-cli-5-db-demotion-replay.md)

- [x] Step 1 — migration for `artifact_root` + `lifecycle_status` (nullable; no backfill)
- [x] Step 2 (TDD) — `test_artifact_first_replay.py` (indexed artifact → JSONL wins over DB)
- [x] Step 3 — artifact-first resolution in timeline payload + lazy handle; DB fallback
- [x] Step 4 — summary service reads manifest mirror
- [x] Step 5 (TDD) — `test_artifact_replay_loader_iterator.py` (iterator/generator, not list) + SSR no-inline guard D
- [x] Step 6 (TDD) — fields documented as cache; core has no `create_solver_run` import (AST)
- [~] Step 7 — ruff + mypy + full gate + recon narrow (full pytest/ruff/black green; source-focused mypy green; repo-wide mypy remains baseline-red)
- [~] Done: artifact-first replay with DB fallback; new columns; fields documented as cache; full pytest gate green. Repo-wide mypy baseline remains open.

## PR-CLI-6 — `subprocess_only` default + viewer import gate (Option A)
Depends: CLI-5 (ideally CLI-2e) · File: [`pr-cli-6-subprocess-only-default.md`](pr-cli-6-subprocess-only-default.md)

- [x] Step 1 — set `subprocess_only`; remove in_process/subprocess branch selection from request path
- [x] Step 2 — remove all core imports from `solver_runtime_entry`; subprocess runner references CLI by module string only
- [x] Step 3 (TDD) — viewer import gate `test_asteroid_lab_viewer_no_core_import.py`, make green
- [x] Step 4 — update docs (`structure.md`, runtime wiring, `current_plan.md`)
- [~] Step 5 — full gate: ruff + black + mypy + pytest (full pytest/ruff/black green; source-focused mypy green; repo-wide mypy remains baseline-red)
- [~] Done: `subprocess_only` only path; no core import in request flow; viewer gate green; docs updated; repo-wide mypy baseline remains open

---

## Global verification (run as PRs land)

**Last verified:** 2026-05-31 @ `5610d55e` (merge `origin/master` + CLI-first WIP) — CLI separation 28 + layers 128 + BA-9 logs 25 passed; `test_full` 1719 passed, 1 xfailed; ruff + black green.

```powershell
python -m pytest tests/unit/architecture/test_shapez2_factory_core_purity.py -v
python -m pytest tests/unit/shapez2_factory/ -v
python -m ruff check src/shapez2_factory
python -m mypy django_apps config src
```

## Full gate (PR / merge)

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```
