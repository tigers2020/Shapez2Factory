# PR-CLI-1 — `shapez2_factory` Scaffold + Manifest Writer Skeleton

**Type:** implementation change (new pure-python package)
**Depends on:** PR-CLI-0
**Enables:** PR-CLI-2a
**Branch (suggested):** `feat/asteroid-cli-first-scaffold`

---

## Goal

Stand up the `src/shapez2_factory/asteroid_lab` package structure, ports, artifact manifest DTO,
and atomic artifact writer skeleton — all pure Python, no algorithm move yet. Lock BA-1 gate.

## Behavior contract

- New package importable as `shapez2_factory.application.asteroid_lab...` with **zero** Django imports.
- `ArtifactManifest` DTO round-trips to/from `manifest.json`.
- `AtomicArtifactWriter` implements BA-5 protocol (temp dir → hash → manifest last → rename).
- Ports defined (Protocol) but not yet wired to real algorithms.

## Non-goals

- No reconstruction/layers move (that is 2a+).
- No Django changes.
- No real `run_stack` execution (use a stub use case returning empty result).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Create | `src/shapez2_factory/asteroid_lab/__init__.py` | namespace |
| Create | `src/shapez2_factory/domain/asteroid_lab/__init__.py` | domain ns |
| Create | `src/shapez2_factory/application/asteroid_lab/__init__.py` | application ns |
| Create | `src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py` | `GameDataRulesPort` Protocol |
| Create | `src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py` | `CopyDecodePort` Protocol |
| Create | `src/shapez2_factory/application/asteroid_lab/run_stack.py` | `RunStackUseCase` stub |
| Create | `src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py` | `ArtifactManifest` DTO + (de)serialize |
| Create | `src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py` | `AtomicArtifactWriter` (BA-5) |
| Create | `src/shapez2_factory/adapters/asteroid_lab/run_status.py` | lifecycle `StrEnum` |
| Create | `src/shapez2_factory/bootstrap/asteroid_lab_wiring.py` | default assembly (no Django) |
| Modify | [`pyproject.toml`](../../../../pyproject.toml) | ensure `packages.find where=["src"]` ships `shapez2_factory` (already set) — add note |
| Create | `tests/unit/shapez2_factory/test_artifact_atomic_write.py` | BA-5 round-trip |
| Create | `tests/unit/shapez2_factory/test_artifact_writer_collision.py` | writer-level collision reject |
| Create | `tests/unit/shapez2_factory/test_manifest_dto.py` | manifest (de)serialize |
| Modify | `tests/unit/architecture/test_shapez2_factory_core_purity.py` | now scans real modules |

---

## Key contracts

```python
# adapters/asteroid_lab/run_status.py
from enum import StrEnum
class RunLifecycleStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    ARTIFACT_WRITING = "artifact_writing"
    ARTIFACT_WRITTEN = "artifact_written"
    INDEXED = "indexed"          # DB/SolverRun only — never written into manifest.json
    SUCCEEDED = "succeeded"      # DB/SolverRun only
    FAILED = "failed"            # DB/SolverRun only
```

**Lifecycle authority (normative):** the writer sets `manifest.lifecycle_status = ARTIFACT_WRITTEN` at
finalize and that value is **immutable** afterward. `INDEXED`/`SUCCEEDED`/`FAILED` belong to the DB index
(PR-CLI-4/5) and must **never** cause a rewrite of `manifest.json`.

```python
# adapters/asteroid_lab/artifact_writer.py  (BA-5 protocol)
class AtomicArtifactWriter:
    def __init__(self, artifact_root: Path, run_key: str, *, replace_existing: bool = False) -> None: ...
    def open_staging(self) -> Path: ...          # var/runs/.tmp/<run_key>
    def write_output(self, relpath: str, data: bytes) -> None: ...
    def finalize(self, manifest: ArtifactManifest) -> Path:
        # 0) collision policy: if final dir exists and not replace_existing → raise ArtifactExistsError
        # 1) hash each written PAYLOAD file → manifest.content_hashes  (EXCLUDES manifest.json itself)
        # 2) set manifest.lifecycle_status = ARTIFACT_WRITTEN (immutable from here)
        # 3) write manifest.json LAST
        # 4) if replace_existing: delete final dir (under lock) — Windows rename fails on existing target
        # 5) os.replace(staging, final)  (atomic on same filesystem)
        ...
```

**`content_hashes` excludes `manifest.json`** — manifest is written last and cannot hash itself. It covers
only payload files written before finalization. Any manifest-integrity digest is computed externally by the
validator/ingest (not stored in `content_hashes`).

### Writer-level collision policy (architect-required, 2026-05-30)

The CLI `--replace-existing` flag is handled in PR-CLI-3a, but the **writer's default behavior** must be
locked here so no consumer can accidentally overwrite a finalized run:

```text
existing final dir exists + replace_existing=False → ArtifactExistsError (fail closed)
existing final dir exists + replace_existing=True  → delete final dir, then atomic rename
Windows: directory os.replace fails if target exists → must delete-then-rename under replace_existing
```

### Staging collision guard (architect-required, 2026-05-30)

Stale or concurrent staging dirs must not be silently reused:

```text
var/runs/.tmp/<run_key> already exists:
  default = reject as STAGING_ALREADY_EXISTS (fail closed)
  replace_existing=True → remove stale staging ONLY after acquiring the run lock
```

This prevents two concurrent runs (or a crashed prior run's leftover staging) from corrupting each other.
Test: `test_artifact_writer_rejects_existing_staging`.

```python
# application/asteroid_lab/ports/game_data_rules.py
from typing import Protocol
class GameDataRulesPort(Protocol):
    def exterior_shape_capacity(self, *, speed_tier: int) -> "ExteriorCapacityRow": ...
```

---

## Tasks

- [ ] **Step 1 (TDD):** `test_manifest_dto.py` — write failing round-trip test; implement `ArtifactManifest`.
- [ ] **Step 2 (TDD):** `test_artifact_atomic_write.py` — assert no final dir until `finalize`; manifest written last; hashes match; staging removed.
- [ ] **Step 3 (TDD):** `test_artifact_writer_rejects_existing_dir` — finalize onto existing final dir with `replace_existing=False` raises `ArtifactExistsError`; `True` replaces atomically. Add `test_artifact_writer_rejects_existing_staging` — existing `.tmp/<run_key>` rejected as `STAGING_ALREADY_EXISTS` unless `replace_existing`. Add `test_content_hashes_excludes_manifest`.
- [ ] **Step 4:** Define ports + stub `RunStackUseCase` (returns empty `StackRunResult`-shaped DTO; real impl in 3b).
- [ ] **Step 5:** Update purity gate to scan populated package; confirm green.
- [ ] **Step 6:** `ruff` + `mypy src`.

## Tests / verification

```powershell
python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/test_shapez2_factory_core_purity.py -v
python -m ruff check src/shapez2_factory tests/unit/shapez2_factory
python -m mypy src
```

## Risks

- `assumption:` `os.replace` atomic dir rename works on same volume; ensure `var/runs/.tmp` shares filesystem with `var/runs`.
- Windows: directory rename fails if target exists → on `replace_existing_run` delete target first inside lock.

## Done criteria

- Pure package imports clean; BA-1 gate green on real modules; atomic write + manifest tests pass.
