---
linear_issue: SHA-29
title: AtomicArtifactWriter accepts run_key outside Guard C charset (weaker than run_key_safety)
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unify AtomicArtifactWriter run_key validation with Guard C

## Source Issue

- Linear: SHA-29
- Status at planning time: In Progress (plans committed on branch `cursor/SHA-29-linear-todo-plan-writing-89a6`)
- Priority: Mid

## Problem

`AtomicArtifactWriter` uses a local `_validate_run_key` that only rejects empty keys, `.`/`..`, path separators, and control characters. It does not enforce the Guard C charset `^[A-Za-z0-9._-]+$` applied by `run_key_safety.resolve_artifact_dir`. Keys like `foo bar` or `foo@bar` succeed in the writer but fail Guard C, splitting the BA-5 artifact write path from the artifact design spec.

## Scope

- Delegate writer `run_key` validation to `run_key_safety` (or a shared helper) so charset rules cannot drift.
- Map `ArtifactPathError` to `InvalidRunKeyError` at the writer boundary.
- Add regression tests proving the writer rejects non-Guard-C keys (`foo bar`, `foo@bar`, `a*b`, `a:b`).
- Optionally replace duplicate `_RUN_KEY_RE` in `django_apps/asteroid_lab/services/solver_subprocess_runner.py` with the same guard.

## Non-goals

- Changing the allowed `run_key` charset.
- Altering CLI exit-code mapping or artifact manifest schema.
- Broad refactor of all path-safety call sites beyond run_key validation unification.

## Implementation Plan

1. **Read current guards** in `artifact_writer.py` (`_validate_run_key`) and `run_key_safety.py` (`_RUN_KEY_RE`, `resolve_artifact_dir`).
2. **Add shared charset helper** in `run_key_safety.py` (e.g. `assert_safe_run_key(run_key: str) -> None`) that raises `ArtifactPathError` for keys failing `_RUN_KEY_RE` plus existing dot/separator checks — or call regex check directly from writer without full `resolve_artifact_dir` (writer has no `allowed_root` at init).
3. **Replace `_validate_run_key` body** in `artifact_writer.py`:

```python
from shapez2_factory.adapters.asteroid_lab.run_key_safety import (
    ArtifactPathError,
    assert_safe_run_key,  # new export
)

def _validate_run_key(run_key: str) -> None:
    try:
        assert_safe_run_key(run_key)
    except ArtifactPathError as exc:
        raise InvalidRunKeyError(str(exc)) from exc
```

4. **Export helper** from `run_key_safety.__all__` if added; keep `resolve_artifact_dir` calling the same helper internally to avoid drift.
5. **Write failing regression test** `test_artifact_writer_rejects_non_guard_c_run_key` in new file `tests/unit/shapez2_factory/test_artifact_writer_run_key.py` (or extend `test_run_key_safety.py` with writer cases):

```python
import pytest
from shapez2_factory.adapters.asteroid_lab.artifact_writer import (
    AtomicArtifactWriter,
    InvalidRunKeyError,
)

@pytest.mark.parametrize("bad", ["foo bar", "foo@bar", "a*b", "a:b", "a$b"])
def test_artifact_writer_rejects_non_guard_c_run_key(tmp_path, bad: str) -> None:
    with pytest.raises(InvalidRunKeyError):
        AtomicArtifactWriter(tmp_path, bad)
```

6. **Run test** — expect FAIL before step 3, PASS after.
7. **Optional Django dedup** — in `solver_subprocess_runner.py`, replace local `_RUN_KEY_RE` with `assert_safe_run_key` or import regex from `run_key_safety`; map errors to `SolverSubprocessError` as today.
8. **Run validation gates**:

```bash
pytest tests/unit/shapez2_factory/test_artifact_writer_run_key.py tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/shapez2_factory/test_artifact_writer_collision.py -v
ruff check src/shapez2_factory/adapters/asteroid_lab/
mypy django_apps config src
```

9. **Commit** with message `fix(artifact): delegate writer run_key validation to Guard C`.

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py`
- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (optional dedup)
- `tests/unit/shapez2_factory/test_artifact_writer_run_key.py` (new)
- `tests/unit/shapez2_factory/test_run_key_safety.py` (may add helper unit tests)
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` (reference only)

## Validation Plan

- lint: `ruff check src/shapez2_factory/adapters/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_artifact_writer_run_key.py tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/shapez2_factory/test_artifact_writer_collision.py -v`
- build: N/A
- manual verification: `AtomicArtifactWriter(tmp, "foo bar")` raises `InvalidRunKeyError`; CLI `resolve_artifact_dir` behavior unchanged

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Writer init lacks `allowed_root`; use charset-only helper, not full `resolve_artifact_dir`, unless writer API gains root args.
- CLI path already calls `resolve_artifact_dir` before writer — regression is for direct/test callers.
- Low-priority `assert_safe_run_key` consolidation tracked separately (see low plan).
