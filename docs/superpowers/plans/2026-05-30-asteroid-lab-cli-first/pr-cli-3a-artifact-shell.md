# PR-CLI-3a — CLI Artifact Shell + `validate-artifact`

**Type:** implementation change
**Depends on:** PR-CLI-1 (and PR-CLI-2a for DTOs)
**Enables:** PR-CLI-3b
**Branch (suggested):** `feat/asteroid-cli-first-artifact-shell`

---

## Goal

Ship the CLI **shell** and artifact tooling that does NOT require the full solver stack: argument parsing,
`validate-artifact`, manifest writing via `AtomicArtifactWriter`, and run_key/artifact-root safety. This
lands the atomic-artifact plumbing early, before L3–L6 + stack_runner are moved (PR-CLI-2e).

> **Structural amendment (2026-05-30):** PR-CLI-3 was split. The previous single PR claimed "No Django
> required to run" while depending on PR-CLI-2d, where stack_runner still bridged to `django_apps`. The
> artifact shell (3a) is decoupled from the full stack run (3b, which depends on PR-CLI-2e).

## Behavior contract

- `python -m shapez2_factory.interfaces.cli.asteroid_solve` exposes `validate-artifact` (and a `run` stub that returns a clear "stack not yet available" error until 3b).
- `validate-artifact` re-hashes files vs manifest, checks lifecycle status + schema version.
- Atomic write protocol (BA-5) used for any artifact emitted.
- run_key + artifact-root safety enforced (guards C below).

## Non-goals

- **No full stack run** (decode→cleanup→recon→stack) — that is PR-CLI-3b.
- No Django integration (PR-CLI-4).
- No HTTP `run-solver` console trace (BA-9 lands in PR-CLI-4).

---

## BA-9 amend (console observability — pure CLI only)

Normative detail: [`obs-console-log.md`](obs-console-log.md) · spec §11.

After the original 3a shell lands (or as a small follow-up before 3b):

| Action | Path | Why |
|--------|------|-----|
| Create | `src/shapez2_factory/adapters/asteroid_lab/cli_console.py` | stdlib-only `emit_cli_line` (BA-1) |
| Modify | `src/shapez2_factory/interfaces/cli/asteroid_solve.py` | start/end stderr one-liners per subcommand |
| Create | `tests/unit/shapez2_factory/test_cli_console.py` | formatter + env gates |
| Modify | `tests/unit/shapez2_factory/test_validate_artifact.py` | `capsys`: start/end substrings |

- Default: one **start** + one **end** line on stderr per `validate-artifact` / `run` (stub).
- Verbose layer lines: **not** in 3a amend (PR-CLI-3b `--verbose`).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Create | `src/shapez2_factory/interfaces/cli/asteroid_solve.py` | argparse: `validate-artifact`, `run` (stub) |
| Create | `src/shapez2_factory/interfaces/cli/__main__.py` | `python -m ...cli` dispatch |
| Create | `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py` | run_key + artifact-root validation |
| Create | `scripts/asteroid_solve.ps1` | Windows wrapper parity |
| Create | `tests/unit/shapez2_factory/test_validate_artifact.py` | hash/schema/lifecycle checks |
| Create | `tests/unit/shapez2_factory/test_run_key_safety.py` | guard C |
| Create | `tests/unit/shapez2_factory/test_manifest_schema_version.py` | guard A |

---

## Guards (architect-required)

### Guard A — schema version

```text
test_manifest_rejects_unknown_schema_version
```

`validate-artifact` and manifest load reject unsupported `schema_version` (fail-closed).

### Guard C — artifact root + run_key safety

```text
artifact_root must resolve under configured allowed root
run_key cannot contain path separators ('/', '\\')
run_key cannot be '.' or '..'
run_key matches ^[A-Za-z0-9._-]+$  (no traversal)
```

```python
# run_key_safety.py
def resolve_artifact_dir(allowed_root: Path, artifact_root: Path, run_key: str) -> Path:
    if run_key in (".", "..") or "/" in run_key or "\\" in run_key:
        raise ArtifactPathError(run_key)
    if not _RUN_KEY_RE.match(run_key):
        raise ArtifactPathError(run_key)
    root = allowed_root.resolve()
    final = (artifact_root / run_key).resolve()
    # Do NOT use str.startswith — "/var/runs2" would falsely match prefix "/var/runs".
    try:
        final.relative_to(root)
    except ValueError as exc:
        raise ArtifactPathError(run_key) from exc
    return final
```

