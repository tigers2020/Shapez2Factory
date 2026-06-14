# Architecture Improvement Report — game data import boundary

**Thread slug:** `game-data-import-boundary`  
**Updated:** 2026-06-14  
**Kanban:** `.devtool/features/codebase-architecture-review-2026-06-14.md`  
**Grill decisions:** Q1=A, Q2=1, Q3=A, Q4=1, Q5=1

## Implementation status (as-built 2026-06-14)

**Branch:** `work/game-data-bundle-gate` · **Kanban:** `.devtool/features/codebase-architecture-review-2026-06-14.md`

| Item | As-built |
|------|----------|
| Bundle gate | `django_apps/game_data/services/bundle_gate.py` — `resolve_game_data_source_dir()`, `validate_game_data_bundle()` → `GameDataBundle` |
| Path candidates | `GAME_DATA_SOURCE_CANDIDATES`: `documents/game_data`, then `documents/knowledge/raw/game_data` |
| CLI `--source` | Optional (`None` → auto-resolve via gate) |
| Import flow | `assert_import_preconditions()` → `validate_game_data_bundle()` → `GameDataImporter(bundle).run()` → `run_post_import_guards()` |
| Verify flow | `validate_game_data_bundle()` → DB manifest hash + `ArtifactChecksum` mismatch count |
| Importer ctor | `GameDataImporter(bundle: GameDataBundle, ...)` — uses `bundle.manifest` / `bundle.manifest_hash` |
| Checksum rows | Post-gate: present or `incomplete_sections` missing → `import_status="ok"`; mismatch impossible at import |
| Tests | `tests/unit/game_data/test_bundle_gate.py`; `dump_paths.resolve_game_data_source_dir` delegates to production |

```text
CLI (no --source)
  → resolve_game_data_source_dir() / validate_game_data_bundle()   [fail-closed disk integrity]
  → assert_import_preconditions()                                  [migrations]
  → GameDataImporter(bundle)._load_manifest()                      [persist batch; all ok]
  → _import_* phases
  → run_post_import_guards()

CLI --verify
  → validate_game_data_bundle()
  → verify_game_data_source()                                      [DB reconcile]
```

Sections below retain the **pre-implementation** analysis that motivated the slice.

## Scope

Game data JSON bundle ingest boundary: CLI `import_game_data`, `GameDataImporter`, `import_guards`, `import_verify`, and test path resolution (`dump_paths.py`). **Not in scope:** `shapez_core` basedata IVVD pipeline, snapshot export modules (`game_data_snapshot_export`, `snapshots/builder`), importer phase decomposition.

## Repository State (at review time)

Dirty worktree (unrelated deletes, `uv.lock`, staged `documents/knowledge/raw/game_data/*`). `graphify-out/graph.json` present (2026-06-14). Review-only — no production edits in that session.

On disk at review time: only `documents/knowledge/raw/game_data/manifest.json` (+ artifacts). CLI default `--source documents/game_data` did not resolve without explicit path or test fallback. **Resolved by as-built gate auto-resolve** (see Implementation status above).

## Current Architecture Map

| Item | Finding |
|------|---------|
| Domain | Runtime-reflection JSON dump → normalized `game_data` ORM |
| CLI entry | `manage.py import_game_data` (`--source` optional, `--batch-name`, `--verify`) |
| Disk gate | `validate_game_data_bundle()` — fail-closed hash + missing-file policy |
| Import entry | `GameDataImporter(bundle).run()` — consumes pre-validated `GameDataBundle` |
| Pre-DB guards | `assert_import_preconditions()` — migrations only |
| Post-DB guards | `run_post_import_guards()` — `assert_no_domain_json_fields()` only |
| Manifest load | `_load_manifest()` records `ArtifactChecksum` with `ok` only (mismatch impossible post-gate) |
| Verify path | `verify_game_data_source()` — gate disk validate + DB batch reconcile |
| Path resolution | Production `bundle_gate.resolve_game_data_source_dir`; tests delegate via `dump_paths.py` |
| Hash helpers | `importers/source_loader.py` — `load_json`, `sha256_file` |
| Snapshot exports (out of scope) | `game_data_snapshot_export` (solver EVTC), `snapshots/builder` (web building bundle) |
| Tests | `test_bundle_gate.py`, loaddata fixtures + `resolve_game_data_dump_path` |

