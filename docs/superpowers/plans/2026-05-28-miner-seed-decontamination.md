# Miner Seed Decontamination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace exhaustive/GeneTemplate miner catalog with 14 DB-canonical `GeneticSample` seeds from game paste, introduce `MinerSeedPattern` + shape/fluid projection, and hard-delete RTTP/legacy pollution in three ordered PRs.

**Architecture:** L0 bootstrap file → `seed_miner_patterns` ingest → L1 `GeneticSample` (island-local `decoded_json`) → L2 `MinerSeedPattern` DTO → L3 `project_miner_layout(resource_kind)`. Coordinate contract: never reject `X==0`/`x==0` on seed or solver-facing paths. RTTP removed in a separate PR with `rg` gate.

**Tech Stack:** Django 5.2, pytest, ruff, mypy (`django_apps config src`), PowerShell `scripts/test_fast.ps1` / `test_full.ps1`.

**Spec:** [`../specs/2026-05-28-miner-seed-decontamination-design.md`](../specs/2026-05-28-miner-seed-decontamination-design.md)

**Branches (recommended worktrees):**

| PR | Branch | Base |
|----|--------|------|
| PR-Seed | `feat/miner-seed-pr-seed` | `master` |
| PR-Legacy | `feat/miner-seed-pr-legacy` | PR-Seed merge commit |
| PR-RTTP | `feat/miner-seed-pr-rttp` | `master` (may merge in parallel) |

---

## File map (all PRs)

