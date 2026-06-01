# Django Residue Audit - CLI-first Split

**Status:** ACTIVE evidence note (2026-05-31, post-merge)  
**Scope:** Current `django_apps/asteroid_lab/**` residue against the CLI-first target state.

## Conclusion

This branch (`feat/layer-03-boundary-m-repack-greedy`) has **merged `origin/master`** through
`b566d4f8` (PR #134 L3–L6 stack, PR #135 decode/cleanup/reconstruction pipeline) plus local
PR-CLI-3b–6 work (subprocess-only request path, artifact ingest, artifact-first replay, BA-9 logs).

**Solver execution is CLI/core-only.** Django owns registry, ingest, viewer enrichment, and
compatibility shims. Repository-wide viewer-only Django is **not** claimed: public shim import paths
and replay viewer modules remain by design.

## CLI separation verification (2026-05-31)

| Surface | Owner | Gate / test | Result |
|---------|-------|-------------|--------|
| `python -m shapez2_factory.interfaces.cli.asteroid_solve run` | core | `test_cli_run_artifact.py`, BA-1 purity | pass |
| `validate-artifact` | core adapters | `test_validate_artifact.py` | pass |
| `python manage.py run_solver` | Django → subprocess CLI | `test_run_solver_management_command.py` | pass |
| HTTP `POST …/run-solver/` | subprocess_only, no core import | `test_asteroid_lab_viewer_no_core_import.py` | pass |
| `export_game_data_snapshot` | Django (BA-8) | ORM export path; not solver input | intentional |
| L3–L6 stack | `src/.../stack_runner.py` | `test_stack_runner_core_boundary.py`, layers suite | pass |
| decode/cleanup/recon pipeline | `src/.../domain/asteroid_lab/**` | PR-CLI-2f shims + `test_pipeline_importable_without_django.py` | pass |
| `replay_core.jsonl` | core emitter | `test_replay_core_monotonic.py`, guard E | pass |

**Known non-blockers (documented):** core L5/L6 layer `run.py` headers may say "stub" for algorithm
completeness; CLI-first **relocation** is done. Layer algorithm tuning is out of CLI-first scope.

## Verified complete

- `src/shapez2_factory/**` remains Django-free under the BA-1 purity gate.
- Contract shim identity holds for moved DTO/contract symbols.
- PR-CLI-2f: `django_apps/asteroid_lab/reconstruction/pipeline.py` and `cleanup/pipeline.py` are
  **shims** to `shapez2_factory.domain.asteroid_lab.*` (no duplicate algorithm bodies).
- BA-9 console observability:
  - pure CLI `asteroid_solve` start/end + optional `layer_done`,
  - `python manage.py run_solver` start/end,
  - HTTP subprocess-only `POST .../run-solver/` start/end,
  - subprocess tee to parent TTY + `logs/subprocess.log`.

## Django code that is still intentional

| Area | Current role | Why kept |
|------|--------------|----------|
| `django_apps/asteroid_lab/layers/layer_03_*` … `layer_06_*` | Compatibility shims | Public import paths; core owns bodies |
| `django_apps/asteroid_lab/layers/stack_runner.py` | Django wrapper | L1 ORM, post-summary logging, delegates L2–L6 to core |
| `artifact_manifest_reader.py` | Plain JSON validation | BA-6: no core import |
| `solver_subprocess_runner.py`, `subprocess_stream_tee.py` | Subprocess boundary + tee | CLI referenced by module string only |
| `django_apps/asteroid_lab/replay/**` | Viewer enrichment | May import pure domain helpers and core DTO contracts only; no solver stack execution |
| `reconstruction/display_map.py` | Viewer/persist adapter | PR-CLI-2c split |
| ORM models/admin/services | Registry, cache, admin | FD-3 |

## Removed or cleaned

- Deleted orphaned `django_apps/asteroid_lab/services/solver_runtime_rim_stack.py` (legacy in-process L3/L4 path; only referenced by its unit test).
- Deleted orphaned `django_apps/asteroid_lab/services/solver_layer_stack_log.py` (legacy stack-log facade; no importers).
- Deleted `django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py`; artifact viewer compose now maps stored `replay_core.jsonl` + `complete_map` only and does not rerun L2/L3 from Django.
- Merged `origin/master` #134/#135; L3 django files are shims only.
- Deleted `solver_runtime_layer02.py`; request path is `subprocess_only`.
- Stale `run_solver` "stub only" help text removed.
- `STACK_NOT_IMPLEMENTED` dead constant removed from `run_stack.py`.
- Replay/viewer AST gate: no solver execution core or `interfaces.cli` imports under `replay/`; pure contracts/domain helpers are allowlisted.
- Viewer/services shim gate: `django_apps/asteroid_lab/replay/*.py` and
  `django_apps/asteroid_lab/services/*.py` must not import `django_apps.asteroid_lab.layers.*`.
- Replay and non-shim layer algorithm tests now target `shapez2_factory.application.asteroid_lab.layers.*`
  directly. Remaining Django layer imports are explicit compatibility-shim, L1 ORM facade, or
  post-summary logging boundary tests.

## Orphan scan (2026-05-31)

Scanned `django_apps/asteroid_lab/services/*.py` for modules with zero direct importers. Candidates
(`lab_replay_timeline_payload`, `project_service`, `topology_service`, etc.) are **false positives**:
they are imported from `django_apps/web/**`, `services/__init__.py` lazy exports, or tests.

No additional solver-runtime orphan modules beyond `solver_runtime_layer02`,
`solver_runtime_rim_stack`, `solver_layer_stack_log`, and `artifact_runtime_replay_compose`
(already deleted on branch).

Placeholder/stub string scan is intentionally not zero: remaining hits are persisted DB field names
(`output_stub_coord`, `is_placeholder`), viewer overlay labels, summary fallback text, or compatibility
shim constants. No additional Django-hosted algorithm placeholder body was found outside the documented
shim surface.

## Suggested PR packaging (uncommitted WIP @ `5610d55e`)

When ready to commit (not done automatically):

| PR | Paths (scope) |
|----|----------------|
| **PR-A runtime** | `src/shapez2_factory/**` (CLI, run_stack, replay_core), `django_apps/asteroid_lab/services/{solver_runtime_entry,solver_subprocess_runner,artifact_*,subprocess_stream_tee}.py`, `management/commands/run_solver.py`, `models.py` + migration `0017`, related tests |
| **PR-B BA-9** | `cli_console.py`, `observability/cli_invoke_trace.py`, `config/settings.py`, `public_pages.py`, log tests |
| **PR-C docs** | `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/**`, spec §11, `documents/ai/current_plan.md` |

Exclude: `.cursor/skills/`, `media/`, `locale/`, unrelated `genetic_sample/miner_seed_constants.py`.

## Remaining optional follow-up (not CLI-first blockers)

1. Retire django `layers/**` shim surfaces when all callers import core directly.
2. Expand viewer import gate to additional web views if new core imports appear.
3. Repo-wide `mypy django_apps config src` baseline (~1030 pre-existing errors).

## Last verification

2026-05-31 local WIP: viewer/replay gate 18 passed; CLI log bundle 27 passed;
`tests/unit/asteroid_lab/layers` 92 passed; `scripts/test_fast.ps1` 1556 passed, 1 xfailed.
`ruff check .`, `black --check .`, `git diff --check`, and `mypy src` passed. Repo-wide
`mypy django_apps config src` remains baseline-red with 1032 Django typing errors.

## Evidence commands

```powershell
python -m pytest tests\unit\architecture\test_shapez2_factory_core_purity.py tests\unit\architecture\test_contract_shim_identity.py tests\unit\shapez2_factory\test_core_stack_runner_importable_without_django.py tests\unit\asteroid_lab\layers\test_stack_runner_core_boundary.py tests\unit\shapez2_factory\test_cli_run_artifact.py tests\unit\architecture\test_asteroid_lab_viewer_no_core_import.py -v --basetemp=F:\Python_Projects\shapez2Factory\var\pytest-basetemp
python -m pytest tests\unit\architecture\test_asteroid_lab_viewer_no_core_import.py -v
python -m pytest tests\unit\asteroid_lab\test_cli_invoke_trace.py tests\unit\web\test_asteroid_run_solver_cli_trace.py tests\unit\asteroid_lab\test_run_solver_management_command.py tests\unit\shapez2_factory\test_cli_console.py -v
python -m pytest tests\unit\asteroid_lab\layers -v --basetemp=F:\Python_Projects\shapez2Factory\var\pytest-basetemp
python -m pytest tests\unit\architecture\test_asteroid_lab_viewer_no_core_import.py tests\unit\asteroid_lab\test_artifact_replay_viewer_compose.py tests\integration\web\test_lab_replay_compose_defer.py -v
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m black --check .
git diff --check
```