```text
CLI import (no --source)
  → assert_import_preconditions()          [migrations]
  → validate_game_data_bundle()            [fail-closed disk integrity]
  → GameDataImporter(bundle)._load_manifest()  [checksum rows; all ok]
  → _import_* phases (fixed order)
  → run_post_import_guards()               [JSONField ban]

CLI --verify
  → validate_game_data_bundle()            [disk]
  → verify_game_data_source()              [ImportBatch hash + DB mismatch count]
```

## Complexity Symptoms and Red Flags (pre-implementation — resolved by gate)

| Symptom / Red Flag | Evidence | Impact | Refactor Pressure |
|---|---|---|---|
| Information leakage — path policy | CLI default vs `dump_paths.py` candidates vs actual `knowledge/raw` location | `import_game_data` fails on fresh checkout without `--source` | High — blocks staged dump import |
| Temporal decomposition — integrity | Mismatch recorded in `_load_manifest`; caught later by `--verify` | Bad bundle can poison ORM; verify is separate step | High — silent data corruption risk |
| Error / special-case leakage | Callers must know import "succeeds" with mismatches | CI/dev confusion; false green imports | Medium |
| Repeated policy — sha256 + manifest | `_load_manifest`, `verify_game_data_source`, `dump_paths` | Three places understand bundle layout | Medium on manifest schema change |
| Shallow module — import_guards | Pre/post guards don't cover bundle integrity | Name suggests full gate; only migrations + JSONField | Low — extend via new module, not expand guards |
| Overexposure — importer owns path + hash | `GameDataImporter.__init__(source_dir)` assumes caller resolved valid bundle | Every new entrypoint duplicates path policy | Medium |

| Question | Answer |
|----------|--------|
| What simple future change is currently hard? | Import new staged dump from `knowledge/raw` with integrity guaranteed in one step |
| How many places must change? | CLI default, importer manifest load, verify, tests (`dump_paths`) — 4+ |
| What must callers know? | Correct `--source` path; that mismatch doesn't fail import; when to run `--verify` |
| What is implicit? | `incomplete_sections` allows missing files; mismatch is non-fatal today |
| Non-obvious dependency | Test fixtures use loaddata (Tier B dump), not live import — import path less exercised in CI |
| Organized by execution order? | Yes — validate-after-import via verify; should be validate-before-import |
| Module that should own bundle integrity? | `bundle_gate.py` (implemented) |

## Scattered Knowledge Found (pre-implementation — consolidated in gate)

| Shared Knowledge | Files / Areas | Status after PR 1 |
|---|---|---|
| Bundle source path candidates | `bundle_gate.GAME_DATA_SOURCE_CANDIDATES`, CLI, `dump_paths` | Production SoT; tests delegate |
| Manifest + per-file sha256 contract | `bundle_gate`, `importer._load_manifest`, `import_verify` | Fail-closed at gate; import records `ok` only |
| `incomplete_sections` missing-file policy | `bundle_gate.validate_game_data_bundle` | Enforced before import |
| Migration preflight | `import_guards` | Unchanged (DB, not bundle) |
| Canonical id uniqueness check | `validators.assert_canonical_ids_unique` | Unwired — defer |

## Better Together / Better Apart Decision

**Bring together:**

- Path resolution (candidate list + explicit override)
- Manifest load + per-file hash validation
- Fail-closed policy (`incomplete_sections` exception for missing only)
- Disk portion of `--verify` (reuse same validate function)

**Keep apart:**

- Migration precheck (`import_guards`) — DB migration state, not bundle knowledge
- Post-import JSONField ban (`run_post_import_guards`) — ORM schema invariant after write
- DB reconcile in `--verify` (latest `ImportBatch` comparison) — needs DB, but calls shared disk validate first
- `GameDataImporter._import_*` phases — domain mapping; consume validated bundle, don't re-validate
- Snapshot exports — different consumers, different payload shapes
- `shapez_core.basedata_import_service` — separate IVVD pipeline