| File | PR | Action |
|------|-----|--------|
| `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py` | Seed | Create |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py` | Seed | Create |
| `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py` | Seed | Create |
| `tests/unit/asteroid_lab/test_miner_seed_topology.py` | Seed | Create |
| `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py` | Seed | Create |
| `tests/unit/architecture/test_miner_seed_bootstrap_read_boundary.py` | Seed | Create |
| `django_apps/asteroid_lab/admin.py` | Seed | Modify — replace exhaustive admin form |
| `django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html` | Seed | Modify |
| `django_apps/web/services/asteroid_lab_page_context.py` | Seed | Modify — `miner_seed_v1` catalog |
| `tests/integration/conftest.py` | Seed | Modify — seed 14 miner rows, drop exhaustive autouse |
| `var/default_miner_pattern.txt` | Seed | Read-only evidence (no code changes) |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_pattern.py` | Legacy | Create |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_projection.py` | Legacy | Create |
| `django_apps/asteroid_lab/snapshots/asteroid_map_coords.py` | Legacy | Modify — remove solver-facing `x==0` reject |
| `tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py` | Legacy | Create |
| `tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py` | Legacy | Create |
| `django_apps/asteroid_lab/services/miner_seed_pattern_export.py` | Legacy | Create (replaces gene export) |
| `django_apps/asteroid_lab/services/runtime_miner_seed_pattern_source.py` | Legacy | Create (rename from `runtime_gene_template_source.py`) |
| `django_apps/asteroid_lab/services/genetic_sample_gene_export.py` | Legacy | Delete |
| `django_apps/asteroid_lab/services/runtime_gene_template_source.py` | Legacy | Delete |
| `django_apps/asteroid_lab/genetic_sample/gene_template.py` | Legacy | Delete |
| `django_apps/asteroid_lab/genetic_sample/gene_template_loader.py` | Legacy | Delete |
| `django_apps/asteroid_lab/genetic_sample/exhaustive_generator.py` | Legacy | Delete |
| `django_apps/asteroid_lab/management/commands/seed_exhaustive_sample_genes.py` | Legacy | Delete |
| `django_apps/asteroid_lab/migrations/00XX_drop_pattern_template.py` | Legacy | Create |
| `tests/fixtures/asteroid_lab/gene_templates/*.json` | Legacy | Delete |
| `tests/unit/asteroid_lab/test_gene_template_loader.py` | Legacy | Delete |
| `tests/unit/asteroid_lab/test_genetic_sample_gene_export.py` | Legacy | Delete → `test_miner_seed_pattern_export.py` |
| `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` | Legacy | Delete |
| `tests/unit/asteroid_lab/test_runtime_gene_template_source.py` | Legacy | Replace |
| `config/settings.py` | Legacy | Remove `gene_templates` fixture path if unused |
| `documents/ai/plans/exhaustive_sample_gene_seed.md` | Legacy | Add superseded banner → spec link |
| `.github/workflows/rttp-lab-macro-smoke.yml` | RTTP | Delete |
| `docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md` | RTTP | Delete |
| `django_apps/asteroid_lab/replay/replay_enums.py` | RTTP | Modify — remove `RTTP_*` |
| `django_apps/asteroid_lab/replay/event_types.py` | RTTP | Modify — remove RTTP wire types |
| `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | RTTP | Modify — remove rttp sections |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | RTTP | Modify |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | RTTP | Modify |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | RTTP | Modify |
| `tests/unit/architecture/test_miner_seed_decontamination_tokens.py` | RTTP | Create |
| `scripts/test_miner_seed_decontamination_tokens.ps1` | RTTP | Create (optional CI wrapper) |

**Out of scope:** Layer 02 exterior transport, `MiningExtractionRule`, reconstruction complete map.

---

# Part A — PR-Seed

### Task 0: Baseline and branch

**Files:** (read-only)

- [ ] **Step 1: Branch**

```powershell
git checkout master
git pull
git checkout -b feat/miner-seed-pr-seed
```

- [ ] **Step 2: Record baseline (must be green)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_genetic_sample_gene_export.py -v
python -m pytest tests/unit/asteroid_lab/test_sample_gene_exhaustive.py -v --maxfail=1
```

Expected: tests pass (documents current exhaustive coupling).

- [ ] **Step 3: Confirm bootstrap file**

```powershell
python -c "print(len([l for l in open('var/default_miner_pattern.txt') if l.strip()]))"
```

Expected: `14`.

---

### Task 1: Miner seed constants and topology signature

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py`
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_topology.py`

- [ ] **Step 1: Write failing topology tests**

Create `tests/unit/asteroid_lab/test_miner_seed_topology.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    topology_signature_from_decoded_root,
    throughput_factor_for_extension_count,
)

_BOOTSTRAP = Path("var/default_miner_pattern.txt")


@pytest.fixture(scope="module")
def bootstrap_lines() -> list[str]:
    return [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_bootstrap_has_fourteen_lines(bootstrap_lines: list[str]) -> None:
    assert len(bootstrap_lines) == 14


def test_topology_signatures_unique_among_bootstrap(bootstrap_lines: list[str]) -> None:
    sigs: list[str] = []
    for line in bootstrap_lines:
        dto = decode_copy_string(line)
        sigs.append(topology_signature_from_decoded_root(dto.root))
    assert len(sigs) == len(set(sigs))


def test_extension_count_distribution(bootstrap_lines: list[str]) -> None:
    counts = [count_extensions(decode_copy_string(line).root) for line in bootstrap_lines]
    assert counts.count(3) == 8
    assert counts.count(2) == 3
    assert counts.count(1) == 2
    assert counts.count(0) == 1


def test_throughput_factor_table() -> None:
    assert throughput_factor_for_extension_count(0) == 4
    assert throughput_factor_for_extension_count(3) == 16
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_seed_topology.py -v
```

Expected: `ModuleNotFoundError` for `miner_seed_topology`.

- [ ] **Step 3: Implement constants**

Create `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py`:

```python
from __future__ import annotations

MINER_SEED_SCHEMA = "miner_seed_v1"
EXHAUSTIVE_GENERATOR_STALE = "exhaustive_sample_gene_v1"
DEFAULT_BOOTSTRAP_PATH = "var/default_miner_pattern.txt"

MINER_LAYOUT_TYPES_SHAPE = (
    "Layout_ShapeMiner",
    "Layout_ShapeMinerExtension",
    "SpaceBelt_Forward",
)

LAYOUT_TYPE_SHAPE_TO_FLUID: dict[str, str] = {
    "Layout_ShapeMiner": "Layout_FluidMiner",
    "Layout_ShapeMinerExtension": "Layout_FluidMinerExtension",
    "SpaceBelt_Forward": "SpacePipe_Forward",
}


def gene_key_for_rank(rank: int) -> str:
    if rank < 1 or rank > 14:
        msg = "seed rank must be 1..14"
        raise ValueError(msg)
    return f"miner_seed_{rank:02d}"
```

- [ ] **Step 4: Implement topology signature**

Create `django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py`:

```python
from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    entry_raw_r,
    entry_raw_x,
    entry_raw_y,
)

_MINER_T = frozenset({"Layout_ShapeMiner", "Layout_FluidMiner"})
_EXT_T = frozenset({"Layout_ShapeMinerExtension", "Layout_FluidMinerExtension"})
_BELT_T = frozenset({"SpaceBelt_Forward", "SpacePipe_Forward"})


def throughput_factor_for_extension_count(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be 0..3"
        raise ValueError(msg)
    return 4 * (1 + extension_count)


def _entries(root: dict[str, Any]) -> list[dict[str, Any]]:
    bp = root.get("BP")
    if not isinstance(bp, dict):
        return []
    raw = bp.get("Entries")
    return list(raw) if isinstance(raw, list) else []


def count_extensions(root: dict[str, Any]) -> int:
    return sum(1 for e in _entries(root) if e.get("T") in _EXT_T)


def topology_signature_from_decoded_root(root: dict[str, Any]) -> str:
    """Stable hash: island-local cells relative to miner, roles not fluid-specific types."""
    entries = _entries(root)
    miner_xy: tuple[int, int] | None = None
    cells: list[tuple[int, int, str, int]] = []
    for e in entries:
        t = str(e.get("T", ""))
        x, y, r = entry_raw_x(e), entry_raw_y(e), entry_raw_r(e)
        if t in _MINER_T:
            role = "miner"
            miner_xy = (x, y)
        elif t in _EXT_T:
            role = "ext"
        elif t in _BELT_T:
            role = "belt"
        else:
            continue
        cells.append((x, y, role, r))
    if miner_xy is None:
        msg = "miner entry required for topology signature"
        raise ValueError(msg)
    mx, my = miner_xy
    rel = sorted(
        [(x - mx, y - my, role, r) for x, y, role, r in cells],
        key=lambda c: (c[0], c[1], c[2]),
    )
    payload = {"cells": rel}
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
```

- [ ] **Step 5: Run topology tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_seed_topology.py -v
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py tests/unit/asteroid_lab/test_miner_seed_topology.py
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py tests/unit/asteroid_lab/test_miner_seed_topology.py
git commit -m "feat(asteroid_lab): add miner seed topology signature helpers"
```

---

### Task 2: `seed_miner_patterns` management command

**Files:**
- Create: `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py`
- Create: `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py`

- [ ] **Step 1: Write failing command tests**

Create `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py`:

```python
from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXHAUSTIVE_GENERATOR_STALE,
    MINER_SEED_SCHEMA,
)
from django_apps.asteroid_lab.models import GeneticSample


@pytest.mark.django_db
def test_seed_miner_patterns_ingests_fourteen_unique_signatures() -> None:
    call_command("seed_miner_patterns", replace_stale=True)
    qs = GeneticSample.objects.filter(metadata_json__schema=MINER_SEED_SCHEMA, metadata_json__is_seed=True)
    assert qs.count() == 14
    sigs = {row.metadata_json["topology_signature"] for row in qs}
    assert len(sigs) == 14


@pytest.mark.django_db
def test_stale_exhaustive_samples_removed_on_replace() -> None:
    GeneticSample.objects.create(
        gene_key="stale_exhaustive_key",
        name="stale",
        code="SHAPEZ2-4-stale$",
        metadata_json={"generator": EXHAUSTIVE_GENERATOR_STALE},
    )
    call_command("seed_miner_patterns", replace_stale=True)
    assert not GeneticSample.objects.filter(metadata_json__generator=EXHAUSTIVE_GENERATOR_STALE).exists()


@pytest.mark.django_db
def test_stored_code_matches_bootstrap_bytes() -> None:
    call_command("seed_miner_patterns")
    lines = [ln.strip() for ln in open("var/default_miner_pattern.txt") if ln.strip()]
    for rank, line in enumerate(lines, start=1):
        row = GeneticSample.objects.get(gene_key=f"miner_seed_{rank:02d}")
        assert row.code == line
```

- [ ] **Step 2: Run — expect FAIL** (`Unknown command`)

```powershell
python -m pytest tests/unit/asteroid_lab/test_seed_miner_patterns_command.py -v
```

- [ ] **Step 3: Implement command**

Create `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py` (core logic):

```python
import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    DEFAULT_BOOTSTRAP_PATH,
    EXHAUSTIVE_GENERATOR_STALE,
    MINER_LAYOUT_TYPES_SHAPE,
    MINER_SEED_SCHEMA,
    gene_key_for_rank,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
    topology_signature_from_decoded_root,
)
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.snapshots.island_coord_meta import attach_island_coord_meta_to_decoded_json


class Command(BaseCommand):
    help = "Ingest 14 miner seed patterns from bootstrap copy strings into GeneticSample."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=DEFAULT_BOOTSTRAP_PATH)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--replace-stale", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["file"])
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) != 14:
            raise SystemExit(f"expected 14 non-empty lines, got {len(lines)}")
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        sigs: set[str] = set()
        for rank, code in enumerate(lines, start=1):
            raw = decode_copy_string(code)
            dto = normalize_decoded_blueprint(raw)
            merged = dict(dto.decoded_json)
            attach_island_coord_meta_to_decoded_json(merged)
            sig = topology_signature_from_decoded_root(dto.root)
            if sig in sigs:
                raise SystemExit(f"duplicate topology_signature at rank {rank}")
            sigs.add(sig)
            ext = count_extensions(dto.root)
            meta = {
                "schema": MINER_SEED_SCHEMA,
                "is_seed": True,
                "seed_rank": rank,
                "source": {"file": str(path).replace("\\", "/"), "line_no": rank, "file_sha256": file_sha},
                "topology_signature": sig,
                "extension_count": ext,
                "throughput_factor": throughput_factor_for_extension_count(ext),
                "resource_kind_stored": "shape",
                "layout_types": list(MINER_LAYOUT_TYPES_SHAPE),
            }
            if options["dry_run"]:
                continue
            GeneticSample.objects.update_or_create(
                gene_key=gene_key_for_rank(rank),
                defaults={"name": f"Seed ext={ext} rank={rank:02d}", "code": code, "metadata_json": meta, "decoded_json": merged},
            )
        if options["replace_stale"] and not options["dry_run"]:
            GeneticSample.objects.filter(metadata_json__generator=EXHAUSTIVE_GENERATOR_STALE).delete()
        self.stdout.write(self.style.SUCCESS(f"miner seeds: {len(lines)} ({'dry-run' if options['dry_run'] else 'saved'})"))
```

- [ ] **Step 4: Run command tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_seed_miner_patterns_command.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/management/commands/seed_miner_patterns.py tests/unit/asteroid_lab/test_seed_miner_patterns_command.py
git commit -m "feat(asteroid_lab): add seed_miner_patterns management command"
```

---

### Task 3: Bootstrap read boundary (architecture test)

**Files:**
- Create: `tests/unit/architecture/test_miner_seed_bootstrap_read_boundary.py`

- [ ] **Step 1: Write architecture test**

```python
from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DJANGO_APPS = _REPO / "django_apps"
_BOOTSTRAP_NAME = "default_miner_pattern.txt"
_ALLOWED_READERS = {
    _REPO / "django_apps" / "asteroid_lab" / "management" / "commands" / "seed_miner_patterns.py",
}


def _py_files_under(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def test_runtime_solver_paths_do_not_reference_bootstrap_file() -> None:
    violations: list[str] = []
    for path in _py_files_under(_DJANGO_APPS):
        if path in _ALLOWED_READERS:
            continue
        if "management" in path.parts and "commands" in path.parts:
            if path.name != "seed_miner_patterns.py":
                continue
        text = path.read_text(encoding="utf-8")
        if _BOOTSTRAP_NAME in text:
            violations.append(str(path.relative_to(_REPO)))
    assert violations == [], f"bootstrap file referenced outside ingest command: {violations}"
```

- [ ] **Step 2: Run — expect PASS after Task 2**

```powershell
python -m pytest tests/unit/architecture/test_miner_seed_bootstrap_read_boundary.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/unit/architecture/test_miner_seed_bootstrap_read_boundary.py
git commit -m "test(architecture): forbid bootstrap miner pattern reads outside ingest"
```

---

### Task 4: Integration conftest and admin/UI catalog

**Files:**
- Modify: `tests/integration/conftest.py`
- Modify: `django_apps/asteroid_lab/admin.py`
- Modify: `django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html`
- Modify: `django_apps/web/services/asteroid_lab_page_context.py`

- [ ] **Step 1: Replace exhaustive autouse fixture**

In `tests/integration/conftest.py`, remove `generate_exhaustive_sample_genes` imports and replace with:

```python
@pytest.fixture(autouse=True)
def seed_miner_patterns_db(db: None) -> None:
    from django.core.management import call_command

    call_command("seed_miner_patterns", replace_stale=True)
```

- [ ] **Step 2: Update page catalog**

In `asteroid_lab_page_context.py`, change `_DEFAULT_GENERATOR_VERSION` to `MINER_SEED_SCHEMA` filter:

```python
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA

# filter: metadata_json__schema=MINER_SEED_SCHEMA, metadata_json__is_seed=True
# seed_command_hint: "python manage.py seed_miner_patterns"
```

- [ ] **Step 3: Admin — swap exhaustive form URL to `seed_miner_patterns`**

Mirror existing `seed_exhaustive_samples_view` but call `call_command("seed_miner_patterns", replace_stale=True)`.

- [ ] **Step 4: Run narrow integration tests**

```powershell
python -m pytest tests/integration/test_integration_conftest_contract.py -v
python -m pytest tests/integration/web/test_asteroid_run_solver.py -v --maxfail=3
```

Note: RTTP assertions in solver integration tests may still pass until PR-RTTP; do not expand scope.

- [ ] **Step 5: PR-Seed gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_seed_topology.py tests/unit/asteroid_lab/test_seed_miner_patterns_command.py tests/unit/architecture/test_miner_seed_bootstrap_read_boundary.py -v
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py django_apps/asteroid_lab/genetic_sample/miner_seed_topology.py django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
```

- [ ] **Step 6: Commit and open PR-Seed**

```bash
git add tests/integration/conftest.py django_apps/asteroid_lab/admin.py django_apps/web/services/asteroid_lab_page_context.py django_apps/web/templates/admin/asteroid_lab/geneticsample/change_list.html
git commit -m "feat(asteroid_lab): wire miner seed ingest into admin and integration fixtures"
```

Update `documents/ai/current_plan.md` with PR-Seed ACTIVE row.

---

# Part B — PR-Legacy (after PR-Seed merged)

### Task 5: `MinerSeedPattern` DTO from DB `decoded_json`

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_pattern.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_pattern.py`

- [ ] **Step 1: Failing test — build from seeded DB row**

```python
@pytest.mark.django_db
def test_miner_seed_pattern_from_genetic_sample_uses_decoded_json() -> None:
    call_command("seed_miner_patterns")
    sample = GeneticSample.objects.get(gene_key="miner_seed_14")
    pattern = miner_seed_pattern_from_genetic_sample(sample)
    assert pattern.seed_id == "miner_seed_14"
    assert pattern.extension_count == 0
    assert pattern.throughput_factor == 4
    assert pattern.topology_signature == sample.metadata_json["topology_signature"]
```

- [ ] **Step 2: Implement `miner_seed_pattern_from_genetic_sample`**

Parse `sample.decoded_json["BP"]["Entries"]` with `copy_json_coords`; populate `occupied_island_cells`, `output_transport_cell` (belt adjacent to miner), `extension_attachments` via 4-neighbor tree BFS from miner.

**Must not import** `exhaustive_generator`.

- [ ] **Step 3: Run tests PASS + ruff**

---

### Task 6: Shape/fluid projection

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_projection.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_projection.py`

- [ ] **Step 1: Failing test — fluid `T` swap**

```python
def test_project_fluid_layout_types_from_shape_seed() -> None:
    call_command("seed_miner_patterns")
    sample = GeneticSample.objects.get(gene_key="miner_seed_01")
    pattern = miner_seed_pattern_from_genetic_sample(sample)
    entries = project_miner_layout(pattern, resource_kind="fluid")
    types = {e["T"] for e in entries}
    assert "Layout_FluidMiner" in types
    assert "SpacePipe_Forward" in types
    assert "Layout_ShapeMiner" not in types
```

- [ ] **Step 2: Implement `project_miner_layout`**

Use `LAYOUT_TYPE_SHAPE_TO_FLUID` from constants; recompute extension `R` with `compute_extension_rotations_by_parent` logic extracted to projection module (copy port-compatible loop from exhaustive generator **without** `abstract_grid_to_raw_xy` or `assert_blueprint_entries_raw_x_nonzero`).

- [ ] **Step 3: Test — no raw X==0 reject on encode path**

```python
def test_no_assert_raw_x_nonzero_on_seed_encode_path() -> None:
    # build entries including X==0 from seed 01; call encode; must not raise raw X==0
```

---

### Task 7: Export service rename and wire consumers

**Files:**
- Create: `django_apps/asteroid_lab/services/miner_seed_pattern_export.py`
- Create: `django_apps/asteroid_lab/services/runtime_miner_seed_pattern_source.py`
- Delete: `genetic_sample_gene_export.py`, `runtime_gene_template_source.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py` — key `miner_seed_pattern_source`
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`

- [ ] **Step 1: Replace export API**

```python
def load_miner_seed_patterns_from_genetic_samples(qs) -> tuple[tuple[MinerSeedPattern, ...], int, list[str]]:
    ...
```

Filter: `metadata_json__schema=miner_seed_v1`, `is_seed=True`.

- [ ] **Step 2: Update/rename tests** (`test_miner_seed_pattern_export.py`, `test_runtime_miner_seed_pattern_source.py`)

- [ ] **Step 3: Grep consumers**

```powershell
rg "gene_template|GeneTemplate|genetic_sample_gene_export|runtime_gene_template" django_apps tests config
```

Fix all import sites.

---

### Task 8A: Retire `asteroid_map_coords` no-x==0 solver gate (blocking, PR-Legacy)

**PR:** PR-Legacy — **must complete before Task 8 commit.** Do not defer until tests fail.

**Rationale:** `asteroid_map_coords` world-map `x == 0` rejection is legacy RTTP / raw-grid contamination. Spec §2 forbids rejecting `x==0` on seed, reconstruction, candidate, route, and probe paths.

**Files:**
- Modify: `django_apps/asteroid_lab/snapshots/asteroid_map_coords.py`
- Search/modify: import sites under `django_apps/asteroid_lab/` (seed, reconstruction, candidate, route, export, projection)
- Create: `tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py`

- [ ] **Step 1: Inventory**

```powershell
rg "assert.*x.*0|x.*0.*reject|raw_x_nonzero|asteroid_map_coords|abstract_grid_to_raw_xy|_MSG_NO_X0|world_raw_coord" django_apps tests
```

Record hits in PR notes. Classify each as: **solver-facing (must fix)** vs **legacy raw-global construction only (isolate/rename)**.

- [ ] **Step 2: Remove or isolate no-x==0 validators**

In `asteroid_map_coords.py`, remove `ValueError` raises when `x == 0` from:

- `visual_col`
- `left_of` / `right_of`
- `world_raw_coord`

Define behaviour at `x == 0` explicitly (spec: allowed on dense/domain coords):

- `visual_col(0) -> 0` (identity at dense origin) **or** document mapping in module docstring if UI needs a different dense index
- `left_of(0) -> -1`, `right_of(0) -> 1` (standard integer neighbours)
- `world_raw_coord(0, y)` returns `WorldRawCoord(0, y)` without raise

If any helper must keep “skip column 0” semantics for **non-solver** forensic tools only:

- Move to `django_apps/asteroid_lab/snapshots/legacy_raw_global_grid.py` (new, clearly named)
- **Must not** be imported from `genetic_sample/`, `miner_seed_*`, reconstruction pipeline, candidate generation, route probe, or `miner_seed_projection`

- [ ] **Step 3: Regression test — seed pipeline with island-local `X==0`**

Create `tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py`:

```python
from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_pattern import (
    miner_seed_pattern_from_genetic_sample,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_projection import project_miner_layout
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.snapshots.asteroid_map_coords import world_raw_coord


@pytest.mark.django_db
def test_world_raw_coord_allows_x_zero() -> None:
    c = world_raw_coord(0, 1)
    assert c.x == 0 and c.y == 1


@pytest.mark.django_db
def test_seed_with_island_x_zero_passes_pattern_and_projection() -> None:
    call_command("seed_miner_patterns")
    sample = GeneticSample.objects.get(gene_key="miner_seed_01")
    pattern = miner_seed_pattern_from_genetic_sample(sample)
    entries = project_miner_layout(pattern, resource_kind="shape")
    xs = {e.get("X", 0) for e in entries}
    assert 0 in xs
```

Extend with encode + any candidate/probe boundary helper once wired in Task 7 (same PR).

- [ ] **Step 4: Architecture gate — no solver-facing contamination imports**

Create `tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py`:

```python
from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FORBIDDEN_IN_SOLVER_PATHS = (
    "django_apps/asteroid_lab/genetic_sample",
    "django_apps/asteroid_lab/services",
    "django_apps/asteroid_lab/reconstruction",
)
_LEGACY_ONLY_MODULE = "legacy_raw_global_grid"


def _raises_on_x_zero(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if "x == 0" in test and any(isinstance(b, ast.Raise) for b in node.body):
                return True
    return False


def test_asteroid_map_coords_does_not_raise_on_x_zero() -> None:
    path = _REPO / "django_apps/asteroid_lab/snapshots/asteroid_map_coords.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert not _raises_on_x_zero(tree), "asteroid_map_coords must not raise on x==0"


def test_solver_packages_do_not_import_legacy_raw_global_grid() -> None:
    for pkg in _FORBIDDEN_IN_SOLVER_PATHS:
        root = _REPO / pkg
        for py in root.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            assert _LEGACY_ONLY_MODULE not in text, f"{py} imports legacy raw-global grid"
```

- [ ] **Step 5: Run Task 8A gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py -v
rg "assert_blueprint_entries_raw_x_nonzero|abstract_grid_to_raw_xy" django_apps/asteroid_lab tests/unit/asteroid_lab
rg "_MSG_NO_X0|raise ValueError.*x == 0" django_apps/asteroid_lab/snapshots/asteroid_map_coords.py
```

Expected: no `assert_blueprint_entries_raw_x_nonzero` / `abstract_grid_to_raw_xy` under `django_apps/asteroid_lab` or `tests/unit/asteroid_lab`; `asteroid_map_coords.py` has no `raise` on `x == 0`.

- [ ] **Step 6: Commit (before Task 8 deletions)**

```bash
git add django_apps/asteroid_lab/snapshots/asteroid_map_coords.py tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py
git commit -m "fix(asteroid_lab): allow x==0 on solver-facing map coords (drop RTTP gate)"
```

---

### Task 8: Delete legacy modules and tests

**Files:** (see file map — delete list)

- [ ] **Step 1: Delete files**

Remove: `exhaustive_generator.py`, `gene_template.py`, `gene_template_loader.py`, `seed_exhaustive_sample_genes.py`, `test_sample_gene_exhaustive.py`, `test_gene_template_loader.py`, fixture JSONs.

- [ ] **Step 2: Drop PatternTemplate / PatternVariant**

```powershell
python manage.py makemigrations asteroid_lab --name drop_pattern_template_variant
```

Ensure migration removes both models; update `admin.py` registrations.

- [ ] **Step 3: Remove `config/settings.py` gene_templates path** if nothing references it.

- [ ] **Step 4: PR-Legacy gate (includes Task 8A inventory)**

```powershell
python -m pytest tests/unit/asteroid_lab -v --maxfail=5
python -m pytest tests/unit/architecture/test_no_solver_facing_x_zero_rejection.py tests/unit/asteroid_lab/test_miner_seed_x_zero_pipeline.py -v
python -m ruff check django_apps/asteroid_lab
python -m mypy django_apps/asteroid_lab
rg "GeneTemplate|exhaustive_sample_gene|generate_exhaustive_sample_genes|assert_blueprint_entries_raw_x_nonzero|abstract_grid_to_raw_xy" django_apps tests
rg "assert.*x.*0|_MSG_NO_X0|raw_x_nonzero" django_apps/asteroid_lab/genetic_sample django_apps/asteroid_lab/services django_apps/asteroid_lab/reconstruction tests/unit/asteroid_lab
```

Expected:

- No forbidden tokens in `django_apps` / `tests` (docs until PR-RTTP)
- No solver-facing `x==0` reject in seed/reconstruction/candidate/route paths
- Task 8A architecture + pipeline tests green

- [ ] **Step 5: Commit PR-Legacy**

---

# Part C — PR-RTTP (may parallelize with PR-Seed/Legacy)

### Task 9: Inventory and delete RTTP surface

- [ ] **Step 1: Generate inventory**

```powershell
rg -i "rttp" --glob "!documents/archive/**" -l > var/log/rttp_delete_inventory.txt
```

- [ ] **Step 2: Delete workflow and spec**

Delete `.github/workflows/rttp-lab-macro-smoke.yml`, `docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md`.

- [ ] **Step 3: Strip replay enums / event_types**

Remove `RTTP_*` from `replay_enums.py`, `event_types.py`, `replay_track_keys.py`. Update `test_replay_event_coverage_matrix.py` and `test_lab_unified_replay_append.py`.

- [ ] **Step 4: Strip lab summary and timeline**

Remove rttp dict branches from `solver_run_lab_summary.py`, `lab_replay_timeline_payload.py`, `solver_runtime_types.py`.

- [ ] **Step 5: Strip UI**

Remove RTTP panels/labels from `asteroid_miner_layout_lab.js`, `asteroid_miner_layout_solver.html`, `public_pages.py` if RTTP-only.

- [ ] **Step 6: Update integration tests**

`tests/integration/web/test_asteroid_run_solver.py` — delete RTTP-specific assertions (keep reconstruction/L2 paths).

- [ ] **Step 7: Locale** — remove orphaned `rttp` msgids via `scripts/build_locale_ko.py` if needed.

---

### Task 10: Token gate (CI)

**Files:**
- Create: `tests/unit/architecture/test_miner_seed_decontamination_tokens.py`
- Create: `scripts/test_miner_seed_decontamination_tokens.ps1`

- [ ] **Step 1: Architecture test wrapping rg**

```python
import subprocess

FORBIDDEN = ("rttp", "GeneTemplate", "pattern_library", "exhaustive_sample_gene")


def test_repo_has_no_forbidden_decontamination_tokens() -> None:
    for token in FORBIDDEN:
        proc = subprocess.run(
            ["rg", "-i", token, "django_apps", "tests", "config", ".github"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines = [ln for ln in proc.stdout.splitlines() if "MinerSeedPattern" not in ln]
        assert proc.returncode != 0 or not lines, f"forbidden token {token!r}:\n" + "\n".join(lines[:20])
```

Adjust: `pattern_library` must not match `MinerSeedPattern` — filter lines where match is exactly `pattern_library` substring (not `MinerSeedPattern`).

- [ ] **Step 2: Full gate**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
```

- [ ] **Step 3: Mark spec/plan CLOSED in `documents/ai/current_plan.md`**

---

## Plan self-review (2026-05-28)

| Spec section | Plan task |
|--------------|-----------|
| §2 coordinate / no x==0 reject | **Task 8A (blocking)**; Task 6 Step 3; Task 8 removes exhaustive assert |
| §4 GeneticSample 14 rows | Tasks 1–2 |
| §5 bootstrap evidence | Task 3 architecture test (reviewer wording) |
| §6 ingest | Task 2 |
| §7 MinerSeedPattern | Tasks 5–7 |
| §8 deletions | Task 8 |
| §9 RTTP | Tasks 9–10 |
| §10 PR order | Parts A→B→C |
| §11 tests | Named in each task |
| Fluid projection not 28 rows | Task 6 |
| rg gate | Task 10 |

**Placeholder scan:** None.

**Blocking amendment (contract review 2026-05-28):** `asteroid_map_coords` world-map `x==0` rejection is legacy RTTP/raw-grid contamination. **PR-Legacy must remove it from all seed/solver-facing paths (Task 8A).** Do not defer until tests fail. Any remaining no-x==0 helper must live in an explicitly named legacy/raw-global module, must not be imported by seed/runtime/solver paths, and must be covered by architecture tests.

**Reviewer status:** APPROVED WITH AMENDMENT — execution may start after Task 8A is in plan (done).

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-28-miner-seed-decontamination.md`.

**Recommended (reviewer + plan): Subagent-Driven** — one fresh subagent per task; mandatory review after Task 8A and before Task 8 deletions (PR-Legacy has delete/rename/coords/migration risk).

**Alternative: Inline Execution** — Part A → B → C in one session with checkpoints after each PR gate.

Default next action unless user objects: **start Part A (PR-Seed) Task 0** via subagent-driven-development.
