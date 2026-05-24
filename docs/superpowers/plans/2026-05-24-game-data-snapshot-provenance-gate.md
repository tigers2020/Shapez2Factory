# Game Data Snapshot Provenance Gate (Track A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every RTTP `SolverRun` carries a complete, validated `GameDataSnapshotProvenance` record so runs are auditable and reproducible by `(import_batch_id, snapshot_schema_version, content_hash)` without making snapshot body algorithm input.

**Architecture:** Frozen provenance DTO in `asteroid_lab/contracts/`; **single construction site** in `web/services/asteroid_game_data_snapshot.py` (returns snapshot + provenance); `solver_runtime_entry` is the only persistence writer into `SolverRun.config_json`; fail-closed persist gate; P1 policy (RTTP off still builds snapshot, no `SolverRun`).

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, `StrEnum`, pytest-django.

**Approved contract (§1):** Principal Solver review 2026-05-24 — 8 required fields, INV-PRV-01~06, unknown keys rejected in config parser, `content_hash` = solver subset only, P1 for RTTP off.

**Worktree (recommended):** `f:\Python_Projects\shapez2Factory\.worktrees\game-data-provenance-gate` on branch `feature/game-data-snapshot-provenance-gate`.

**Non-goals (this plan):** B/C/D tracks; snapshot body as algorithm input; `SolverRun` DB columns for provenance; expanding `AsteroidGameDataSnapshot` fields.

**Execution amendments (2026-05-24, approved):**

| Item | Rule |
|------|------|
| Parser | Reject `import_batch_id <= 0`, `content_hash` not 64 hex chars, `snapshot_schema_version` / `rule_version` mismatch vs constants; do **not** force `data_revision` to 64 hex |
| Builder | `pin_latest_import_batch()` once → `_build_asteroid_game_data_snapshot_for_batch(batch, db_alias)` → `provenance_from_snapshot(..., batch.pk)`; `build_asteroid_game_data_snapshot()` wraps `.snapshot` only |
| Runtime gate | **Before** `create_solver_run`: snapshot+provenance present, hash match, merge+`parse_provenance_config` self-check; **After** create: DB readback parse; then pipeline |
| P1 HTTP | `game_data_snapshot_ready=true` + slim diagnostic: `reproducibility_key` fields + `content_hash` (not full 8-field object unless needed) |
| Callers | Runtime paths use `build_asteroid_game_data_snapshot_with_provenance()` only |
| RTTP tests | New RTTP runtime tests **MUST** use `run_solver_runtime_with_pinned_game_data` (`tests/unit/asteroid_lab/_runtime_game_data.py`) **or** pass both `game_data_snapshot` and `game_data_provenance` explicitly |

---

## Implementation status (2026-05-24)

| Task | Status |
|------|--------|
| Task 1 — Provenance contract module | [x] |
| Task 2 — Single builder (web service) | [x] |
| Task 3 — Config key + entry persist gate | [x] |
| Task 4 — HTTP + CLI callers | [x] |
| Task 5 — Drift + architecture guard tests | [x] |
| Task 6 — Documentation (ADR + domain) | [x] |
| Task 7A — Narrow pytest (42 + 10 + 4) | [x] |
| Task 7B — Ruff touched paths | [x] |
| Task 7C — Full repository gate | [ ] |

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py` | **CREATE** — `GameDataSnapshotProvenance`, parse/validate, `reproducibility_key()`, config dict wire format |
| `django_apps/web/services/asteroid_game_data_snapshot.py` | **MODIFY** — `GameDataSnapshotBuildResult`; sole builder of snapshot + provenance |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | **MODIFY** — accept provenance; persist gate; `PROVENANCE_INCOMPLETE` |
| `django_apps/asteroid_lab/services/solver_run_config_keys.py` | **MODIFY** — document wire key; optional constant for diagnostic key |
| `django_apps/web/views/public_pages.py` | **MODIFY** — use build result; P1 stub diagnostics |
| `django_apps/asteroid_lab/management/commands/run_solver.py` | **MODIFY** — use build result |
| `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py` | **CREATE** — contract + parser tests |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | **MODIFY** — provenance gate + RTTP requires provenance |
| `tests/integration/web/test_asteroid_run_solver.py` | **MODIFY** — readback + P1 stub |
| `docs/adr/ADR-004-game-data-snapshot-boundary.md` | **MODIFY** — provenance required on runs; body not algorithm input |
| `docs/domain/asteroid_game_data_snapshot.md` | **MODIFY** — provenance section + hash scope + `built_at_utc` rule |

---

## Wire format

`SolverRun.config_json["game_data_snapshot_provenance"]` — object with **exactly** these string keys (all required):

```json
{
  "snapshot_schema_version": "game_data_snapshot_v1",
  "rule_version": "asteroid_v0",
  "data_revision": "<manifest_self_hash>",
  "import_batch_id": "42",
  "content_hash": "<64-char hex>",
  "game_version": "<game_version>",
  "db_alias": "default",
  "built_at_utc": "2026-05-24T12:00:00Z"
}
```

- `import_batch_id` stored as **decimal string** in JSON (parse to `int` on read; avoids JSON number drift in tests).
- **Unknown keys inside this object → reject** (`ProvenanceParseError`).
- Legacy key `game_data_snapshot_meta` (3-field dict): remove writes; optional one-release read fallback **not** in scope (YAGNI — grep tests only).

---

## Task 1: Provenance contract module

**Files:**
- Create: `django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py`
- Test: `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py`

- [x] **Step 1: Write failing tests for provenance construction and parser**

```python
# tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py
from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    SCHEMA_VERSION,
    RULE_VERSION,
    AsteroidGameDataSnapshot,
    BuildingSnapshot,
    build_snapshot_meta,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    ProvenanceParseError,
    provenance_from_snapshot,
    parse_provenance_config,
    provenance_to_config_dict,
)