**Chosen boundary:** `django_apps/game_data/services/bundle_gate.py`

**Reason:** Callers need one operation — "give me a validated bundle or raise" — before any DB mutation. Importer should not know path candidates or permissive checksum policy.

## Deep Module Candidate

**Implemented module:** `bundle_gate.py` (`django_apps/game_data/services/`)

**Owns:**

- Canonical source-dir candidate list and resolution order
- Manifest parse + `manifest_self_hash`
- Per-file hash verification against `manifest.file_hashes`
- Missing-file policy via `manifest.incomplete_sections`
- Typed `GameDataBundle` result (source_dir, manifest dict, manifest_hash, verified files index)
- Error codes: `BUNDLE_NOT_FOUND`, `FILE_MISSING`, `FILE_HASH_MISMATCH`, `MANIFEST_INVALID`

**Hides:**

- Candidate path tuple duplication in tests
- sha256 computation details
- Which manifest keys are required vs optional for gate (gate validates integrity, not full schema)

**Exposes:**

- `resolve_game_data_source_dir(explicit: Path | None = None) -> Path`
- `validate_game_data_bundle(source: Path | None = None) -> GameDataBundle`
- `GameDataBundleInvalid` with structured `code` + context

**Does not expose:**

- ORM `ImportBatch` / `ArtifactChecksum` creation (importer keeps batch persistence after gate passes)
- Migration checks
- Per-artifact import mapping logic

**Caller responsibilities:**

- Pass explicit `--source` when auto-resolve is wrong
- Run migration precheck before import (unchanged)
- Pass validated `GameDataBundle` to importer

**Module responsibilities:**

- Resolve or raise `BUNDLE_NOT_FOUND`
- Fail closed on hash mismatch before any DB write
- Allow missing files only when listed in `incomplete_sections`

**Invariants:**

- Every file in `file_hashes` with on-disk presence must match expected sha256
- Missing file allowed iff filename ∈ `incomplete_sections`
- `manifest_self_hash` computed from raw `manifest.json` bytes (same as today)

**Default behavior:**

- `source=None` → try candidates in order: `documents/game_data`, `documents/knowledge/raw/game_data`
- Explicit `source` → must contain `manifest.json` or raise

**Error policy:**

- Fail fast on first integrity violation (aggregate message optional in error string)
- No `--force` / no record-and-continue for mismatches (grill Q4=1)

**Special-case policy:**

- `incomplete_sections` is the only missing-file escape hatch

**Non-goals:**

- Splitting `GameDataImporter` by artifact
- Unifying snapshot export modules
- Wiring `assert_canonical_ids_unique` (separate slice if needed)
- JSON schema validation of artifact contents (future; gate is integrity-only)

## Interface Comment Draft

```text
Validate a game_data JSON bundle on disk before any ORM import.

Resolves the source directory from an explicit path or repo-standard candidates,
loads manifest.json, and verifies every file_hashes entry: on-disk files must
match the expected sha256; files listed in incomplete_sections may be absent.

Raises GameDataBundleInvalid on any integrity failure. Does not touch the database.
Import callers run this once, then pass GameDataBundle to GameDataImporter.

--verify reuses validate_game_data_bundle() for disk checks, then compares
manifest hash to the latest ImportBatch (DB reconcile — separate step).
```

## Design Alternatives

### Option A (recommended — grill Q2=1)

- **Summary:** `bundle_gate` module; production path SoT; fail-closed; verify reuses disk validate.
- **Interface:** `validate_game_data_bundle(source?) -> GameDataBundle`
- **Common case:** `call_command("import_game_data")` with no args on current tree → resolves `knowledge/raw/game_data`, validates, imports.
- **Rare case:** `import_game_data --source /custom/bundle` skips candidate walk.
- **Hides:** Path list, hash policy, incomplete_sections rules.
- **Pros:** Smallest reversible slice; fixes path drift + integrity in one PR; tests dedupe.
- **Cons:** Importer signature change (`GameDataBundle` vs raw `Path`).
- **Failure mode:** Gate too strict blocks dev with hand-edited JSON — fix manifest or file, don't bypass.

