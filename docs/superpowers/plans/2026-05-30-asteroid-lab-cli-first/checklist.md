# Asteroid Lab CLI-first Split — Master Execution Checklist

**Status:** ACTIVE (derived from [`README.md`](README.md), 2026-05-30 2nd-review plan set)
**Scope:** Single source of execution truth across PR-CLI-0 … PR-CLI-6. Each PR's own file remains the
detailed contract; this file is the cross-PR progress tracker.
**Closing rule:** No commit / push / PR / merge / `CLOSED` without explicit user request ([`AGENTS.md`](../../../../AGENTS.md)).

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[-]` skipped (document reason).

---

## 0. Frozen decisions (must hold in every PR)

- [ ] FD-1 package root = `src/shapez2_factory/`
- [ ] FD-2 hybrid now → subprocess/artifact default later (`subprocess_only` = target)
- [ ] FD-3 DB = run registry / artifact index / option cache only (not solver state SoT)

## 1. Blocking amendments (cross-cutting; verified per touching PR)

- [ ] BA-1 `src/shapez2_factory/**` imports no `django`, `django_apps`, `config`, ORM, settings, web/replay UI (one-direction shims only)
- [ ] BA-2 no monolithic move PR; 2a–2e split + CLI as own PR
- [ ] BA-3 no active L3 relocation during boundary-m-repack PR-B/C; PR-CLI-2e gated
- [ ] BA-4 `output/replay_core.jsonl` is core/deterministic; Django enrichment only; no web-ready core payload
- [ ] BA-5 atomic write `.tmp/<run_key>` → hash → manifest last → rename; DB ingest after `ARTIFACT_WRITTEN`
- [ ] BA-6 Phase D manifest parsing via `artifact_manifest_reader.py` (Option 1, no core import)
- [ ] BA-7 subprocess: `shell=False`, list args, `sys.executable`, fixed cwd, timeout, log capture, traversal guard, typed exit codes
- [ ] BA-8 `game_data_snapshot.json` fail-closed; ORM → export → JSON adapter single path

## 2. Structural amendments (2nd review)

- [ ] SA-1 PR-CLI-2d drops `stack_runner` move (L2 + shared + contracts only)
- [ ] SA-2 `stack_runner` moves in PR-CLI-2e together with L3–L6 (no bridge ever)
- [ ] SA-3 PR-CLI-3 split into 3a (artifact shell) + 3b (full run)
- [ ] SA-4 PR-CLI-2c gains blocking `display_map` pure/viewer split
- [ ] SA-5 PR-CLI-6 uses Option A (in-process removed from request path entirely)

## 3. Cross-cutting guards (land in listed PR, stay green after)

- [ ] Guard A — schema version reject (`test_manifest_rejects_unknown_schema_version`) — PR-3a
- [ ] Guard B — replay monotonic (`test_replay_core_rejects_non_monotonic_frame_index`) — PR-3b
- [ ] Guard C — artifact root + run_key safety (`test_run_key_safety`, sibling-prefix variant) — PR-3a (reused PR-4)
- [ ] Guard D — JSONL streaming-only (`test_ssr_does_not_inline_full_replay`) — PR-3b policy, enforced PR-5
- [ ] Guard E — `replay_core` no django replay import (`test_replay_core_does_not_import_django_replay`) — PR-3b
- [ ] run_key collision writer-level (`test_artifact_writer_rejects_existing_dir`) — PR-1 (+ `--replace-existing` PR-3a)
- [ ] shim identity (`test_contract_shims_preserve_identity`) — PR-2d
- [ ] replay loader iterator (`test_artifact_replay_loader_returns_iterator`) — PR-5

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

**Slice 1 (done):** prereq DTO/snapshots/leaf move + `display_map` pure split + parity. **Slice 2 (pending):** `complete_map` + `acceptance_topology` move + serializer.

- [x] Step 1 — audited all 20 `reconstruction/*.py` + 3 `cleanup/*.py`; allowlist below (no wildcard)
- [x] Step 2 (BLOCKING) — split `display_map.py` → pure `complete_map_merge.py` (core) + viewer `display_map.py` (Django); `snapshot_map_replay` transforms relocated to core; `test_complete_map_merge.py` parity (no-db)
- [x] Step 3 (Slice 1 subset) — moved pure leaves to core + shimmed: `DecodedCellDTO`, `asteroid_map_coords`, `transport_components`, `reconstruction/{grid,result,evidence}`, `cleanup/result`. **Deferred to Slice 2:** `complete_map`, `acceptance_topology` (TYPE_CHECKING dep on `complete_map`)
- [ ] Step 4 (TDD, Slice 2) — `test_complete_map_serializer.py` round-trip
- [x] Step 5 — `scripts/test_reconstruction_narrow.ps1` green (25 passed); full asteroid_lab/replay suite parity green (235 + 509)
- [x] Step 6 — purity gate + import-matrix gates + ruff + `mypy src` green (38 files). Also fixed pre-existing PR-CLI-2b import-matrix violations (game_data↔asteroid_lab) + `structure.md` `var/runs/` governance.
- [ ] Done: pure recon in core; display/persist stay Django; serializer round-trips; recon gates green

## PR-CLI-2d — L2 + shared + contracts move (NO stack_runner)
Depends: CLI-2b, CLI-2c · File: [`pr-cli-2d-l2-shared-contracts-move.md`](pr-cli-2d-l2-shared-contracts-move.md)

- [ ] Step 1 — move contracts; rewrite intra-core imports; shim (re-export, not redefine)
- [ ] Step 2 — move L1 facade + L2 + shared route_probe; wire L2 port; shim
- [ ] Step 3 — split observability: pure metric builders → core; settings emit stays Django
- [ ] Step 4 (TDD) — `test_contract_shim_identity.py` (all parametrized symbols `is`-identical)
- [ ] Step 5 — confirm `stack_runner` (still Django) runs unchanged via core/current paths
- [ ] Step 6 — purity gate green with ZERO `django_apps` exceptions (no bridge)
- [ ] Step 7 — layer + budget + recon gates; ruff + mypy
- [ ] Done: contracts + L1 + L2 + shared in core, pure; shim identity green; stack_runner still Django; no bridge

## PR-CLI-2e — L3..L6 + stack_runner move (GATED)
Depends: CLI-2d AND L3 boundary-m-repack PR-B/C merged+green · File: [`pr-cli-2e-l3-gated-move.md`](pr-cli-2e-l3-gated-move.md)

GATE (BA-3) — all must be true before starting:
- [ ] boundary-m-repack PR-B merged to master
- [ ] PR-C merged or explicitly out of scope
- [ ] Lab gate green on master with new L3
- [ ] no open PR editing `layer_03_rim_mining_bundles/**`

Tasks:
- [ ] Step 0 — verify GATE; record merged boundary-m-repack SHA in PR description
- [ ] Step 1 — move L3–L6; rewrite imports to core paths; shim originals
- [ ] Step 2 — move `stack_runner`; point at in-core L3–L6; inject clock/flags
- [ ] Step 3 — confirm no `_l3_l6_bridge` anywhere; purity gate zero `django_apps` exceptions
- [ ] Step 4 — full layer + stack_runner budget + L3 repack tests
- [ ] Step 5 — ruff + mypy + recon gates
- [ ] Done: L3–L6 + stack_runner in core; no bridge; purity clean; behavior identical to master

## PR-CLI-3a — CLI artifact shell + `validate-artifact`
Depends: CLI-1 (+CLI-2a) · File: [`pr-cli-3a-artifact-shell.md`](pr-cli-3a-artifact-shell.md)

- [ ] Step 1 (TDD) — `test_run_key_safety.py` (traversal/separator/dot rejected; sibling-prefix variant)
- [ ] Step 2 (TDD) — `test_manifest_schema_version.py` (guard A)
- [ ] Step 3 (TDD) — `test_validate_artifact.py` (hash mismatch + lifecycle != ARTIFACT_WRITTEN fail)
- [ ] Step 4 — implement CLI shell + `validate-artifact`; `run` returns typed "stack unavailable"
- [ ] Step 5 — collision policy + `--replace-existing` (delete-then-rename on Windows)
- [ ] Step 6 — ruff + mypy + purity gate
- [ ] Done: CLI shell + validate-artifact work; run_key/root/schema/collision guards green; core-pure

## PR-CLI-3b — Full pure CLI `run` (decode → stack → artifacts)
Depends: CLI-2e AND CLI-3a · File: [`pr-cli-3b-full-run-stack.md`](pr-cli-3b-full-run-stack.md)

- [ ] Step 1 (TDD) — `test_cli_run_artifact.py` (final dir only after success; manifest hashes; outputs present; JSONL parses per line)
- [ ] Step 2 — implement `run_stack` use case (decode/cleanup/recon/in-core stack_runner + JSON snapshot adapter)
- [ ] Step 3 — implement `replay_core` emitter (core event construction only; Django enrichment left behind)
- [ ] Step 4 (TDD) — `test_replay_core_monotonic.py` (B) + `test_cli_exit_codes.py` (BA-7) + `test_replay_core_no_django_replay.py` (E)
- [ ] Step 5 — ruff + mypy + purity gate
- [ ] Done: full pure CLI produces valid atomic artifact incl. streaming JSONL; exit codes mapped; no Django reachable

## PR-CLI-4 — Django subprocess mode + artifact ingest
Depends: CLI-3b · File: [`pr-cli-4-django-subprocess-ingest.md`](pr-cli-4-django-subprocess-ingest.md)

- [ ] Step 1 — add `ASTEROID_LAB_SOLVER_MODE` setting + mode dispatch in `solver_runtime_entry`
- [ ] Step 2 (TDD) — `artifact_manifest_reader` validation + no-core-import AST test (BA-6)
- [ ] Step 3 (TDD) — `solver_subprocess_runner` (mock: `shell=False`, list args, timeout, traversal rejected) (BA-7)
- [ ] Step 4 (TDD) — `artifact_ingest` (hash mismatch fail-closed; partial rejected; index-only writes) (BA-5)
- [ ] Step 5 — wire HTTP/management opt-in flags
- [ ] Step 6 — integration test subprocess mode end-to-end (small fixture)
- [ ] Step 7 — ruff + mypy + full gate
- [ ] Done: both modes work; subprocess produces + ingests safely; index-only DB writes; integration green

## PR-CLI-5 — DB demotion + artifact-first replay
Depends: CLI-4 · File: [`pr-cli-5-db-demotion-replay.md`](pr-cli-5-db-demotion-replay.md)

- [ ] Step 1 — migration for `artifact_root` + `lifecycle_status` (nullable; no backfill)
- [ ] Step 2 (TDD) — `test_artifact_first_replay.py` (indexed artifact → JSONL wins over DB)
- [ ] Step 3 — artifact-first resolution in timeline payload + lazy handle; DB fallback
- [ ] Step 4 — summary service reads manifest mirror
- [ ] Step 5 (TDD) — `test_artifact_replay_loader_iterator.py` (iterator/generator, not list) + SSR no-inline guard D
- [ ] Step 6 (TDD) — fields documented as cache; core has no `create_solver_run` import (AST)
- [ ] Step 7 — ruff + mypy + full gate + recon narrow
- [ ] Done: artifact-first replay with DB fallback; new columns; fields documented as cache; gates green

## PR-CLI-6 — `subprocess_only` default + viewer import gate (Option A)
Depends: CLI-5 (ideally CLI-2e) · File: [`pr-cli-6-subprocess-only-default.md`](pr-cli-6-subprocess-only-default.md)

- [ ] Step 1 — set `subprocess_only`; remove in_process/subprocess branch selection from request path
- [ ] Step 2 — remove all core imports from `solver_runtime_entry`; subprocess runner references CLI by module string only
- [ ] Step 3 (TDD) — viewer import gate `test_asteroid_lab_viewer_no_core_import.py`, make green
- [ ] Step 4 — update docs (`structure.md`, runtime wiring, `current_plan.md`)
- [ ] Step 5 — full gate: ruff + black + mypy + pytest
- [ ] Done: `subprocess_only` only path; no core import in request flow; viewer gate green; docs updated; full gate green

---

## Global verification (run as PRs land)

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
