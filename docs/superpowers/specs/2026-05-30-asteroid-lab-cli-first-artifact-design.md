# Asteroid Lab CLI-first Artifact Design — Normative Contract

**Status:** ACTIVE (authored in PR-CLI-0)
**Date:** 2026-05-30
**Owner:** Asteroid Lab core extraction (`src/shapez2_factory/`)
**Plan set:** [`../plans/2026-05-30-asteroid-lab-cli-first/README.md`](../plans/2026-05-30-asteroid-lab-cli-first/README.md)
**ADR:** [`../../adr/ADR-006-asteroid-lab-cli-first-artifact.md`](../../adr/ADR-006-asteroid-lab-cli-first-artifact.md)
**Invariants:** [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)

This document is the single source of truth for the CLI-first artifact contract. Each later PR
(PR-CLI-1 … PR-CLI-6) restates the blocking amendment(s) it touches and MUST NOT deviate from the
schemas declared here. No solver code moves in PR-CLI-0.

---

## Goal

Extract the Asteroid Lab solver into a pure, Django-free core package (`src/shapez2_factory/`) that
runs as a CLI subprocess and emits a deterministic, hash-verified **artifact directory**. Django
becomes a run registry / artifact index / option cache and an enrichment + viewer layer only — never
the solver state source of truth.

## Frozen decisions (must hold in every PR)

1. Package root = `src/shapez2_factory/`.
2. Hybrid now → subprocess/artifact default later (`subprocess_only` = target).
3. DB = run registry / artifact index / option cache only (not solver state SoT).

## Normative blocking amendments (BA-1 … BA-8)

| ID | Rule |
|----|------|
| BA-1 | `src/shapez2_factory/**` MUST NOT import `django`, `django_apps`, `config`, ORM, settings, or web/replay UI. Shims point one direction only (Django → core). |
| BA-2 | No monolithic move PR. Moves split across PR-CLI-2a … 2e; CLI is its own PR. |
| BA-3 | No active L3 relocation during boundary-m-repack PR-B/C; PR-CLI-2e is gated on those landing green. |
| BA-4 | `output/replay_core.jsonl` is core/deterministic; Django performs enrichment only; no web-ready core payload. |
| BA-5 | Atomic write: staging `.tmp/<run_key>` → hash payloads → manifest written **last** → rename to final; DB ingest only after `ARTIFACT_WRITTEN`. |
| BA-6 | Phase D (Django) manifest parsing uses `artifact_manifest_reader.py` (Option 1); reader MUST NOT import core. |
| BA-7 | Subprocess: `shell=False`, list args, `sys.executable`, fixed cwd, timeout, log capture, path-traversal guard, typed exit codes. |
| BA-8 | `game_data_snapshot.json` is fail-closed; single path ORM → export → JSON adapter. |

---

## 1. Artifact directory layout

```text
var/runs/<run_key>/                 # final, immutable after finalize
  manifest.json                     # written LAST; see §2
  output/
    replay_core.jsonl               # one JSON object per line; see §3
    solver_summary.json             # core summary (no web/template fields)
    complete_map.json               # reconstruction complete-map serialization
  input/
    game_data_snapshot.json         # snapshot used for this run; see §7
  logs/
    subprocess.log                  # stdout+stderr capture (BA-7)

var/runs/.tmp/<run_key>/            # staging; same layout; removed after rename
```