### Option B

- **Summary:** Fix CLI default path only + add fail-closed check inline in `_load_manifest` (no new module).
- **Interface:** unchanged `GameDataImporter(source_dir)`.
- **Pros:** Minimal file count.
- **Cons:** Shallow — path policy stays in CLI + tests; verify still duplicates disk logic; doesn't reduce caller knowledge.
- **Failure mode:** Next path move re-breaks CLI; verify/import drift returns.

### Comparison

| Question | Option A | Option B |
|----------|----------|----------|
| Simpler common case for callers? | Yes — one validate call | No — scattered |
| Hides implementation knowledge? | Yes | Partial |
| Eliminates repeated errors? | Yes | Partial |
| Avoids temporal decomposition? | Yes | No |
| Safer migration path? | Yes — incremental | Yes but shallow |
| Easier interface comment? | Yes | No |

## Recommendation

Implement **Option A — `bundle_gate` module** with grill-locked decisions:

1. Production owns path candidates (Q3=A)
2. Fail-closed on hash mismatch; `incomplete_sections` only for missing (Q4=1)
3. `--verify` = `validate_game_data_bundle()` + DB batch reconcile (Q5=1)
4. Migration precheck stays in `import_guards`

## Minimal Change Plan

**PR 1 — introduce gate + wire entrypoints (single PR, narrow)**

1. Add `django_apps/game_data/services/bundle_gate.py`:
   - `GAME_DATA_SOURCE_CANDIDATES` tuple
   - `GameDataBundle` dataclass
   - `GameDataBundleInvalid` + error codes
   - `resolve_game_data_source_dir()`, `validate_game_data_bundle()`
2. Refactor `tests/unit/game_data/dump_paths.py` to delegate `resolve_game_data_source_dir` to production (re-export for backward compat).
3. Update `import_game_data` command:
   - Default `--source` to `None` (auto-resolve via gate) or keep arg optional
   - Import path: preconditions → `validate_game_data_bundle` → `GameDataImporter(bundle).run()`
   - Verify path: `validate_game_data_bundle` → existing DB reconcile (refactor `verify_game_data_source` to call gate first)
4. Refactor `GameDataImporter`:
   - Accept `GameDataBundle` (or bundle + keep path compat shim one release)
   - `_load_manifest` uses pre-validated manifest/hash; **remove** permissive mismatch recording OR record all `ok` only (mismatch impossible post-gate)
5. Tests:
   - Unit tests for gate: path resolve, hash ok, hash mismatch raises, incomplete missing allowed, missing not in incomplete raises
   - Update `test_dump_paths` to assert production delegation
   - Existing import integration tests pass with auto-resolve

**Stop after PR 1.** Do not split importer phases or wire `assert_canonical_ids_unique` without separate approval.

## Tests / Validation

```bash
python -m pytest tests/unit/game_data/test_dump_paths.py tests/unit/game_data/test_import_guards.py -q
python -m pytest tests/unit/game_data/ -q -k "bundle or import or dump"
python manage.py import_game_data --verify
python manage.py import_game_data   # no --source; should resolve knowledge/raw on current tree
ruff check django_apps/game_data/
```

## Stop Conditions

- Gate blocks legitimate Tier B loaddata fixtures → gate is import-only; loaddata path unchanged
- Parity tests require duplicate candidate list → tests must import production helper (Q3=A)
- Importer refactor touches >5 import phases → stop; gate-only PR without phase moves

## Open Questions (resolved in PR 1)

- **Importer ctor:** `GameDataBundle` only — all call sites updated in same PR.
- **Aggregate vs fail-fast errors:** Collect-all mismatches in one `GameDataBundleInvalid` message.
- **Docs path:** `documents/knowledge/raw/game_data/README.md` documents auto-resolve; architecture spec/report updated in docs-sync pass.
