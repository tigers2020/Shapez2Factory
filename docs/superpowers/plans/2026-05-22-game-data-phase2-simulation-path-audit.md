# game_data Phase 2 — Simulation Nested Path Audit Implementation Plan

> **pytest output:** [`AGENTS.md`](../../../AGENTS.md) · [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove `simulation_systems.json` high-count nested paths are each `promoted`, `cross_ref`, or `ignore_audit` via coverage manifest + import-time audit + RED→GREEN parity tests — **no new domain models** unless explicitly classified `promoted`.

**Architecture:** Run `scripts/audit_simulation_nested_paths.py --normalized` → human-reviewed disposition rules in `coverage/simulation_paths.py` → `MANIFEST` built from static entries + rule-generated prefixes → `sync_definition_snapshot_coverage_audit` records `UnknownProperty` for `definition_snapshot` ignore paths → pytest gates every priority family.

**Tech Stack:** Python 3, Django `game_data`, pytest, TSV audit artifact under `documents/game_data_analysis/simulation_systems/`.

**Non-goals:** `game_data_dump.json` refresh; A≡B structural parity; `AsteroidGameDataSnapshot` / ADR-004 changes; new ORM tables for `ChainPositions` (classified **ignore_audit** below).

---

## Audit results (2026-05-22 run)

**Artifacts**

| File | Lines | Notes |
| ---- | ----- | ----- |
| `documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv` | 5356 | Full normalized aggregate (`# total_norm_paths=5786` in stderr) |
| `documents/game_data_analysis/simulation_systems/_nested_path_audit.stderr.txt` | 1 | Run metadata only |

**Top families (by `max_list_len`)**

| Family | Path count in TSV | Max list len | Channel |
| ------ | ----------------- | ------------ | ------- |
| `ChainPositions` | 3 | 129 | `definition_snapshot` delegate tree only |
| `TileBasedSystems` | 24 | 129 | `definition_snapshot` / mirrored in `simulation_parameters` delegates |
| `ConnectableSimulations` | 149 | 54 | Mostly `simulation_parameters` (6 connectable-profile rows) |
| `SimulationFactory` | 1650 | 9 | Both channels |
| `ISimulationSystem` | 613 | 129 | Delegate / listener capture |
| `k__BackingField` | 619 | 19 | Research/interlock/wiki dumps inside converter snapshots |
| `ExtractorPositions` | 3 | 58 | With `TileBasedSystems` |

**Planner-relevance decision (locked for this plan)**

| Path | Disposition | `reason_code` / note |
| ---- | ----------- | -------------------- |
| `simulation_systems.json:simulation_parameters.ConnectableSimulations` | **promoted** | `ConnectableSimulation` (existing) |
| `…ConnectableSimulations[].Connectors` | **promoted** | `SimulationConnector` |
| `…ConnectableSimulations[].Simulation._Lanes` | **promoted** | `SimulationLaneDefinition` + `SimulationLaneRuntimeState` (`state_value_text`) |
| `…ConnectableSimulations[].Simulation.InputLanes` | **cross_ref** | Same lane importer path as `_Lanes` |
| `…ConnectableSimulations[].ChunkBounds` / `TileBounds` | **promoted** | `SimulationChunkBounds` / `SimulationTileBounds` |
| `…ConnectableSimulations[].Building` | **cross_ref** | `BuildingVariant` via `internal_name` |
| `…ConnectableSimulations[].Junctions` / `JunctionsByPivot` / `TileConnectors` | **ignore_audit** | `RUNTIME_DELEGATE` — runtime junction graph |
| `…ConnectableSimulations[].Simulation.State` / `NextBundle` / `ProviderConductors` | **ignore_audit** | `RUNTIME_DELEGATE` |
| `definition_snapshot.*ChainPositions*` | **ignore_audit** | `RUNTIME_DELEGATE` — island sim runtime coords, not connectable import |
| `definition_snapshot.*TileBasedSystems*` | **ignore_audit** | `RUNTIME_DELEGATE` — duplicate channel; graph promoted via `simulation_parameters` |
| `definition_snapshot.*ExtractorPositions*` | **ignore_audit** | `RUNTIME_DELEGATE` |
| `definition_snapshot.*TileBasedSystems.*ConnectableSimulations` | **cross_ref** | Equivalence to `simulation_parameters.ConnectableSimulations` (audit only) |
| `definition_snapshot.ISimulationSystem.*` | **ignore_audit** | `RUNTIME_DELEGATE` (prefix) |
| `simulation_parameters.ISimulationSystem.*` | **ignore_audit** | `RUNTIME_DELEGATE` (prefix) |
| `*.SimulationFactory.*` | **ignore_audit** | `SIMULATION_FACTORY_STUB` (prefix) |
| `definition_snapshot.Interlock.*` | **ignore_audit** | `REFLECTION_METADATA` — scenario/wiki capture |
| `*k__BackingField*` | **ignore_audit** | `REFLECTION_METADATA` |
| `*.Assembly.*` / `DefinedTypes` / `ExportedTypes` | **ignore_audit** | `REFLECTION_METADATA` |
| `*.Listeners[]*` (under delegates) | **ignore_audit** | `RUNTIME_DELEGATE` |
| `$type` / `$unity` leaf keys during walk | **ignore_audit** | `RUNTIME_UNITY_METADATA` |

**Blocked today:** `django_apps/game_data/coverage/manifest.py` imports missing `disposition.py`, `simulation_paths.py`; `simulation_systems.py` imports missing `simulation_definition_snapshot_audit.py` → **Task 1 unblocks imports**.

---

## File map

| File | Responsibility |
| ---- | -------------- |
| `django_apps/game_data/coverage/disposition.py` | `Disposition` StrEnum |
| `django_apps/game_data/coverage/simulation_paths.py` | Prefix rules + `manifest_entries_from_rules()` + `classify_norm_path()` |
| `django_apps/game_data/coverage/manifest.py` | Static entries + `MANIFEST.update(rules)` |
| `django_apps/game_data/importers/simulation_definition_snapshot_audit.py` | Walk `definition_snapshot`; record ignore_audit UnknownProperty |
| `scripts/audit_simulation_nested_paths.py` | Add `--priority` filtered TSV |
| `documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv` | Human review subset (~150–250 rows) |
| `tests/unit/game_data/test_simulation_path_coverage.py` | RED→GREEN parity gates |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | Extend: rule keys + no duplicate prefixes |
| `docs/domain/game_data_coverage.md` | Phase 2 classifications + “domain-complete for simulation” gate |

---

### Task 1: Restore coverage package imports

**Files:**
- Create: `django_apps/game_data/coverage/disposition.py`
- Create: `django_apps/game_data/coverage/simulation_paths.py` (skeleton only)
- Modify: `django_apps/game_data/coverage/__init__.py` (export `Disposition`, `classify_norm_path` if needed)

- [ ] **Step 1: `disposition.py`**

```python
"""Coverage disposition enum (A1 manifest)."""

from __future__ import annotations

from enum import StrEnum


class Disposition(StrEnum):
    PROMOTED = "promoted"
    CROSS_REF = "cross_ref"
    IGNORE_AUDIT = "ignore_audit"
```

- [ ] **Step 2: `simulation_paths.py` skeleton**

```python
"""simulation_systems.json path classification rules (Phase 2)."""

from __future__ import annotations

from django_apps.game_data.coverage.disposition import Disposition


def manifest_entries_from_rules() -> dict[str, tuple[Disposition, str]]:
    return {}


def classify_norm_path(norm_path: str) -> tuple[Disposition, str] | None:
    return None
```

- [ ] **Step 3: Verify import**

Run: `python -c "from django_apps.game_data.coverage.manifest import MANIFEST; print('ok', len(MANIFEST))"`

Expected: `ok` + integer ≥ 11 (no `ModuleNotFoundError`)

- [ ] **Step 4: Commit**

```bash
git add django_apps/game_data/coverage/disposition.py django_apps/game_data/coverage/simulation_paths.py
git commit -m "fix(game_data): add coverage disposition package stubs"
```

---

### Task 2: Priority TSV + audit script flag

**Files:**
- Modify: `scripts/audit_simulation_nested_paths.py`
- Create: `documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv`

- [ ] **Step 1: Add `--priority` mode** (filter: max_list_len ≥ 4 OR priority keywords; cap 250 lines)

Append to `main()`:

```python
    parser.add_argument(
        "--priority",
        action="store_true",
        help="Emit priority families only (review subset, max 250 rows).",
    )
```

In `_emit_normalized_aggregate`, after building `ordered`, filter rows when `args.priority`:

```python
_PRIORITY_KW = (
    "ChainPosition",
    "TileBased",
    "ConnectableSimulation",
    "SimulationFactory",
    "ISimulationSystem",
    "k__BackingField",
    "ExtractorPosition",
    "_Networks",
    "Interlock",
)
# keep row if max_len >= 4 or any kw in norm_path; stop at 250 data lines
```

- [ ] **Step 2: Regenerate artifacts**

```powershell
cd f:\Python_Projects\shapez2Factory
python scripts/audit_simulation_nested_paths.py --normalized 2>documents/game_data_analysis/simulation_systems/_nested_path_audit.stderr.txt | Out-File -Encoding utf8 documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv
python scripts/audit_simulation_nested_paths.py --normalized --priority | Out-File -Encoding utf8 documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv
```

Expected stderr: `# total_norm_paths=5786`

- [ ] **Step 3: Commit**

```bash
git add scripts/audit_simulation_nested_paths.py documents/game_data_analysis/simulation_systems/_nested_path_audit.tsv documents/game_data_analysis/simulation_systems/_nested_path_audit_priority.tsv documents/game_data_analysis/simulation_systems/_nested_path_audit.stderr.txt
git commit -m "chore(game_data): simulation nested path audit TSV artifacts"
```

---

### Task 3: RED — simulation path coverage tests

**Files:**
- Create: `tests/unit/game_data/test_simulation_path_coverage.py`

- [ ] **Step 1: Write failing tests**

```python
"""Phase 2: simulation_systems.json nested path disposition parity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.manifest import MANIFEST
from django_apps.game_data.coverage.simulation_paths import classify_norm_path
from django_apps.game_data.coverage.reason_codes import (
    REFLECTION_METADATA,
    RUNTIME_DELEGATE,
    RUNTIME_UNITY_METADATA,
    SIMULATION_FACTORY_STUB,
)
from django_apps.game_data.models import (
    ConnectableSimulation,
    ImportBatch,
    SimulationConnector,
    SimulationLaneDefinition,
    UnknownProperty,
)

_REPO = Path(__file__).resolve().parents[3]
_PRIORITY_TSV = (
    _REPO
    / "documents"
    / "game_data_analysis"
    / "simulation_systems"
    / "_nested_path_audit_priority.tsv"
)


def _priority_paths() -> list[str]:
    assert _PRIORITY_TSV.is_file(), "run audit script with --priority first"
    lines = _PRIORITY_TSV.read_text(encoding="utf-8-sig").strip().splitlines()[1:]
    return [ln.split("\t", 1)[0] for ln in lines if ln.strip() and not ln.startswith("#")]


@pytest.mark.parametrize("norm_path", _priority_paths())
def test_priority_audit_path_has_manifest_disposition(norm_path: str) -> None:
    key = f"simulation_systems.json:{norm_path}"
    assert key in MANIFEST or classify_norm_path(norm_path) is not None


def test_chain_positions_classified_ignore_audit() -> None:
    d, _ = classify_norm_path(
        "definition_snapshot.ISimulationSystem.OnSimulationCreated.Listeners[]."
        "Target.TileBasedSystems[].ChainPositions"
    )
    assert d == Disposition.IGNORE_AUDIT


def test_connectable_root_promoted_in_manifest() -> None:
    assert MANIFEST["simulation_systems.json:simulation_parameters.ConnectableSimulations"][0] == (
        Disposition.PROMOTED
    )


@pytest.mark.django_db
def test_connectable_profile_has_promoted_rows_not_only_unknown(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    assert ConnectableSimulation.objects.filter(simulation_system__import_batch=batch).exists()
    assert SimulationConnector.objects.filter(
        connectable_simulation__simulation_system__import_batch=batch
    ).exists()
    assert SimulationLaneDefinition.objects.filter(
        connectable_simulation__simulation_system__import_batch=batch
    ).exists()


@pytest.mark.django_db
def test_definition_snapshot_chain_positions_unknown_after_import(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    qs = UnknownProperty.objects.filter(
        import_batch=batch,
        owner_model="SimulationSystem",
        reason_code=RUNTIME_DELEGATE,
        json_path__contains="ChainPositions",
    )
    assert qs.exists()
```

- [ ] **Step 2: Run RED**

```powershell
python -m pytest tests/unit/game_data/test_simulation_path_coverage.py
```

Expected: FAIL (`classify_norm_path` returns None, import audit missing, MANIFEST keys missing)

- [ ] **Step 3: Commit test-only**

```bash
git add tests/unit/game_data/test_simulation_path_coverage.py
git commit -m "test(game_data): RED simulation nested path coverage gates"
```

---

### Task 4: Classification rules + manifest entries

**Files:**
- Modify: `django_apps/game_data/coverage/simulation_paths.py`
- Modify: `django_apps/game_data/coverage/manifest.py` (only if manual entries need tweaks)

- [ ] **Step 1: Implement rules** (longest-prefix wins; first match in ordered list)

```python
from django_apps.game_data.coverage import reason_codes as rc
from django_apps.game_data.coverage.disposition import Disposition

# (pattern_suffix, disposition, note) — pattern is suffix after "simulation_systems.json:"
_RULES: list[tuple[str, Disposition, str]] = [
    ("simulation_parameters.ConnectableSimulations[].Connectors", Disposition.PROMOTED, "SimulationConnector"),
    ("simulation_parameters.ConnectableSimulations[].Simulation._Lanes", Disposition.PROMOTED, "SimulationLaneDefinition"),
    ("simulation_parameters.ConnectableSimulations[].Simulation.InputLanes", Disposition.CROSS_REF, "lane importer alias"),
    ("simulation_parameters.ConnectableSimulations[].ChunkBounds", Disposition.PROMOTED, "SimulationChunkBounds"),
    ("simulation_parameters.ConnectableSimulations[].TileBounds", Disposition.PROMOTED, "SimulationTileBounds"),
    ("simulation_parameters.ConnectableSimulations[].Building", Disposition.CROSS_REF, "BuildingVariant"),
    ("simulation_parameters.ConnectableSimulations", Disposition.PROMOTED, "ConnectableSimulation"),
    ("definition_snapshot.ChainPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems[].ChainPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ExtractorPositions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("TileBasedSystems[].ConnectableSimulations", Disposition.CROSS_REF, "params ConnectableSimulations"),
    ("Interlock.", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("k__BackingField", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    (".Assembly.", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("DefinedTypes", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("ExportedTypes", Disposition.IGNORE_AUDIT, rc.REFLECTION_METADATA),
    ("ISimulationSystem.", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("SimulationFactory.", Disposition.IGNORE_AUDIT, rc.SIMULATION_FACTORY_STUB),
    ("ConnectableSimulations[].Junctions", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ConnectableSimulations[].Simulation.State", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("ConnectableSimulations[].Simulation.NextBundle", Disposition.IGNORE_AUDIT, rc.RUNTIME_DELEGATE),
    ("$type", Disposition.IGNORE_AUDIT, rc.RUNTIME_UNITY_METADATA),
]


def classify_norm_path(norm_path: str) -> tuple[Disposition, str] | None:
    best: tuple[int, Disposition, str] | None = None
    for suffix, disposition, note in _RULES:
        if suffix in norm_path:
            rank = len(suffix)
            if best is None or rank > best[0]:
                best = (rank, disposition, note)
    if best is None:
        return None
    return best[1], best[2]


def manifest_entries_from_rules() -> dict[str, tuple[Disposition, str]]:
    out: dict[str, tuple[Disposition, str]] = {}
    for suffix, disposition, note in _RULES:
        out[f"simulation_systems.json:{suffix}"] = (disposition, note)
    return out
```

- [ ] **Step 2: Run subset test**

```powershell
python -m pytest tests/unit/game_data/test_simulation_path_coverage.py::test_chain_positions_classified_ignore_audit tests/unit/game_data/test_simulation_path_coverage.py::test_priority_audit_path_has_manifest_disposition
```

Expected: priority test may still FAIL for paths not matching any suffix — extend `_RULES` until priority TSV lines classify (iterate once, commit).

- [ ] **Step 3: Commit**

```bash
git add django_apps/game_data/coverage/simulation_paths.py
git commit -m "feat(game_data): simulation path disposition rules"
```

---

### Task 5: `definition_snapshot` coverage audit importer

**Files:**
- Create: `django_apps/game_data/importers/simulation_definition_snapshot_audit.py`

- [ ] **Step 1: Implement bounded walk** (max 40 UnknownProperty rows per system; prefix keys only for list-heavy paths)

```python
"""Record definition_snapshot ignore_audit coverage for SimulationSystem rows."""

from __future__ import annotations

from typing import Any

from django_apps.game_data.coverage.simulation_paths import classify_norm_path
from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.importers.base import ImportContext

_MAX_RECORDS = 40
_LIST_HEAVY = ("ChainPositions", "TileBasedSystems", "k__BackingField", "Listeners")


def _should_record_prefix(path: str) -> bool:
    return any(marker in path for marker in _LIST_HEAVY)


def sync_definition_snapshot_coverage_audit(
    ctx: ImportContext,
    *,
    owner_key: str,
    definition_snapshot: dict[str, Any] | None,
) -> int:
    if not isinstance(definition_snapshot, dict):
        return 0
    recorded = 0
    seen: set[str] = set()

    def walk(obj: object, prefix: str) -> None:
        nonlocal recorded
        if recorded >= _MAX_RECORDS:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                path = f"{prefix}.{key}" if prefix else key
                norm = path  # indices already absent at this depth until lists
                if path not in seen:
                    classified = classify_norm_path(path)
                    if classified and classified[0] == Disposition.IGNORE_AUDIT:
                        if _should_record_prefix(path) or not isinstance(val, (dict, list)):
                            ctx.record_unknown(
                                "SimulationSystem",
                                owner_key,
                                f"definition_snapshot.{path}",
                                key,
                                val,
                                reason_code=classified[1],
                                classification="definition_snapshot_coverage",
                            )
                            seen.add(path)
                            recorded += 1
                walk(val, path)
        elif isinstance(obj, list) and prefix:
            if _should_record_prefix(prefix) and prefix not in seen:
                classified = classify_norm_path(prefix)
                if classified and classified[0] == Disposition.IGNORE_AUDIT:
                    ctx.record_unknown(
                        "SimulationSystem",
                        owner_key,
                        f"definition_snapshot.{prefix}",
                        prefix.rsplit(".", 1)[-1],
                        obj,
                        reason_code=classified[1],
                        classification="definition_snapshot_coverage",
                    )
                    seen.add(prefix)
                    recorded += 1
            for item in obj[:3]:
                walk(item, f"{prefix}[]")

    walk(definition_snapshot, "")
    return recorded
```

- [ ] **Step 2: Verify importer import**

Run: `python -c "from django_apps.game_data.importers.simulation_systems import import_simulation_systems; print('ok')"`

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add django_apps/game_data/importers/simulation_definition_snapshot_audit.py
git commit -m "feat(game_data): definition_snapshot coverage audit"
```

---

### Task 6: GREEN parity tests + manifest smoke

**Files:**
- Modify: `tests/unit/game_data/test_domain_coverage_manifest.py`

- [ ] **Step 1: Add duplicate-prefix guard**

```python
def test_manifest_simulation_rules_have_unique_suffix() -> None:
    sim_keys = [k for k in MANIFEST if k.startswith("simulation_systems.json:")]
    suffixes = [k.split(":", 1)[1] for k in sim_keys]
    assert len(suffixes) == len(set(suffixes))
```

- [ ] **Step 2: Run GREEN gate**

```powershell
python -m pytest tests/unit/game_data/test_simulation_path_coverage.py tests/unit/game_data/test_domain_coverage_manifest.py
python -m ruff check django_apps/game_data/coverage django_apps/game_data/importers/simulation_definition_snapshot_audit.py tests/unit/game_data/test_simulation_path_coverage.py
```

Expected: PASS (if `test_priority_audit_path_has_manifest_disposition` fails, add `_RULES` entries for remaining priority TSV rows — **no PROMOTED additions** without explicit approval)

- [ ] **Step 3: Full game_data narrow gate**

```powershell
python -m pytest tests/unit/game_data/test_simulation_systems_import.py tests/unit/game_data/test_simulation_parameter_registry.py
```

- [ ] **Step 4: Commit**

```bash
git add tests/unit/game_data/test_domain_coverage_manifest.py
git commit -m "test(game_data): GREEN simulation path coverage parity"
```

---

### Task 7: Document Phase 2 closure

**Files:**
- Modify: `docs/domain/game_data_coverage.md`
- Modify: `docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md` (status line only)

- [ ] **Step 1: Replace “Phase 2 pending” table** with classification table from this plan + link to `_nested_path_audit_priority.tsv`

- [ ] **Step 2: Update spec status**

```markdown
**Status:** Phase 0–1, 1d, 3 + **Phase 2 simulation path audit** implemented (2026-05-22)
```

- [ ] **Step 3: Commit**

```bash
git add docs/domain/game_data_coverage.md docs/superpowers/specs/2026-05-22-game-data-domain-complete-coverage-design.md
git commit -m "docs(game_data): Phase 2 simulation path disposition"
```

---

## Self-review (plan author)

| Check | Result |
| ----- | ------ |
| Spec coverage: audit → classify → manifest → tests | Tasks 2–7 |
| Placeholder scan | No TBD tasks |
| No new models unless promoted | ChainPositions = ignore_audit only |
| Broken imports fixed | Task 1 + Task 5 |
| Gap | Priority TSV may need 1–2 rule iterations in Task 4 Step 2 — expected |

---

## Verification commands (full Phase 2 done)

```powershell
python scripts/audit_simulation_nested_paths.py --normalized --priority
python -m pytest tests/unit/game_data/test_simulation_path_coverage.py tests/unit/game_data/test_domain_coverage_manifest.py
python -m ruff check django_apps/game_data/coverage django_apps/game_data/importers/simulation_definition_snapshot_audit.py
```

**Success statement (allowed after GREEN):**

```text
simulation_systems.json priority nested paths are explicitly
promoted / cross_ref / ignore_audit via manifest + import audit + tests.
Domain-complete coverage for simulation channel is proven at Phase 2 scope.
```

**Housekeeping later (out of scope):** regenerate `game_data_backup/game_data_dump.json` after Phase 2 gate.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-22-game-data-phase2-simulation-path-audit.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach?
