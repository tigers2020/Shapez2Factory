# PR-CLI-5 — DB Demotion + Artifact-First Replay

**Type:** contract change · implementation change
**Depends on:** PR-CLI-4
**Enables:** PR-CLI-6
**Branch (suggested):** `feat/asteroid-cli-first-db-demotion`

---

## Goal

Make the artifact directory the source of truth for replay. `SolverRun.*_json` columns become caches/mirrors
of artifact files, and Lab replay loading reads `replay_core.jsonl` from the artifact path first, falling
back to DB only during transition.

## Behavior contract

- Lab replay payload prefers artifact `replay_core.jsonl` when `artifact_root` is indexed.
- `SolverRun` JSON fields documented + treated as cache mirrors, not authority.
- Core / CLI never call `create_solver_run` (enforced).
- DB fallback path remains for legacy runs without artifacts.

## Guard D — replay JSONL streaming-only (architect-required, 2026-05-30)

```text
replay_core.jsonl is stream-read.
Django MUST NOT inline the full replay JSON into the SSR page.
```

This protects against the prior TTFB / large-payload regressions (13D-SSR / 13G). The viewer reads frames
lazily (existing lazy-handle path) from the JSONL file; SSR ships only shell + handle, never the full blob.

- Test: `test_ssr_does_not_inline_full_replay` — assert page payload excludes full frame array when artifact present.
- Reuse existing lazy-load contract ([`lab_replay_lazy_handle.py`](../../../../django_apps/asteroid_lab/services/lab_replay_lazy_handle.py)).

### Generator/streaming loader contract (architect-required, 2026-05-30)

The artifact replay loader must **not** `json.load` the whole `replay_core.jsonl` into a list. It returns a
frame **iterator/generator** read line-by-line, so memory stays bounded regardless of run size (13D/13G
regression prevention).

```text
test_artifact_replay_loader_returns_iterator
  - loader(path) returns an Iterator/Generator, not list/tuple
  - reading N frames does not require materializing all frames
  - (optional) assert peak does not hold full file: read first frame from a large fixture without loading rest
```

```python
# expected loader shape
def iter_replay_core_frames(path: Path) -> Iterator[ReplayFrameDTO]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:               # streaming; never read().splitlines() of the whole file
            ...
            yield frame
```

## Non-goals

- No removal of `ReplayFrame` model (deprecate for new runs only).
- No default mode flip (PR-CLI-6).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`services/lab_replay_timeline_payload.py`](../../../../django_apps/asteroid_lab/services/lab_replay_timeline_payload.py) | artifact-first load, DB fallback |
| Modify | [`services/lab_replay_lazy_handle.py`](../../../../django_apps/asteroid_lab/services/lab_replay_lazy_handle.py) | resolve artifact path |
| Modify | [`services/solver_run_lab_summary.py`](../../../../django_apps/asteroid_lab/services/solver_run_lab_summary.py) | summary from artifact mirror |
| Modify | [`models.py`](../../../../django_apps/asteroid_lab/models.py) `SolverRun` | docstrings: fields = cache/index; add `artifact_root`, `lifecycle_status` if missing |
| Create | migration | add `artifact_root` / `lifecycle_status` columns (index/cache role) |
| Modify | [`services/experiment_service.py`](../../../../django_apps/asteroid_lab/services/experiment_service.py) | reinforce UI-only; guard against core calling it |
| Create | `tests/unit/asteroid_lab/test_artifact_first_replay.py` | artifact path wins over DB |
| Create | `tests/unit/asteroid_lab/test_solver_run_fields_are_cache.py` | doc/contract test |
| Create | `tests/integration/web/test_ssr_does_not_inline_full_replay.py` | guard D |
| Create | `tests/unit/asteroid_lab/test_artifact_replay_loader_iterator.py` | streaming loader contract |

---

## Field role table (contract)

| Field | After PR-CLI-5 |
|-------|----------------|
| `solver_runtime_replay_frames_json` | cache mirror of `replay_core.jsonl` (legacy/fallback) |
| `lab_replay_manifest_summary_json` | mirror of manifest summary |
| `config_json` | options + `artifact_root` pointer |
| `artifact_root` (new) | filesystem index pointer |
| `lifecycle_status` (new) | `QUEUED..SUCCEEDED/FAILED` |
| `ReplayFrame` rows | deprecated for new runs; lazy-load reads artifact |

## Tasks

- [ ] **Step 1:** Migration for `artifact_root` + `lifecycle_status` (nullable; backfill not required).
- [ ] **Step 2 (TDD):** `test_artifact_first_replay.py` — given indexed artifact, payload reads JSONL file not DB.
- [ ] **Step 3:** Implement artifact-first resolution in timeline payload + lazy handle; DB fallback when no `artifact_root`.
- [ ] **Step 4:** Summary service reads manifest mirror.
- [ ] **Step 5 (TDD):** `test_artifact_replay_loader_iterator.py` — loader returns iterator/generator, not list; SSR no-inline guard D.
- [ ] **Step 6 (TDD):** contract test that fields documented as cache; assert core has no `create_solver_run` import (AST).
- [ ] **Step 7:** ruff + mypy + full gate + reconstruction narrow.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/unit/asteroid_lab/test_solver_run_fields_are_cache.py tests/unit/asteroid_lab/test_artifact_replay_loader_iterator.py -v
python -m pytest tests/unit/asteroid_lab/replay/ tests/integration/web/test_asteroid_miner_layout_solver.py -v
python -m mypy django_apps config src
```

## Risks

- `invariant:` replay truncation tracked from last-frame metrics, not top-level persist — preserve when reading JSONL.
- `invariant:` DB rows ≠ algorithm input — fallback read is viewer-only.
- `uncertain:` interaction with replay compose-defer (13C2-lite) — store pre-compose frames in artifact; Django compose stays viewer-only.
- Migration on existing rows — nullable columns, no destructive change.

## Done criteria

- Artifact-first replay works with DB fallback; new columns added; fields documented as cache; gates green.