def _minimal_snapshot(*, content_hash: str = "aa" * 32) -> AsteroidGameDataSnapshot:
    meta = build_snapshot_meta(
        data_revision="rev-hash-001",
        db_alias="default",
        built_at_utc="2026-05-24T00:00:00Z",
        content_hash=content_hash,
        game_version="9.9.9",
    )
    return AsteroidGameDataSnapshot(
        meta=meta,
        buildings=(
            BuildingSnapshot(
                canonical_id="bv:test",
                internal_name="test",
                footprint_cells=(),
                connectors=(),
            ),
        ),
        transport_registry=(),
    )


def test_provenance_from_snapshot_maps_all_fields() -> None:
    snap = _minimal_snapshot()
    prov = provenance_from_snapshot(snap, import_batch_id=99)
    assert prov.snapshot_schema_version == SCHEMA_VERSION
    assert prov.rule_version == RULE_VERSION
    assert prov.data_revision == "rev-hash-001"
    assert prov.import_batch_id == 99
    assert prov.content_hash == snap.meta.content_hash
    assert prov.game_version == "9.9.9"
    assert prov.db_alias == "default"
    assert prov.built_at_utc == "2026-05-24T00:00:00Z"


def test_reproducibility_key_excludes_built_at_utc() -> None:
    snap = _minimal_snapshot()
    a = provenance_from_snapshot(snap, import_batch_id=1)
    b = GameDataSnapshotProvenance(
        snapshot_schema_version=a.snapshot_schema_version,
        rule_version=a.rule_version,
        data_revision=a.data_revision,
        import_batch_id=a.import_batch_id,
        content_hash=a.content_hash,
        game_version=a.game_version,
        db_alias=a.db_alias,
        built_at_utc="2026-05-25T99:99:99Z",
    )
    assert a.reproducibility_key() == b.reproducibility_key()


def test_parse_provenance_rejects_unknown_keys() -> None:
    payload = provenance_to_config_dict(
        provenance_from_snapshot(_minimal_snapshot(), import_batch_id=1)
    )
    payload["extra_field"] = "nope"
    with pytest.raises(ProvenanceParseError):
        parse_provenance_config(payload)


def test_parse_provenance_rejects_missing_field() -> None:
    payload = provenance_to_config_dict(
        provenance_from_snapshot(_minimal_snapshot(), import_batch_id=1)
    )
    del payload["content_hash"]
    with pytest.raises(ProvenanceParseError):
        parse_provenance_config(payload)