> **String-prefix check forbidden (architect-required):** `str(final).startswith(str(root))` is a known
> traversal bug (`/var/runs2` matches prefix `/var/runs`). Use `Path.relative_to` (or
> `root == final or root in final.parents`). Add `test_run_key_safety_rejects_sibling_prefix_dir`.

### Run key collision policy

```text
existing final dir exists:
  default = reject (ArtifactExistsError)
  --replace-existing: allowed only when explicit; delete final dir inside lock before atomic rename
Windows: directory rename fails if target exists → must delete-then-rename under --replace-existing
```

---

## Tasks

- [x] **Step 1 (TDD):** `test_run_key_safety.py` — traversal/separator/dot/trailing-newline/empty rejected; valid key resolves under root; sibling-prefix (`runs` vs `runs2`) rejected via `relative_to`. `_RUN_KEY_RE` matched with `fullmatch` (not `match`) so `"abc\n"` is rejected. (6 tests)
- [x] **Step 2 (TDD):** `test_manifest_schema_version.py` — `parse_manifest_checked` rejects unknown/missing/non-int `schema_version` + non-dict top-level (`ManifestSchemaVersionError`); malformed JSON propagates as `json.JSONDecodeError`. Lenient `from_json` untouched. (6 tests)
- [x] **Step 3 (TDD):** `test_validate_artifact.py` — tampered file (hash mismatch), missing payload, lifecycle != ARTIFACT_WRITTEN, unknown schema, missing manifest, malformed JSON, bad lifecycle enum value, missing required field all → `VALIDATION_FAILED`; failure branch pinned via `capsys` stderr substring. (12 tests)
- [x] **Step 4:** CLI shell `interfaces/cli/asteroid_solve.py` + `__main__.py` + `scripts/asteroid_solve.ps1`; `validate-artifact` fully fail-closed (catches `ManifestSchemaVersionError`/`ValueError`/`KeyError`/`OSError`); `run` enforces Guard C (`resolve_artifact_dir`) then returns typed `STACK_UNAVAILABLE` until 3b. `--allowed-root` default = configured sandbox `var/runs`.
- [~] **Step 5:** `--replace-existing` flag exposed on `run`; delete-then-rename collision policy lives in `AtomicArtifactWriter` (PR-1). CLI flag parsed/forwarded but inert in the 3a stub — real write-path wiring deferred to PR-3b.
- [x] **Step 6:** ruff clean; `mypy src` clean (87 files); black clean; purity + import-matrix + shim-identity gates green (51 passed).
- [x] **Step 7 (BA-9 amend):** `adapters/asteroid_lab/cli_console.py` (stdlib-only `emit_cli_line` + `console_logging_enabled`, BA-1 pure) + start/end stderr one-liners in `asteroid_solve.main` for both `validate-artifact` and `run` stub (end carries `exit`/`elapsed_ms` via `time.monotonic`/`ok`; `run` carries `run_key`; end reflects exit code on `ArtifactPathError` path). `test_cli_console.py` (18 tests: formatter + env gates) + 3 `capsys` tests in `test_validate_artifact.py`. Verbose layer lines remain PR-CLI-3b scope. Gates: pytest 36 passed (incl. purity), ruff clean, `mypy src` clean (88 files), black clean.

## Tests / verification

```powershell
python -m shapez2_factory.interfaces.cli.asteroid_solve validate-artifact --dir var/runs/<existing>
python -m pytest tests/unit/shapez2_factory/test_validate_artifact.py tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/shapez2_factory/test_manifest_schema_version.py -v
python -m ruff check src/shapez2_factory/interfaces src/shapez2_factory/adapters/asteroid_lab
python -m mypy src
```

## Risks

- Windows directory rename + collision — covered by collision policy + delete-then-rename.
- `assumption:` allowed root is configurable; default `var/runs`.

## Done criteria

- CLI shell + validate-artifact work (fully fail-closed); run_key/root safety + schema version guards green; writer-level collision green (PR-1); core-pure. `--replace-existing` real wiring through CLI `run` deferred to PR-3b (stub run does not write).