- **`run_key`** is the only path segment derived from caller input. It MUST be validated (see §C
  run_key safety): no path separators (`/`, `\`), no `.`/`..` segments, no absolute paths, no
  null/control characters, no sibling-prefix escape. The artifact root is fixed (`var/runs/`); the
  resolved final path MUST stay strictly under it.
- The **final** directory MUST NOT exist before atomic finalize. The writer rejects an existing
  final dir and an existing staging dir by default (`test_artifact_writer_rejects_existing_dir`,
  `_existing_staging`). `--replace-existing` (PR-CLI-3a) is the only opt-in override (delete-then-
  rename on Windows).

## 2. `manifest.json` schema

```jsonc
{
  "schema_version": 1,                 // integer; unknown version rejected (Guard A)
  "run_key": "<validated run_key>",
  "lifecycle_status": "ARTIFACT_WRITTEN",  // immutable artifact lifecycle (see §4)
  "created_at_utc": "2026-05-30T14:00:00Z",
  "core_build_id": "<core build/version id>",
  "content_hashes": {                  // relpath -> sha256 hex; EXCLUDES manifest.json
    "output/replay_core.jsonl": "<sha256>",
    "output/solver_summary.json": "<sha256>",
    "output/complete_map.json": "<sha256>",
    "input/game_data_snapshot.json": "<sha256>"
  },
  "paths": {                           // logical name -> relpath
    "replay_core": "output/replay_core.jsonl",
    "solver_summary": "output/solver_summary.json",
    "complete_map": "output/complete_map.json",
    "game_data_snapshot": "input/game_data_snapshot.json"
  },
  "game_data_provenance": { /* §7 provenance fields; manifest-side key set finalized in PR-CLI-1/4 (TODO) */ },
  "error_code": null                   // SolverRuntimeEntryErrorCode value or null
}
```

- **`content_hashes` excludes `manifest.json`.** The manifest is the last write and cannot hash
  itself. It covers **every artifact payload file written before manifest finalization**
  (`test_content_hashes_excludes_manifest`).
- If a manifest integrity digest is required, `manifest_sha256` is computed **externally** by the
  validator / DB ingest and is **NOT** stored inside `content_hashes`.
- Unknown `schema_version` MUST be rejected by `validate-artifact` and by Django ingest
  (`test_manifest_rejects_unknown_schema_version`, Guard A).

## 3. `replay_core.jsonl` line schema

- One JSON object per line; UTF-8; LF line terminator; deterministic ordering.
- `frame_index` is an integer, starts at 0, and is **contiguous** (strictly increasing by exactly 1).
  Non-monotonic input is rejected (`test_replay_core_rejects_non_monotonic_frame_index`, Guard B). The
  CLI-3b test MUST enforce the step-of-1 contiguity, not merely non-decreasing ordering.
- Output-only: NO web/template/SSR fields, NO `map_view` HTML, NO Django enrichment.
- **`event_type` reuses the value semantics** of
  [`django_apps/asteroid_lab/replay/event_types.py`](../../../django_apps/asteroid_lab/replay/event_types.py)
  but the pure enum/const definitions are **copied/relocated into core**. **Core MUST NOT import**
  `django_apps.asteroid_lab.replay.event_types` (or any `django_apps` module) — that file is a
  reference for values only (`test_replay_core_does_not_import_django_replay`, Guard E).
- Each line carries at minimum: `frame_index` (int), `event_type` (registered const), `payload`
  (object). Single replay timeline; global monotonic `frame_index` (invariant: Lab replay timeline).

## 4. Run lifecycle enum

```text
QUEUED | RUNNING | ARTIFACT_WRITING | ARTIFACT_WRITTEN | INDEXED | SUCCEEDED | FAILED
```

**Authority split (normative):**

- `manifest.lifecycle_status` is the **artifact** lifecycle. After atomic finalize it is
  `ARTIFACT_WRITTEN` and is **immutable** thereafter.
- `QUEUED` / `RUNNING` / `ARTIFACT_WRITING` are **pre-finalize orchestration / DB** states only; they
  are never persisted as a finalized `manifest.lifecycle_status` (a finalized manifest is always
  `ARTIFACT_WRITTEN`).
- `INDEXED` / `SUCCEEDED` / `FAILED` are **DB / `SolverRun`** lifecycle states only.
- **Django ingest MUST NEVER rewrite `manifest.json`.** `validate-artifact` therefore only ever
  expects `ARTIFACT_WRITTEN` in the manifest; any other manifest value fails validation.

## 5. Atomic write protocol (BA-5)

1. Create staging `var/runs/.tmp/<run_key>/` (reject if it already exists).
2. Write all payload files (`output/*`, `input/*`, `logs/*`) into staging.
3. Compute sha256 of each payload file → `content_hashes` (manifest excluded).
4. Write `manifest.json` **last** with `lifecycle_status = ARTIFACT_WRITTEN`.
5. Rename staging → final `var/runs/<run_key>/` (reject if final already exists, unless
   `--replace-existing`). Rename is the commit point; no partial final dir is ever observable.
6. DB ingest happens **only after** a valid `ARTIFACT_WRITTEN` final dir exists.

## 6. Subprocess contract (BA-7)

- Invocation: `shell=False`, **list** args (never a joined string), `sys.executable`, fixed cwd
  (repo root), explicit timeout.
- stdout + stderr captured to `logs/subprocess.log`.
- Path-traversal guard on `run_key` and artifact root before spawning.
- Exit code → `SolverRuntimeEntryErrorCode` mapping (see table below). Today only `DECODE_FAILED`
  exists in [`solver_runtime_types.py`](../../../django_apps/asteroid_lab/services/solver_runtime_types.py);
  the table aligns with that enum **once CLI-3/CLI-4 add the declared values**.

### Exit-code mapping table

| Exit | Meaning | error_code |
|------|---------|------------|
| 0 | success | none |
| 2 | validation failed | `VALIDATION_FAILED` |
| 3 | timeout fail-closed | `SOLVER_TIME_BUDGET_EXCEEDED` |
| 4 | snapshot missing/invalid | `GAME_DATA_SNAPSHOT_INVALID` (new enum value) |
| 5 | decode failed | `DECODE_FAILED` |
| 1 | unexpected | `SOLVER_INTERNAL_ERROR` |

> New enum values (`VALIDATION_FAILED`, `SOLVER_TIME_BUDGET_EXCEEDED`,
> `GAME_DATA_SNAPSHOT_INVALID`, `SOLVER_INTERNAL_ERROR`) are **added in the PR that implements them**
> (CLI-3 / CLI-4), not in PR-CLI-0. This spec only declares them. `DECODE_FAILED` already exists.
>
> **Distinction from existing `RTTP_VALIDATION_FAILED`:** the new exit-2 `VALIDATION_FAILED` is the
> CLI's **final read-only artifact/layout validation** failure (ADR-003 assertion gate). It is a
> distinct, separately-named code from the legacy RTTP-specific `RTTP_VALIDATION_FAILED`; CLI-3/CLI-4
> MUST NOT collapse the two into one ambiguous "validation failed" code.

## 7. `game_data_snapshot.json` (BA-8)

- Single production path: ORM → `export_game_data_snapshot` → JSON file → core JSON adapter
  (`orm_game_data_rules.py` is the only ORM-touching path; consistent with ADR-004).
- Schema carries: `snapshot_schema_version`, solver subset of building/transport rules,
  `content_hash` (sha256 of solver subset; excludes `built_at_utc`), provenance fields.
- **Fail-closed** on: file missing, unsupported `snapshot_schema_version`, `content_hash` mismatch.
  Each fail-closed case maps to exit code 4 (`GAME_DATA_SNAPSHOT_INVALID`).
- Snapshot **body** stays **not** algorithm input beyond what ADR-004 already permits; the artifact
  records it only as the deterministic input pin for the run.

## 8. BA-1 core purity — forbidden import prefixes

`src/shapez2_factory/**` MUST NOT import any module whose top-level package is one of:

```text
django, django_apps, config
```

Additionally, no module path may contain `django_apps` anywhere. Enforced by AST gate
`tests/unit/architecture/test_shapez2_factory_core_purity.py`. The gate is **active and green** from
PR-CLI-0 (empty/scaffold package tolerated) and stays green as real modules land.

## 9. BA-4 replay boundary — core vs viewer responsibility

| Concern | Core (`src/shapez2_factory`) | Viewer / Django (`django_apps`) |
|---------|------------------------------|----------------------------------|
| `replay_core.jsonl` emission | YES (deterministic events) | NO |
| `event_type` value semantics | owns relocated pure const | reference only |
| Web/SSR payload, `map_view` HTML | NO | YES (enrichment) |
| Timeline composition for UI | NO | YES |
| Algorithm input from replay | FORBIDDEN | FORBIDDEN (invariant: no payload semantic substitution) |

Core produces only the deterministic core stream; all UI/web-ready shaping is Django enrichment.

## 10. BA-6 manifest reader — Option 1

- Django reads manifests through `django_apps/asteroid_lab/.../artifact_manifest_reader.py`
  (added in PR-CLI-4).
- The reader parses `manifest.json` as plain JSON + dataclasses; it **MUST NOT import** any
  `src/shapez2_factory` core module (verified by a no-core-import AST test in PR-CLI-4, BA-6).
- This keeps the Django side decoupled from core internals: the manifest JSON schema (§2) is the
  only contract crossing the boundary.

---

## Cross-cutting guards (where each lands)

| Guard | Lands in | Test |
|-------|----------|------|
| A schema version reject | PR-CLI-3a | `test_manifest_rejects_unknown_schema_version` |
| B replay monotonic | PR-CLI-3b | `test_replay_core_rejects_non_monotonic_frame_index` |
| C run_key + root safety | PR-CLI-3a (reused PR-CLI-4) | `test_run_key_safety` |
| D JSONL streaming-only | PR-CLI-3b policy, enforced PR-CLI-5 | `test_ssr_does_not_inline_full_replay` |
| E replay_core no-django | PR-CLI-3b | `test_replay_core_does_not_import_django_replay` |
| run_key collision (writer) | PR-CLI-1 (+ `--replace-existing` PR-CLI-3a) | `test_artifact_writer_rejects_existing_dir` |
| shim identity | PR-CLI-2d | `test_contract_shims_preserve_identity` |
| replay loader iterator | PR-CLI-5 | `test_artifact_replay_loader_returns_iterator` |

## Invariant references

- Replay: single replay timeline; global monotonic `frame_index`; no payload semantic substitution;
  metrics/NDJSON/artifact are **not** algorithm input
  ([`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) Replay row).
- Enums: `event_type` / `issue_code` / `failure_reason` are StrEnum/const — no free-form strings.
- Validation: read-only assert; no repair (ADR-003).
- Snapshot boundary: ORM → export → adapter single path (ADR-004).

## Risks

- `uncertain:` exact `replay_core` line fields finalized in PR-CLI-3b; §3 fixes the invariant subset
  (`frame_index`, `event_type`, `payload`).
- `assumption:` `var/runs/` is the chosen artifact root; confirmed in `structure.md` (PR-CLI-0 Step 3).
- Spec drift if later PRs deviate — each PR restates the BA it touches and cites this spec.