def test_roundtrip_config_dict() -> None:
    prov = provenance_from_snapshot(_minimal_snapshot(), import_batch_id=7)
    again = parse_provenance_config(provenance_to_config_dict(prov))
    assert again == prov
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd f:\Python_Projects\shapez2Factory
python -m pytest tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py -v
```

Expected: FAIL — `ModuleNotFoundError` or import errors for `game_data_snapshot_provenance`.

- [ ] **Step 3: Implement provenance module**

```python
# django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py
"""Frozen provenance for game_data snapshot builds (metadata only — not algorithm input)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
)

_REQUIRED_KEYS = frozenset(
    {
        "snapshot_schema_version",
        "rule_version",
        "data_revision",
        "import_batch_id",
        "content_hash",
        "game_version",
        "db_alias",
        "built_at_utc",
    }
)


class ProvenanceParseErrorCode(StrEnum):
    UNKNOWN_KEY = "unknown_key"
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"


class ProvenanceParseError(ValueError):
    def __init__(self, code: ProvenanceParseErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class GameDataSnapshotProvenance:
    snapshot_schema_version: str
    rule_version: str
    data_revision: str
    import_batch_id: int
    content_hash: str
    game_version: str
    db_alias: str
    built_at_utc: str

    def reproducibility_key(self) -> tuple[int, str, str]:
        """Reproducibility key — built_at_utc MUST NOT participate."""
        return (
            self.import_batch_id,
            self.snapshot_schema_version,
            self.content_hash,
        )


def provenance_from_snapshot(
    snapshot: AsteroidGameDataSnapshot,
    *,
    import_batch_id: int,
) -> GameDataSnapshotProvenance:
    meta = snapshot.meta
    return GameDataSnapshotProvenance(
        snapshot_schema_version=meta.schema_version,
        rule_version=meta.rule_version,
        data_revision=meta.data_revision,
        import_batch_id=int(import_batch_id),
        content_hash=meta.content_hash,
        game_version=meta.game_version,
        db_alias=meta.db_alias,
        built_at_utc=meta.built_at_utc,
    )


def provenance_to_config_dict(provenance: GameDataSnapshotProvenance) -> dict[str, str]:
    return {
        "snapshot_schema_version": provenance.snapshot_schema_version,
        "rule_version": provenance.rule_version,
        "data_revision": provenance.data_revision,
        "import_batch_id": str(provenance.import_batch_id),
        "content_hash": provenance.content_hash,
        "game_version": provenance.game_version,
        "db_alias": provenance.db_alias,
        "built_at_utc": provenance.built_at_utc,
    }


def parse_provenance_config(payload: object) -> GameDataSnapshotProvenance:
    if not isinstance(payload, dict):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "provenance payload must be dict",
        )
    unknown = set(payload) - _REQUIRED_KEYS
    if unknown:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.UNKNOWN_KEY,
            f"unknown provenance keys: {sorted(unknown)}",
        )
    missing = _REQUIRED_KEYS - set(payload)
    if missing:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.MISSING_FIELD,
            f"missing provenance keys: {sorted(missing)}",
        )
    try:
        batch_id = int(str(payload["import_batch_id"]))
    except (TypeError, ValueError) as exc:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "import_batch_id must be int-like string",
        ) from exc
    return GameDataSnapshotProvenance(
        snapshot_schema_version=str(payload["snapshot_schema_version"]),
        rule_version=str(payload["rule_version"]),
        data_revision=str(payload["data_revision"]),
        import_batch_id=batch_id,
        content_hash=str(payload["content_hash"]),
        game_version=str(payload["game_version"]),
        db_alias=str(payload["db_alias"]),
        built_at_utc=str(payload["built_at_utc"]),
    )


__all__ = [
    "GameDataSnapshotProvenance",
    "ProvenanceParseError",
    "ProvenanceParseErrorCode",
    "parse_provenance_config",
    "provenance_from_snapshot",
    "provenance_to_config_dict",
]
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py -v
python -m ruff check django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py
git commit -m "feat(asteroid_lab): add GameDataSnapshotProvenance contract"
```

---

## Task 2: Single builder (web service)

**Files:**
- Modify: `django_apps/web/services/asteroid_game_data_snapshot.py`
- Modify: `tests/unit/web/test_asteroid_game_data_snapshot.py`

- [ ] **Step 1: Write failing test for build result provenance**

Add to `tests/unit/web/test_asteroid_game_data_snapshot.py`:

```python
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)


@pytest.mark.django_db
def test_build_with_provenance_sets_import_batch_id(imported_game_data_batch) -> None:
    del imported_game_data_batch  # fixture pins batch
    result = build_asteroid_game_data_snapshot_with_provenance(db_alias="default")
    assert result.provenance.import_batch_id > 0
    assert result.provenance.data_revision == result.snapshot.meta.data_revision
    assert result.provenance.content_hash == result.snapshot.meta.content_hash
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/web/test_asteroid_game_data_snapshot.py::test_build_with_provenance_sets_import_batch_id -v
```

- [ ] **Step 3: Implement `GameDataSnapshotBuildResult`**

In `django_apps/web/services/asteroid_game_data_snapshot.py`:

```python
from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    provenance_from_snapshot,
)


@dataclass(frozen=True, slots=True)
class GameDataSnapshotBuildResult:
    snapshot: AsteroidGameDataSnapshot
    provenance: GameDataSnapshotProvenance


def build_asteroid_game_data_snapshot_with_provenance(
    *, db_alias: str = "default"
) -> GameDataSnapshotBuildResult:
    batch = pin_latest_import_batch(db_alias=db_alias)
    snapshot = build_asteroid_game_data_snapshot(db_alias=db_alias)
    provenance = provenance_from_snapshot(snapshot, import_batch_id=int(batch.pk))
    return GameDataSnapshotBuildResult(snapshot=snapshot, provenance=provenance)
```

Refactor `build_asteroid_game_data_snapshot` to call `pin` + bundle logic once, or call `build_..._with_provenance(...).snapshot` to avoid double DB work (preferred: internal helper `_build_snapshot_for_batch(batch, db_alias)` used by both entry points).

- [ ] **Step 4: Run web snapshot tests**

```powershell
python -m pytest tests/unit/web/test_asteroid_game_data_snapshot.py tests/unit/asteroid_lab/test_game_data_snapshot_determinism.py -v
python -m ruff check django_apps/web/services/asteroid_game_data_snapshot.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add django_apps/web/services/asteroid_game_data_snapshot.py tests/unit/web/test_asteroid_game_data_snapshot.py
git commit -m "feat(web): build snapshot with GameDataSnapshotProvenance"
```

---

## Task 3: Config key + entry persist gate

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

- [ ] **Step 1: Add config key constant**

In `solver_run_config_keys.py`:

```python
SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY = "game_data_snapshot_provenance"
```

Deprecate comment on `SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY` — stop writing in Task 3.

- [ ] **Step 2: Write failing test — RTTP run persists full provenance**

Add to `test_solver_runtime_entry.py` (requires `imported_game_data_batch` fixture at module or test level):

```python
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    parse_provenance_config,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    provenance_from_snapshot,
)
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_persists_game_data_snapshot_provenance(imported_game_data_batch) -> None:
    del imported_game_data_batch
    build = build_asteroid_game_data_snapshot_with_provenance()
    proj = m.AsteroidProject.objects.create(name="Prov", slug="prov-gate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=build.provenance,
    )
    assert result.solver_run_id is not None
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    raw = run.config_json.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY)
    assert raw is not None
    parsed = parse_provenance_config(raw)
    assert parsed == build.provenance
```

- [ ] **Step 3: Write failing test — missing provenance fails closed**

```python
@pytest.mark.django_db
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_without_provenance_returns_provenance_incomplete(imported_game_data_batch) -> None:
    del imported_game_data_batch
    build = build_asteroid_game_data_snapshot_with_provenance()
    proj = m.AsteroidProject.objects.create(name="NoProv", slug="no-prov-gate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=None,
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE
    if result.solver_run_id is not None:
        run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
        assert run.config_json.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY) is None
```

- [ ] **Step 4: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py -k provenance -v
```

- [ ] **Step 5: Implement entry changes**

In `solver_runtime_entry.py`:

1. Add to `SolverRuntimeEntryErrorCode`:

```python
PROVENANCE_INCOMPLETE = "provenance_incomplete"
```

2. Replace `_snapshot_meta_for_config` usage with:

```python
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    provenance_to_config_dict,
    parse_provenance_config,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
)


def _merge_provenance_into_run_config(
    run_config: dict[str, Any],
    provenance: GameDataSnapshotProvenance,
) -> dict[str, Any]:
    out = dict(run_config)
    out[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY] = provenance_to_config_dict(
        provenance
    )
    return out


def _assert_run_config_has_valid_provenance(config: dict[str, Any]) -> GameDataSnapshotProvenance:
    raw = config.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY)
    if raw is None:
        raise ValueError("missing game_data_snapshot_provenance")
    return parse_provenance_config(raw)
```

3. Extend `run_solver_runtime_for_project` and `_run_rttp_solver_for_map_input` signatures:

```python
game_data_provenance: GameDataSnapshotProvenance | None = None,
```

4. At start of `_run_rttp_solver_for_map_input` (after decode, before `create_solver_run`):

```python
if game_data_snapshot is None or game_data_provenance is None:
    return SolverRuntimeEntryResult(
        ok=False,
        solver_run_id=None,
        ...
        error_code=SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE,
        message="RTTP run requires game_data snapshot and provenance.",
    )
# Optional strict: provenance content_hash matches snapshot.meta.content_hash
if game_data_provenance.content_hash != game_data_snapshot.meta.content_hash:
    return SolverRuntimeEntryResult(..., error_code=PROVENANCE_INCOMPLETE, message="...")
run_config = _merge_provenance_into_run_config(run_config, game_data_provenance)
```

5. Immediately after `create_solver_run` / `create_or_replace_solver_run`, **persist gate**:

```python
run_row = m.SolverRun.objects.get(pk=run_id)
try:
    _assert_run_config_has_valid_provenance(dict(run_row.config_json or {}))
except (ValueError, ProvenanceParseError):
    # fail-closed: mark run failed, do not return ok=True later
    ...
```

Simplest v0 gate: if assert fails, return `PROVENANCE_INCOMPLETE` **before** `run_rttp_pipeline` (no pipeline on bad config). That satisfies INV-PRV-04 without orphan runs.

6. Remove writes to `SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY`.

7. In `_persist_solver_run_outcome`, re-validate provenance still present (read config, parse); if missing, do not treat as success (set `validation_passed=False` in returned result if summary says ok — or assert in tests only). **v0:** re-parse in test readback is enough; optional defensive re-check in `_persist_solver_run_outcome`.

- [ ] **Step 6: Run entry provenance tests + ruff**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py -k provenance -v
python -m ruff check django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/services/solver_run_config_keys.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/services/solver_run_config_keys.py tests/unit/asteroid_lab/test_solver_runtime_entry.py
git commit -m "feat(asteroid_lab): fail-closed game_data provenance on RTTP SolverRun"
```

---

## Task 4: HTTP + CLI callers (single writer path)

**Files:**
- Modify: `django_apps/web/views/public_pages.py`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`
- Modify: `tests/integration/web/test_asteroid_run_solver.py`

- [ ] **Step 1: Write failing integration test — readback after POST**

Add to `tests/integration/web/test_asteroid_run_solver.py`:

```python
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    parse_provenance_config,
)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_post_persists_provenance_on_solver_run(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="ProvInt", slug="prov-int")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    run_id = data.get("solver_run_id")
    assert run_id is not None
    run = m.SolverRun.objects.get(pk=int(run_id))
    prov = parse_provenance_config(
        run.config_json[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY]
    )
    assert prov.import_batch_id > 0
    assert len(prov.content_hash) == 64
```

- [ ] **Step 2: Write failing test — P1 RTTP off returns `game_data_snapshot_ready`**

```python
@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_stub_still_reports_game_data_snapshot_ready(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="StubProv", slug="stub-prov")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data.get("game_data_snapshot_ready") is True
    assert data.get("error_code") == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert data.get("solver_run_id") is None
    repro = data.get("game_data_snapshot_provenance")
    assert isinstance(repro, dict)
    assert "content_hash" in repro
```

- [ ] **Step 3: Run integration tests — expect FAIL**

```powershell
python -m pytest tests/integration/web/test_asteroid_run_solver.py -k "provenance or stub_still" -v
```

- [ ] **Step 4: Update `public_pages.py`**

Replace:

```python
game_data_snapshot = build_asteroid_game_data_snapshot()
```

with:

```python
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    provenance_to_config_dict,
)

build = build_asteroid_game_data_snapshot_with_provenance()
```

Pass to entry:

```python
result = run_solver_runtime_for_project(
    int(project.pk),
    config=run_config,
    game_data_snapshot=build.snapshot,
    game_data_provenance=build.provenance,
)
```

After `entry_result_to_json_dict(result)`:

```python
if result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE:
    body["game_data_snapshot_ready"] = True
    body["game_data_snapshot_provenance"] = provenance_to_config_dict(build.provenance)
    return JsonResponse(body, status=200)
```

- [ ] **Step 5: Update `run_solver.py` management command** — same `build_asteroid_game_data_snapshot_with_provenance()` and pass `game_data_provenance=build.provenance`.

- [ ] **Step 6: Run integration + CLI smoke**

```powershell
python -m pytest tests/integration/web/test_asteroid_run_solver.py -v
python -m ruff check django_apps/web/views/public_pages.py django_apps/asteroid_lab/management/commands/run_solver.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add django_apps/web/views/public_pages.py django_apps/asteroid_lab/management/commands/run_solver.py tests/integration/web/test_asteroid_run_solver.py
git commit -m "feat(web): P1 snapshot build on RTTP stub; pass provenance to runtime"
```

---

## Task 5: Drift + architecture guard tests

**Files:**
- Modify: `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py`
- Modify: `tests/unit/architecture/test_django_app_import_boundaries.py` (only if new imports — likely none)

- [ ] **Step 1: Add drift test (same blueprint, provenance reflects pinned batch)**

```python
@pytest.mark.django_db
def test_provenance_data_revision_matches_pinned_import_batch(imported_game_data_batch) -> None:
    from django_apps.game_data.selectors.import_batch import pin_latest_import_batch
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    batch = pin_latest_import_batch(db_alias="default")
    build = build_asteroid_game_data_snapshot_with_provenance(db_alias="default")
    assert build.provenance.import_batch_id == int(batch.pk)
    assert build.provenance.data_revision == batch.manifest_self_hash
```

- [ ] **Step 2: Add test — optimization package does not import game_data**

Verify existing `tests/unit/asteroid_lab/test_import_boundaries.py` or architecture test still passes; if missing, add:

```python
def test_optimization_does_not_import_game_data() -> None:
    import importlib
    mod = importlib.import_module("django_apps.asteroid_lab.optimization.pipeline")
    src = open(mod.__file__, encoding="utf-8").read()
    assert "game_data" not in src
```

(Prefer existing architecture matrix test if it already covers this.)

- [ ] **Step 3: Run narrow asteroid_lab + architecture tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py tests/unit/architecture/test_django_app_import_boundaries.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py
git commit -m "test(asteroid_lab): provenance drift matches pinned import batch"
```

---

## Task 6: Documentation (ADR + domain)

**Files:**
- Modify: `docs/adr/ADR-004-game-data-snapshot-boundary.md`
- Modify: `docs/domain/asteroid_game_data_snapshot.md`

- [ ] **Step 1: ADR-004 — add subsection "Provenance gate (Track A)"**

Bullet points to add:

- Every RTTP `SolverRun` MUST include `game_data_snapshot_provenance` (8 fields).
- `content_hash` is **solver subset** hash, not `manifest_self_hash`.
- `built_at_utc` MUST NOT participate in `content_hash` or reproducibility key.
- Snapshot body remains **not** algorithm input until a future ADR.
- RTTP disabled: snapshot build still required (P1); no `SolverRun`.

- [ ] **Step 2: Domain doc — new section `## GameDataSnapshotProvenance`**

Document fields, wire key, unknown-key reject, reproducibility key tuple, writer ownership (web assembler only constructs; entry persists).

- [ ] **Step 3: Commit docs**

```bash
git add docs/adr/ADR-004-game-data-snapshot-boundary.md docs/domain/asteroid_game_data_snapshot.md
git commit -m "docs: game_data snapshot provenance gate (Track A)"
```

---

## Task 7: Phase gate (narrow + optional full)

- [ ] **Step 1: Narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/unit/web/test_asteroid_game_data_snapshot.py tests/integration/web/test_asteroid_run_solver.py -v
```

Expected: all PASS.

- [ ] **Step 2: Ruff on touched paths**

```powershell
python -m ruff check django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/services/asteroid_game_data_snapshot.py django_apps/web/views/public_pages.py
```

- [ ] **Step 3: Optional PR full gate** (before merge)

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
```

---

## Plan self-review (completed)

| Spec requirement | Task |
|------------------|------|
| Frozen `GameDataSnapshotProvenance` | Task 1 |
| 8 required fields | Task 1, 3 |
| Unknown key reject | Task 1 |
| `reproducibility_key` excludes `built_at_utc` | Task 1 |
| Single writer (web build result) | Task 2, 4 |
| Persist fail-closed before pipeline | Task 3 |
| No snapshot body as algorithm input | Docs Task 6; no optimization imports Task 5 |
| P1 RTTP off snapshot + diagnostic | Task 4 |
| Readback integration test | Task 4 |
| Drift / pinned batch | Task 5 |
| ADR + domain doc | Task 6 |

**Placeholder scan:** None.

**Type consistency:** `game_data_provenance` parameter name used consistently; config key `game_data_snapshot_provenance` throughout.

---

## Execution handoff

**Track A narrow implementation: CLOSED (2026-05-24).** PR: pending `feature/game-data-snapshot-provenance-gate`. Full gate (Task 7C) deferred to merge CI / explicit run.

**Validation record:** narrow pytest + ruff touched paths green; **full gate not run** (document in PR body).
