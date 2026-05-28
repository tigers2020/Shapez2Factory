# Asteroid Lab ↔ game_data DB Integration Implementation Plan

> **pytest output:** [`AGENTS.md`](../../../AGENTS.md) · [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Deprecated command:** `/write-plan` → use this skill instead.

**Goal:** Wire normalized `game_data` ORM into Asteroid Lab via revision-pinned immutable snapshot (no ORM on solver hot path, no `raw_json` fallback, import matrix preserved).

**Architecture:** `game_data` selectors/builder → `web` assembler → `asteroid_lab` DTOs + adapter → solver entry metadata (v0, not algorithm input).

**Tech Stack:** Python 3.12, Django 5, pytest-django, frozen dataclasses, `coord_transform.py`.

**Worktree (recommended):** `f:\Python_Projects\shapez2Factory\.worktrees\asteroid-lab-game-data` on branch `feature/asteroid-lab-game-data-integration`.

---

## Micro-task rules (2–5 minutes each)

| Rule | Meaning |
|------|---------|
| **One checkbox = one action** | Write one test, run one command, edit one file hunk, or one commit. |
| **~2 min** | Empty file, import stub, run single pytest node, `ruff` one path. |
| **~3–5 min** | One function + matching test, one dataclass group, one selector query. |
| **Red-green** | Test task immediately followed by impl task + verify task. |
| **Commit cadence** | Every 3–6 micro-tasks when green (see **Commit bundles**). |

**Standard verify command:**

```powershell
cd f:\Python_Projects\shapez2Factory\.worktrees\asteroid-lab-game-data
python -m pytest <path>::<test_name> --tb=short
python -m ruff check <paths>
```

---

## Progress dashboard (2026-05-22)

| Status | Scope | Notes |
|--------|--------|-------|
| **Done (master WIP, uncommitted)** | Phase 0 docs, Phase 1 contracts, Phase 2 selectors/builder | Cherry-pick or copy into worktree before T040+ |
| **Verify** | `8 passed` — contracts + selector + builder tests (~130s) | Includes `imported_game_data_batch` fixture |
| **Not started** | Phase 3 web assembler, adapter, solver wire, Phase 4–5 | T070+ |

**Before coding in worktree:** `git cherry-pick` or copy WIP from `master` → `feature/asteroid-lab-game-data-integration`, then re-run T039 verify.

---

## Micro-task index (quick jump)

| Phase | IDs | ~Tasks | ~Wall time |
|-------|-----|--------|------------|
| 0 Spec / ADR | T001–T015 | 15 | 45–75 min |
| 1 Consumer DTOs | T016–T039 | 24 | 80–120 min |
| 2 game_data ORM | T040–T059 | 20 | 70–100 min |
| 3 Web + adapter + wire | T060–T079 | 20 | 80–120 min |
| 4 Determinism P0 exit | T080–T089 | 10 | 35–50 min |
| 5 Runbook + docs | T090–T095 | 6 | 20–30 min |
| Gate | T096–T099 | 4 | 15–25 min |

**Total:** 99 micro-tasks · **~6–9 h** agent time (excl. full-suite CI).

---

## Phase 0 — ADR + domain specs (T001–T015)

### T001–T005: ADR-004

- [x] **T001** Create `docs/adr/ADR-004-game-data-snapshot-boundary.md` with title + Status: Accepted *(master WIP)*
- [x] **T002** Paste Context + Decision bullets (import matrix, web assembler, `SnapshotMeta`) *(master WIP)*
- [x] **T003** Add Consequences + v0 single-DB / no replica *(master WIP)*
- [ ] **T004** Read ADR aloud vs `test_django_app_import_boundaries.py` — no contradiction · **2 min**
- [ ] **T005** Commit ADR only: `git add docs/adr/ADR-004-game-data-snapshot-boundary.md` · `docs(adr): game_data snapshot boundary` · **2 min**

### T006–T010: `asteroid_game_data_snapshot.md`

- [x] **T006** Create `docs/domain/asteroid_game_data_snapshot.md` *(master WIP)*
- [x] **T007** Document sort keys table: buildings, footprint, connectors, transport *(master WIP)*
- [x] **T008** Document `SnapshotMeta` fields + fail-fast policy *(master WIP)*
- [ ] **T009** Cross-link ADR-004 + `django.md` import row · **3 min**
- [ ] **T010** Commit: `docs(domain): game_data snapshot ordering and meta` · **2 min**

### T011–T015: `asteroid_coord_transform_spec.md`

- [x] **T011** Create `docs/domain/asteroid_coord_transform_spec.md` *(master WIP)*
- [x] **T012** Document canonical E + CW `steps_from_canonical_e` *(master WIP)*
- [ ] **T013** Add golden table: offset `(1,0)` @ 0/90/180/270° · **5 min**
- [ ] **T014** State raw coords decode-only (link `asteroid-lab-invariants`) · **2 min**
- [ ] **T015** Commit: `docs(domain): coord transform spec for game_data adapter` · **2 min**

**Commit bundle A:** T005 + T010 + T015 (if not already committed).

---

## Phase 1 — Consumer contracts, no Django (T016–T039)

### T016–T022: Contract types

- [x] **T016** Create `django_apps/asteroid_lab/optimization/game_data_contracts.py` empty + module docstring *(master WIP)*
- [x] **T017** Add `SnapshotMeta` + `build_snapshot_meta()` + `SCHEMA_VERSION` / `RULE_VERSION` *(master WIP)*
- [x] **T018** Add `BuildingFootprintCell`, `BuildingConnectorSnapshot`, `BuildingSnapshot` *(master WIP)*
- [x] **T019** Add `TransportRegistryEntry`, `AsteroidGameDataSnapshot` *(master WIP)*
- [ ] **T020** `ruff check django_apps/asteroid_lab/optimization/game_data_contracts.py` · **2 min**
- [ ] **T021** Confirm **no** `django` import in contracts module · **2 min**
- [ ] **T022** Commit: `feat(asteroid_lab): game_data consumer snapshot contracts` · **2 min**

### T023–T028: Validation

- [x] **T023** Create `game_data_contract_validation.py` with `_sort_footprint` *(master WIP)*
- [x] **T024** Add `validate_building_snapshot()` returning sorted copy *(master WIP)*
- [ ] **T025** Add `TypeError` if `footprint_cells` is not `tuple` · **3 min**
- [ ] **T026** `ruff check` validation module · **2 min**
- [ ] **T027** Commit: `feat(asteroid_lab): validate building snapshot tuple order` · **2 min**

### T029–T034: Contract tests

- [x] **T029** Create `tests/unit/asteroid_lab/test_game_data_contracts.py` *(master WIP)*
- [x] **T030** Test footprint sort stable regardless of input order *(master WIP)*
- [x] **T031** Test `build_snapshot_meta` hashable *(master WIP)*
- [x] **T032** Test rejects list footprint · **3 min** *(add if missing)*
- [ ] **T033** Run: `pytest tests/unit/asteroid_lab/test_game_data_contracts.py` → PASS · **2 min**
- [ ] **T034** Commit: `test(asteroid_lab): game_data contract ordering` · **2 min**

### T035–T039: Content hash

- [x] **T035** Create `game_data_snapshot_hash.py` with `_canonical_payload` *(master WIP)*
- [x] **T036** Implement `snapshot_content_hash()` (no `asdict`) *(master WIP)*
- [ ] **T037** Add test `test_content_hash_stable_across_building_order` · **5 min**
- [ ] **T038** Run hash test → PASS · **2 min**
- [ ] **T039** Commit: `feat(asteroid_lab): deterministic snapshot content_hash` · **2 min**

**Commit bundle B:** T022 + T027 + T034 + T039.

**Phase 1 gate:** `pytest tests/unit/asteroid_lab/test_game_data_contracts.py`

---

## Phase 2 — game_data selectors + builder (T040–T059)

### T040–T044: Package + import batch

- [x] **T040** Create `django_apps/game_data/selectors/__init__.py` *(master WIP)*
- [x] **T041** Create `selectors/import_batch.py` with `GAME_DATA_READ_ALIAS` *(master WIP)*
- [x] **T042** Implement `pin_latest_import_batch()` · raise if None · **5 min** *(verify)*
- [x] **T043** Test `test_pin_import_batch_returns_manifest_self_hash` *(master WIP)*
- [ ] **T044** Run: `pytest tests/unit/game_data/test_snapshot_selectors.py::test_pin_import_batch_returns_manifest_self_hash` · **3 min**

### T045–T050: Split building queries

- [x] **T045** Create `selectors/buildings.py` + `BuildingRowsBundle` dataclass *(master WIP)*
- [x] **T046** Query variants `values_list` + `order_by("internal_name", "canonical_id")` *(master WIP)*
- [x] **T047** Query footprints separate + `order_by(building_variant_id, order_index)` *(master WIP)*
- [x] **T048** Query connectors separate + ordered fields *(master WIP)*
- [x] **T049** Test `test_building_rows_split_queries` ≤3 queries *(master WIP)*
- [ ] **T050** Run selector tests → PASS · **3 min** (slow: DB import fixture)

### T051–T055: Transport selector

- [ ] **T051** Create `selectors/transport_registry.py` ordered `values_list` · **5 min**
- [ ] **T052** Add test `test_transport_registry_ordered_by_kind` · **3 min**
- [ ] **T053** Export from `selectors/__init__.py` · **2 min**
- [ ] **T054** Run transport test → PASS · **2 min**
- [ ] **T055** Commit: `feat(game_data): snapshot selectors` · **2 min**

### T056–T059: Builder + errors

- [x] **T056** Create `snapshots/errors.py` — `SnapshotBuildErrorCode(StrEnum)` *(master WIP)*
- [x] **T057** Create `snapshots/rows.py` — row tuple types *(master WIP)*
- [x] **T058** Create `snapshots/builder.py` — `build_game_data_row_bundle()` *(master WIP)*
- [x] **T059** Tests: determinism + orphan footprint fail-fast *(master WIP)*
- [ ] **T059b** Run: `pytest tests/unit/game_data/test_snapshot_builder.py` → PASS · **3 min**
- [ ] **T059c** `ruff check django_apps/game_data/selectors django_apps/game_data/snapshots` · **2 min**
- [ ] **T059d** Commit: `feat(game_data): snapshot row builder` · **2 min**

**Phase 2 gate:** `pytest tests/unit/game_data/test_snapshot_selectors.py tests/unit/game_data/test_snapshot_builder.py`

---

## Phase 3 — Web assembler + adapter + solver wire (T060–T079)

### T060–T066: Web assembler

- [ ] **T060** Create `django_apps/web/services/asteroid_game_data_snapshot.py` · **2 min**
- [ ] **T061** Add failing test `test_assemble_snapshot_matches_pinned_revision` in `tests/unit/web/test_asteroid_game_data_snapshot.py` · **5 min**
- [ ] **T062** Run test → FAIL (ImportError) · **2 min**
- [ ] **T063** Implement `build_asteroid_game_data_snapshot()` — call builder, map rows → DTOs, `validate_building_snapshot`, `snapshot_content_hash` · **5 min**
- [ ] **T064** Sort buildings by `(internal_name, canonical_id)` before hash · **3 min**
- [ ] **T065** Run web test → PASS · **3 min**
- [ ] **T066** Commit: `feat(web): assemble AsteroidGameDataSnapshot` · **2 min**

### T067–T072: Transport adapter

- [ ] **T067** Create `django_apps/asteroid_lab/adapters/game_data_snapshot_adapter.py` · **2 min**
- [ ] **T068** Add failing tests — known `io_channel_type` → `TransportKind` table · **5 min**
- [ ] **T069** Add test — unknown channel raises `ValueError` · **3 min**
- [ ] **T070** Implement `map_io_channel_to_transport_kind()` explicit dict (no default NONE) · **5 min**
- [ ] **T071** Calibrate strings from DB: `pytest ... -k transport --pdb` on one connector row · **5 min**
- [ ] **T072** Commit: `feat(asteroid_lab): game_data transport adapter` · **2 min**

### T073–T079: Solver entry + HTTP

- [ ] **T073** Add optional `game_data_snapshot: AsteroidGameDataSnapshot | None` to `run_solver_runtime_for_project` · **3 min**
- [ ] **T074** Persist `game_data_snapshot_meta` in `SolverRun.config_json` only (not algorithm input) · **5 min**
- [ ] **T075** Wire `asteroid_miner_layout_project_run_solver` to `build_asteroid_game_data_snapshot()` · **5 min**
- [ ] **T076** Create `tests/integration/web/test_solver_with_game_data_snapshot.py` smoke · **5 min**
- [ ] **T077** Run integration test → PASS · **5 min**
- [ ] **T078** `ruff check` web + adapter + solver_runtime_entry · **2 min**
- [ ] **T079** Commit: `feat: wire game_data snapshot meta into solver runtime entry` · **2 min**

**Phase 3 gate:**

```powershell
python -m pytest tests/unit/web/test_asteroid_game_data_snapshot.py tests/unit/asteroid_lab/test_game_data_snapshot_adapter.py tests/integration/web/test_solver_with_game_data_snapshot.py
```

---

## Phase 4 — P0 determinism exit (T080–T089)

- [ ] **T080** Create `test_game_data_coord_transform_golden.py` with parametrize 0/90/180/270 · **5 min**
- [ ] **T081** Import expected vectors from `docs/domain/asteroid_coord_transform_spec.md` · **3 min**
- [ ] **T082** Run golden tests → PASS · **2 min**
- [ ] **T083** Commit: `test(asteroid_lab): coord transform golden vectors` · **2 min**
- [ ] **T084** Create `test_game_data_snapshot_determinism.py` · **3 min**
- [ ] **T085** Fixture: insert buildings/footprints in permuted order · **5 min**
- [ ] **T086** Assert `snapshot_content_hash` equal across permutations · **3 min**
- [ ] **T087** Run determinism test → PASS · **3 min**
- [ ] **T088** Commit: `test: snapshot determinism vs insert order` · **2 min**
- [ ] **T089** Re-run Phase 1–3 gate tests · **5 min**

---

## Phase 5 — Runbook + doc sync (T090–T095)

- [ ] **T090** Create `docs/runbooks/game_data_snapshot_deploy.md` with 4-step sequence · **5 min**
- [ ] **T091** Link `import_game_data --verify` + pytest paths · **3 min**
- [ ] **T092** Add § future PatternLibrary / expand-backfill · **3 min**
- [ ] **T093** Edit `documents/Algorithm/asteroid_lab_00_overview.md` — § GameData snapshot + ADR link · **5 min**
- [ ] **T094** Commit: `docs: game_data snapshot deploy runbook` · **2 min**
- [ ] **T095** Copy plan + docs into worktree if edited on master only · **2 min**

---

## PR gate (T096–T099)

- [ ] **T096** `pytest` narrow bundle (see command below) · **5–15 min**
- [ ] **T097** `ruff check` touched paths · **3 min**
- [ ] **T098** `mypy django_apps/game_data django_apps/asteroid_lab django_apps/web` · **5 min**
- [ ] **T099** `black --check` touched paths · **3 min**

```powershell
python -m pytest `
  tests/unit/game_data/test_snapshot_selectors.py `
  tests/unit/game_data/test_snapshot_builder.py `
  tests/unit/asteroid_lab/test_game_data_contracts.py `
  tests/unit/asteroid_lab/test_game_data_snapshot_adapter.py `
  tests/unit/asteroid_lab/test_game_data_coord_transform_golden.py `
  tests/unit/asteroid_lab/test_game_data_snapshot_determinism.py `
  tests/unit/web/test_asteroid_game_data_snapshot.py `
  tests/integration/web/test_solver_with_game_data_snapshot.py `
 
```

---

## Phase 6 — Deferred (separate plan)

Do **not** implement here. Follow-up: `docs/superpowers/plans/2026-XX-XX-asteroid-pattern-library-from-game-data.md`

- PatternLibrary compile from `BuildingSnapshot`
- CandidateGenerator build-time geometry
- Miner variant allowlist from `game_data`

---

## Appendix A — Code reference (large blocks)

Use when a micro-task says “implement per appendix”.

### A.1 Consumer contracts (T017–T019)

See original `game_data_contracts.py` in master WIP or:

```python
# django_apps/asteroid_lab/optimization/game_data_contracts.py
SCHEMA_VERSION = "game_data_snapshot_v1"
RULE_VERSION = "asteroid_v0"

@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    schema_version: str
    data_revision: str
    db_alias: str
    built_at_utc: str
    content_hash: str
    game_version: str
    rule_version: str
# ... BuildingFootprintCell, BuildingSnapshot, AsteroidGameDataSnapshot
```

### A.2 `pin_latest_import_batch` (T042)

```python
def pin_latest_import_batch(*, db_alias: str = "default") -> ImportBatch:
    batch = (
        ImportBatch.objects.using(db_alias)
        .order_by("-imported_at", "-id")
        .first()
    )
    if batch is None:
        raise SnapshotBuildError(SnapshotBuildErrorCode.NO_IMPORT_BATCH, ...)
    return batch
```

### A.3 Web assembler sketch (T063)

```python
def build_asteroid_game_data_snapshot(*, db_alias: str = "default") -> AsteroidGameDataSnapshot:
    batch = pin_latest_import_batch(db_alias=db_alias)
    bundle = build_game_data_row_bundle(batch.pk, db_alias=db_alias)
    buildings = tuple(_building_dto(b) for b in bundle.iter_buildings_sorted())
    transport = tuple(_transport_dto(r) for r in bundle.transport_rows)
    meta = build_snapshot_meta(
        data_revision=batch.manifest_self_hash,
        db_alias=db_alias,
        built_at_utc=datetime.now(tz=UTC).strftime(...),
        content_hash="",  # filled after snap assembled
        game_version=batch.game_version,
    )
    snap = AsteroidGameDataSnapshot(meta=meta, buildings=buildings, transport_registry=transport)
    return replace(snap, meta=replace(snap.meta, content_hash=snapshot_content_hash(snap)))
```

### A.4 Solver config_json meta (T074)

```python
GAME_DATA_SNAPSHOT_META_KEY = "game_data_snapshot_meta"

def _snapshot_meta_for_config(snap: AsteroidGameDataSnapshot) -> dict[str, str]:
    m = snap.meta
    return {
        "schema_version": m.schema_version,
        "data_revision": m.data_revision,
        "content_hash": m.content_hash,
    }
```

---

## Self-review (spec → micro-task)

| P0 review item | Micro-tasks |
|----------------|-------------|
| Ordered tuples | T017–T025, T064 |
| SnapshotMeta + hash | T017, T035–T038, T063 |
| Single DB alias | T041, ADR T003 |
| Split queries | T045–T049 |
| Fail-fast / no raw_json | T059, domain T008 |
| Coord spec | T011–T014, T080–T082 |
| Web boundary | T060–T066, ADR |
| Transport mapping | T067–T071 |
| Solver/export revision | T073–T074 (meta only v0) |
| Tests matrix | T029–T038, T043–T059, T080–T087 |

---

## Execution handoff

**Plan:** `docs/superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md`

1. **Subagent-driven** — one subagent per commit bundle (A/B/C…) or per 5 micro-tasks  
2. **Inline** — executing-plans from **T044** (first incomplete verify) or **T060** (greenfield Phase 3)

**Suggested resume point:** **T044** if WIP cherry-picked; **T060** if starting Phase 3 only.

---

## Caveman 6 sections

## Summary
- **Classification:** documentation change — re-split plan into **99 × 2–5 min** micro-tasks.
- `/write-plan` deprecated → **writing-plans** skill.
- **T001–T059** mostly master WIP complete; **T060+** not started.

## Files
- `docs/superpowers/plans/2026-05-21-asteroid-lab-game-data-integration.md` — this document updated

## Contracts
- Micro-task rules + progress dashboard + appendix code references
- No changes (implementation contract unchanged)

## Tests
- master WIP: `8 passed` (contracts + selectors + builder) · ~130s

## Risks
- WIP on `master` ≠ worktree — cherry-pick before T044/T060
- `T071` needs real `io_channel_type` strings from imported DB

## Next
- Cherry-pick WIP → worktree → resume **T044** or **subagent from T060**
