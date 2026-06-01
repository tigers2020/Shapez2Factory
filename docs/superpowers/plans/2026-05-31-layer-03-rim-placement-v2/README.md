# Layer 03 Rim Placement v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a from-scratch Layer 03 rim placement algorithm that consumes DB gene samples via a hexagonal `GeneCatalogSnapshot` boundary and uses a two-phase hybrid (deterministic candidate pool + immediate route probe, then a deterministic beam selector) to emit route-feasible provisional rim placements.

**Architecture:** DB `GeneticSample` is read only at a Django adapter and serialized into a JSON `GeneCatalogSnapshot`, carried to the pure CLI/core via a `--gene-catalog` file (mirroring `--snapshot` game data). Core Layer 03 enumerates rim candidates deterministically, probes routes to L2 trunk connectors, then a deterministic beam selector picks an overlap-free, throughput-maximizing subset, finalized by a commit-time route re-probe.

**Tech Stack:** Python 3.12, hexagonal `src/shapez2_factory/`, Django adapters `django_apps/asteroid_lab/`, pytest, ruff, mypy, black.

**Spec:** [`docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md`](../../specs/2026-05-31-layer-03-rim-placement-v2-design.md) (APPROVED).

**Scope of this checklist:** Phase A (wiring) → Phase B (candidates) → Phase C1 (deterministic beam, v2 MVP) → Phase D (finalize) → Phase E (tests/benchmark). **Deferred (not in this checklist):** Phase C2 local search, Phase C3 GA-lite.

**Approval gate:** No production code until this checklist is approved.

**Verification (full gate, run at PR):** `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`. Narrow loop: `python -m pytest <path>` (no `-q`/`--quiet`/`--tb=no`).

---

## File structure

Create:
- `src/shapez2_factory/adapters/asteroid_lab/gene_catalog_snapshot.py` — core `GeneCatalogSnapshot.from_payload` DTO (no ORM).
- `django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py` — ORM → snapshot serializer.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py` — rim anchor enumeration.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py` — footprint projection + geometry validation + route probe → pool.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py` — deterministic beam selection + fitness.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/finalize.py` — commit-time re-probe → committed placements.

Modify:
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py` — `Layer03SkipReason` enum additions.
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py` — orchestrate phases.
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`, `stack_runner.py` — thread `gene_catalog`.
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` — `--gene-catalog` arg + threading + artifact persist.
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` — `gene_catalog` field + `--gene-catalog`.
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` — build + inject snapshot.

Tests:
- `tests/unit/asteroid_lab/layers/` and `tests/unit/asteroid_lab/` per task.

---

## Phase A — DB to CLI gene wiring

### Task A0: Add gene-catalog skip reasons (enum)

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py:49-55`
- Test: `tests/unit/asteroid_lab/layers/test_layer03_skip_reason_gene_catalog.py`

- [ ] **Step 1: Write the failing test**

```python
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason


def test_gene_catalog_skip_reasons_exist():
    assert Layer03SkipReason.MISSING_GENE_CATALOG.value == "missing_gene_catalog"
    assert Layer03SkipReason.INVALID_GENE_CATALOG.value == "invalid_gene_catalog"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer03_skip_reason_gene_catalog.py -v`
Expected: FAIL (`AttributeError: MISSING_GENE_CATALOG`).

- [ ] **Step 3: Add the enum members**

```python
class Layer03SkipReason(StrEnum):
    NONE = "none"
    MISSING_EXTERIOR_CONNECTION_PLAN = "missing_exterior_connection_plan"
    NO_ROUTE_GOALS = "no_route_goals"
    EMPTY_MINER_SEED_CATALOG = "empty_miner_seed_catalog"
    BUDGET_EXHAUSTED = "budget_exhausted"
    ALGORITHM_RESET = "algorithm_reset"
    MISSING_GENE_CATALOG = "missing_gene_catalog"
    INVALID_GENE_CATALOG = "invalid_gene_catalog"
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer03_skip_reason_gene_catalog.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** — `feat(l3): add gene-catalog skip reasons`

---

### Task A1: Core `GeneCatalogSnapshot` DTO (no ORM)

Mirror [`json_snapshot_rules.py`](../../../../src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py). Schema per spec §G.

**Files:**
- Create: `src/shapez2_factory/adapters/asteroid_lab/gene_catalog_snapshot.py`
- Test: `tests/unit/asteroid_lab/test_gene_catalog_snapshot.py`

- [ ] **Step 1: Write failing tests**

```python
import pytest

from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import (
    GeneCatalogSnapshot,
    GeneCatalogInvalid,
)


def _valid_payload():
    return {
        "schema_version": "gene_catalog_v1",
        "generated_at": "2026-05-31T00:00:00Z",
        "provenance_hash": "abc123",
        "source_batch_id": "exhaustive_sample_gene_v1",
        "deterministic_sort_key": "by_gene_id_then_throughput_desc",
        "entries": [
            {
                "gene_id": "m3e_01",
                "resource_kind": "both",
                "canonical_output_dir": "E",
                "occupied_offsets": [[0, 0], [-1, 0], [-2, 0], [-3, 0]],
                "extractor_offset": [0, 0],
                "extension_offsets": [[-1, 0], [-2, 0], [-3, 0]],
                "output_stub_offset": [1, 0],
                "route_probe_start_offset": [2, 0],
                "throughput_factor": 16,
                "topology_signature_base": "m3e_01_base",
            }
        ],
    }


def test_from_payload_roundtrip():
    snap = GeneCatalogSnapshot.from_payload(_valid_payload())
    assert snap.schema_version == "gene_catalog_v1"
    assert len(snap.entries) == 1
    assert snap.entries[0].gene_id == "m3e_01"
    assert snap.entries[0].canonical_output_dir == "E"
    assert snap.entries[0].throughput_factor == 16


def test_unsupported_schema_rejected():
    payload = _valid_payload()
    payload["schema_version"] = "gene_catalog_v999"
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_missing_canonical_output_dir_rejected():
    payload = _valid_payload()
    del payload["entries"][0]["canonical_output_dir"]
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_bad_throughput_factor_rejected():
    payload = _valid_payload()
    payload["entries"][0]["throughput_factor"] = 5
    with pytest.raises(GeneCatalogInvalid):
        GeneCatalogSnapshot.from_payload(payload)


def test_empty_entries_is_valid_but_has_no_usable_genes():
    payload = _valid_payload()
    payload["entries"] = []
    snap = GeneCatalogSnapshot.from_payload(payload)
    assert snap.entries == ()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_gene_catalog_snapshot.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement the adapter**

```python
"""``GeneCatalogSnapshot`` — core gene allele catalog from a frozen JSON snapshot (no ORM)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

SUPPORTED_SCHEMA_VERSIONS = frozenset({"gene_catalog_v1"})
VALID_THROUGHPUT_FACTORS = frozenset({4, 8, 12, 16})
VALID_RESOURCE_KINDS = frozenset({"shape", "fluid", "both"})


class GeneCatalogIssue(StrEnum):
    MISSING = "missing"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    MALFORMED = "malformed"


class GeneCatalogInvalid(Exception):
    def __init__(self, issue: GeneCatalogIssue, message: str) -> None:
        self.issue = issue
        super().__init__(f"{issue.value}: {message}")


@dataclass(frozen=True, slots=True)
class GeneCatalogEntry:
    gene_id: str
    resource_kind: str
    canonical_output_dir: str
    occupied_offsets: tuple[tuple[int, int], ...]
    extractor_offset: tuple[int, int]
    extension_offsets: tuple[tuple[int, int], ...]
    output_stub_offset: tuple[int, int]
    route_probe_start_offset: tuple[int, int]
    throughput_factor: int
    topology_signature_base: str


@dataclass(frozen=True, slots=True)
class GeneCatalogSnapshot:
    schema_version: str
    generated_at: str
    provenance_hash: str
    source_batch_id: str
    deterministic_sort_key: str
    entries: tuple[GeneCatalogEntry, ...]

    @classmethod
    def from_payload(cls, payload: object) -> GeneCatalogSnapshot:
        if not isinstance(payload, dict):
            raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, "payload must be a JSON object")
        schema_version = payload.get("schema_version")
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise GeneCatalogInvalid(
                GeneCatalogIssue.UNSUPPORTED_SCHEMA,
                f"schema_version {schema_version!r} not in {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, "entries must be a list")
        entries = tuple(_parse_entry(e) for e in raw_entries)
        return cls(
            schema_version=str(schema_version),
            generated_at=str(payload.get("generated_at", "")),
            provenance_hash=str(payload.get("provenance_hash", "")),
            source_batch_id=str(payload.get("source_batch_id", "")),
            deterministic_sort_key=str(payload.get("deterministic_sort_key", "")),
            entries=entries,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> GeneCatalogSnapshot:
        file_path = Path(path)
        if not file_path.is_file():
            raise GeneCatalogInvalid(GeneCatalogIssue.MISSING, f"file not found: {file_path}")
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, f"invalid JSON: {exc}") from exc
        return cls.from_payload(payload)


def _coord(value: object) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, f"bad offset {value!r}")
    try:
        return (int(value[0]), int(value[1]))
    except (TypeError, ValueError) as exc:
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, f"bad offset {value!r}") from exc


def _parse_entry(raw: object) -> GeneCatalogEntry:
    if not isinstance(raw, dict):
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, "entry must be an object")
    if "canonical_output_dir" not in raw:
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, "entry missing canonical_output_dir")
    output_dir = str(raw["canonical_output_dir"])
    if output_dir != "E":
        raise GeneCatalogInvalid(
            GeneCatalogIssue.MALFORMED, f"canonical_output_dir must be 'E', got {output_dir!r}"
        )
    resource_kind = str(raw.get("resource_kind", ""))
    if resource_kind not in VALID_RESOURCE_KINDS:
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, f"bad resource_kind {resource_kind!r}")
    try:
        throughput_factor = int(raw["throughput_factor"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GeneCatalogInvalid(GeneCatalogIssue.MALFORMED, "bad throughput_factor") from exc
    if throughput_factor not in VALID_THROUGHPUT_FACTORS:
        raise GeneCatalogInvalid(
            GeneCatalogIssue.MALFORMED, f"throughput_factor {throughput_factor} not allowed"
        )
    return GeneCatalogEntry(
        gene_id=str(raw["gene_id"]),
        resource_kind=resource_kind,
        canonical_output_dir=output_dir,
        occupied_offsets=tuple(_coord(c) for c in raw.get("occupied_offsets", [])),
        extractor_offset=_coord(raw.get("extractor_offset", [0, 0])),
        extension_offsets=tuple(_coord(c) for c in raw.get("extension_offsets", [])),
        output_stub_offset=_coord(raw.get("output_stub_offset", [1, 0])),
        route_probe_start_offset=_coord(raw.get("route_probe_start_offset", [2, 0])),
        throughput_factor=throughput_factor,
        topology_signature_base=str(raw.get("topology_signature_base", "")),
    )


__all__ = [
    "GeneCatalogEntry",
    "GeneCatalogInvalid",
    "GeneCatalogIssue",
    "GeneCatalogSnapshot",
    "SUPPORTED_SCHEMA_VERSIONS",
]
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/test_gene_catalog_snapshot.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Lint + commit** — `ruff check src/shapez2_factory/adapters/asteroid_lab/gene_catalog_snapshot.py` then `feat(l3): add core GeneCatalogSnapshot DTO`.

---

### Task A2: Django serializer `build_gene_catalog_snapshot`

Reuses [`load_gene_templates_from_genetic_samples`](../../../../django_apps/asteroid_lab/services/genetic_sample_gene_export.py); extend to include `miner_seed_*` keys (separate loader path since exhaustive cache lacks them). Output is a pure dict matching the `gene_catalog_v1` schema, with entries sorted by `(gene_id, -throughput_factor)`.

**Files:**
- Create: `django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py`
- Test: `tests/unit/asteroid_lab/test_genetic_sample_catalog_snapshot.py` (uses `@pytest.mark.django_db`)

- [ ] **Step 1: Write the failing test**

```python
import pytest

from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
    build_gene_catalog_snapshot,
)
from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import GeneCatalogSnapshot


@pytest.mark.django_db
def test_snapshot_roundtrips_through_core_dto(seed_one_exhaustive_gene):
    payload = build_gene_catalog_snapshot(GeneticSample.objects.all())
    assert payload["schema_version"] == "gene_catalog_v1"
    snap = GeneCatalogSnapshot.from_payload(payload)
    assert len(snap.entries) >= 1
    assert all(e.canonical_output_dir == "E" for e in snap.entries)


@pytest.mark.django_db
def test_empty_queryset_yields_zero_entries():
    payload = build_gene_catalog_snapshot(GeneticSample.objects.none())
    assert payload["entries"] == []
    snap = GeneCatalogSnapshot.from_payload(payload)
    assert snap.entries == ()


@pytest.mark.django_db
def test_entries_deterministically_sorted(seed_two_genes):
    payload = build_gene_catalog_snapshot(GeneticSample.objects.all())
    gene_ids = [e["gene_id"] for e in payload["entries"]]
    assert gene_ids == sorted(gene_ids)
```

(Define `seed_one_exhaustive_gene` / `seed_two_genes` fixtures using the existing seed command helpers in `tests/unit/asteroid_lab/conftest.py`.)

- [ ] **Step 2: Run to verify it fails** — `python -m pytest tests/unit/asteroid_lab/test_genetic_sample_catalog_snapshot.py -v` → FAIL (module missing).

- [ ] **Step 3: Implement the serializer**

```python
"""ORM -> GeneCatalogSnapshot payload serializer (adapter boundary; ORM allowed here only)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from django.db.models import QuerySet

from django_apps.asteroid_lab.genetic_sample.gene_template import GeneTemplate
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    load_gene_templates_from_genetic_samples,
)

SCHEMA_VERSION = "gene_catalog_v1"
SORT_KEY = "by_gene_id_then_throughput_desc"


def _entry_from_template(t: GeneTemplate) -> dict[str, Any]:
    return {
        "gene_id": t.gene_id,
        "resource_kind": "both",
        "canonical_output_dir": t.output_dir.value if hasattr(t.output_dir, "value") else "E",
        "occupied_offsets": sorted([o[0], o[1]] for o in t.occupied_offsets),
        "extractor_offset": list(t.extractor_offset),
        "extension_offsets": [list(o) for o in t.extension_offsets],
        "output_stub_offset": list(t.fixed_output_transport_offset),
        "route_probe_start_offset": list(t.route_probe_start_offset),
        "throughput_factor": int(t.throughput_factor),
        "topology_signature_base": t.topology_signature_base,
    }


def build_gene_catalog_snapshot(
    queryset: QuerySet[GeneticSample],
    *,
    source_batch_id: str = "exhaustive_sample_gene_v1",
) -> dict[str, Any]:
    templates, _skipped, _errors = load_gene_templates_from_genetic_samples(queryset)
    entries = sorted(
        (_entry_from_template(t) for t in templates),
        key=lambda e: (e["gene_id"], -e["throughput_factor"]),
    )
    provenance_hash = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "provenance_hash": provenance_hash,
        "source_batch_id": source_batch_id,
        "deterministic_sort_key": SORT_KEY,
        "entries": entries,
    }


__all__ = ["SCHEMA_VERSION", "SORT_KEY", "build_gene_catalog_snapshot"]
```

> NOTE: if the catalog must include `miner_seed_*` rows (gene_key not in exhaustive cache), extend `load_gene_templates_from_genetic_samples` (or add a sibling loader) in a sub-step before this task. Track as Task A2b if needed; do not silently drop those rows.

- [ ] **Step 4: Run to verify it passes** — same command → PASS.

- [ ] **Step 5: Lint + commit** — `feat(l3): add Django gene-catalog snapshot serializer`.

---

### Task A3: Carry `gene_catalog` through subprocess + CLI + use case

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (`SolverSubprocessRequest`, `_write_inputs`, `build_solver_cli_args`)
- Modify: `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (`run` parser, `_run_artifact`, artifact persist)
- Modify: `src/shapez2_factory/application/asteroid_lab/run_stack.py` (`RunStackUseCase.run` accepts `gene_catalog`)
- Modify: `src/shapez2_factory/application/asteroid_lab/stack_runner.py` (thread to L3 runner)
- Test: `tests/unit/asteroid_lab/test_cli_gene_catalog_threading.py`, `tests/unit/asteroid_lab/test_solver_subprocess_gene_catalog_args.py`

- [ ] **Step 1: Write failing tests** (CLI arg presence + use-case threading)

```python
from pathlib import Path

from django_apps.asteroid_lab.services.solver_subprocess_runner import (
    SolverSubprocessRequest,
    build_solver_cli_args,
)


def test_cli_args_include_gene_catalog(tmp_path: Path):
    req = SolverSubprocessRequest(
        run_key="k1",
        copy_code="SHAPEZ2-4-x",
        game_data_snapshot={"schema_version": "game_data_snapshot_v1"},
        gene_catalog={"schema_version": "gene_catalog_v1", "entries": []},
        artifact_root=tmp_path,
        allowed_root=tmp_path,
        timeout_seconds=5.0,
    )
    args = build_solver_cli_args(
        req, copy_path=tmp_path / "c.txt", snapshot_path=tmp_path / "s.json"
    )
    assert "--gene-catalog" in args
```

- [ ] **Step 2: Run to verify it fails** — FAIL (`TypeError: unexpected keyword 'gene_catalog'`).

- [ ] **Step 3: Implement threading**

In `solver_subprocess_runner.py`: add `gene_catalog: dict[str, Any] = field(default_factory=dict)` to `SolverSubprocessRequest`; in `_write_inputs` write `gene_catalog.json`; in `build_solver_cli_args` append `["--gene-catalog", str(gene_catalog_path)]` (thread the path through both functions).

In `asteroid_solve.py`: add `run.add_argument("--gene-catalog", dest="gene_catalog", type=Path, default=None)`; in `_run_artifact` parse via `GeneCatalogSnapshot.from_payload(json.loads(...))` when provided (else `None`), pass `gene_catalog=...` to `RunStackUseCase.run`; `writer.write_output("input/gene_catalog.json", ...)` and add manifest `paths["gene_catalog"] = "input/gene_catalog.json"`.

In `run_stack.py`: `def run(self, *, copy_text, throughput_target_percent=80, budget_ms=..., speed_tier=1, gene_catalog: GeneCatalogSnapshot | None = None)`; pass into the L3 runner partial.

In `stack_runner.py`: bind L3 runner to `partial(run_layer_03_rim_greedy_placement, gene_catalog=gene_catalog)` (keyword), keeping the existing per-slug wiring.

- [ ] **Step 4: Run to verify it passes** — PASS.

- [ ] **Step 5: Commit** — `feat(l3): thread gene_catalog through subprocess, CLI, use case`.

---

### Task A4: Inject snapshot from Django runtime entry

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_solver_runtime_entry_gene_catalog.py`

- [ ] **Step 1: Write failing test** — assert `run_solver_runtime_for_project` builds a `SolverSubprocessRequest` whose `gene_catalog["schema_version"] == "gene_catalog_v1"` (patch the subprocess runner to capture the request).

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3:** In `solver_runtime_entry.py`, call `build_gene_catalog_snapshot(GeneticSample.objects.all())` and pass it as `gene_catalog=` when constructing `SolverSubprocessRequest`.

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): inject DB gene catalog into solver subprocess request`.

---

### Task A5: Missing/invalid catalog skip behavior in L3 (spec §M)

**Files:**
- Modify: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_gene_catalog_gate.py`

- [ ] **Step 1: Write failing tests**

```python
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
# build complete_map + non-None exterior_plan via existing fixtures


def test_missing_gene_catalog_returns_skip(complete_map, exterior_plan, budget_ctx):
    result = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=budget_ctx,
        gene_catalog=None,
    )
    assert result.committed_placements == ()
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_GENE_CATALOG.value


def test_empty_gene_catalog_returns_skip(complete_map, exterior_plan, budget_ctx, empty_catalog):
    result = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=budget_ctx,
        gene_catalog=empty_catalog,
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_GENE_CATALOG.value
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3:** Add `gene_catalog: GeneCatalogSnapshot | None = None` to `run_layer_03_rim_greedy_placement`. After the `exterior_plan is None` gate, add: if `gene_catalog is None or not gene_catalog.entries: return build_empty_integrated_rim_greedy_result(layer_skip_reason=Layer03SkipReason.MISSING_GENE_CATALOG.value, rim_anchor_count=0)`. Keep `ALGORITHM_RESET` return only until Phase B replaces it. **Never** read DB; **never** synthesize genes (spec M3).

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): gate L3 on missing/empty gene catalog`.

---

## Phase B — Candidate generation + immediate route probe

### Task B1: Rim anchor scan

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py`
- Test: `tests/unit/asteroid_lab/layers/test_rim_anchor_scan.py`

- [ ] **Step 1: Write failing test** — given a small `ReconstructionCompleteMap` fixture, assert `scan_rim_anchors(complete_map)` returns field cells adjacent to external void, each with non-empty `void_dirs`, ordered by `(row, col)` in the canonical solver frame (spec D1).

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `scan_rim_anchors(complete_map) -> tuple[RimAnchor, ...]` where `RimAnchor` is a frozen dataclass `(coord: tuple[int,int], field_kind: str, void_dirs: tuple[str, ...])`. Coordinates come from `complete_map.field_cells` / `external_void_cells` (canonical solver frame — no dense/screen projection). Sort by `(coord[0], coord[1])`.

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): rim anchor scan in solver frame`.

### Task B2: Candidate generation + geometry validation + route probe

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- Test: `tests/unit/asteroid_lab/layers/test_candidate_gen.py`

- [ ] **Step 1: Write failing tests** covering spec R2/R3/R4/R5/D1:
  - equipment cells ⊆ matching-resource field;
  - output stub ⊆ external void;
  - only route-feasible candidates (immediate probe success) enter the normal pool;
  - candidate ordering equals `(anchor_row, anchor_col, output_dir_rank, -throughput_factor, gene_id)` in solver frame.

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `generate_candidates(complete_map, exterior_plan, gene_catalog, anchors) -> RimBundleCandidateSet`: for each `(anchor, entry, output_dir in anchor.void_dirs)`, orient the canonical-E footprint to `output_dir`, project onto the map, validate geometry (R2/R3), run `immediate_route_probe`/`weighted_route_probe` (`shared/route_probe.py`) from `route_probe_start` to the nearest matching trunk goal from `exterior_plan`. Success → `normal_candidates`; failure → diagnostic rejects. Emit candidates in the D1 order. No commit (R6).

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): rim candidate generation with immediate route probe`.

---

### Task B2.1: Footprint transform contract — full-footprint D4 (spec §T / Amendment 6)

The earlier candidate gen oriented the bundle by rotating the footprint to face each `void_dir`
with a single shared rotation. Amendment 6 mandates a **full-footprint D4** model with **independent
extractor output**. Implement incrementally; each sub-step is its own red→green→commit.

**Files:**
- Modify: `.../layer_03_rim_greedy_placement/candidate_gen.py` (transform helpers + enumeration)
- Maybe create: `.../layer_03_rim_greedy_placement/footprint_transform.py` (`rotate_xy`, `rotate_r`, `mirror_x/y`, `enumerate_d4`, `normalize_footprint`)
- Test: `tests/unit/asteroid_lab/layers/test_candidate_gen.py`, `test_footprint_transform.py`

- [x] **B2.1a — rotation `R` field fix (T4):** placement `rotation` = `edge_rotation_k(edge)` (East=0, CW+1), NOT `output_dir_rank` (NESW). Lock T5 vectors + R-only-invalid (T2). **DONE** (commit `8338099b`).
- [x] **B2.1b — D4 enumeration (T1/T3/T6):** `footprint_transform.py` with `rotate_xy`/`rotate_r`/`mirror_xy`/`mirror_r` + `enumerate_d4` (dedup after full normalization). **DONE** (commit `63591ee0`). Straight line → 4, corner → 8.
- [x] **B2.1c-0 — golden fixture geometry audit (read-only):** stage-count audit before any rewrite. **DONE** (see table below). Only `test_candidate_gen.py` calls `generate_candidates`; replay/assembler tests use the golden map fixture but not the generator.
- [ ] **B2.1c-1 — wire `enumerate_d4` only** into `generate_candidates` (keep existing single output rule). Acceptance: straight dedup class held, per-placement R applied, no R-only rotation. Failures explained by stage table, not patched by tweaking filters.
- [ ] **B2.1c-2 — independent extractor output (T7):** enumerate extractor output faces independently; reject extension-blocked + non-void faces; miner `R = output_side_k`, extension `R = orientation_k` (per-placement R differs). **Dedup D4 by extension layout only — extractor `R` is independent** (see audit finding). Keep D4 wiring and output rewrite in **separate commits**.
- [ ] **B2.1c-3 — golden test reclassification:** replace legacy exact-count assertions with **stage-count breakdown** (canonical → D4 → deduped → boundary → output-face → route → final). No blind `old_count → new_count` swap.
- [ ] **B2.1d — dedup metric + D1 ordering:** `dedupe_duplicate_count` reflects normalization dedups; D1 ordering sorts by `(anchor_row, anchor_col, output_dir_rank, -throughput_factor, gene_id)` with `output_dir` = independent output side (stable sort preserves orientation tiebreak).

> Expansion stays in **core B2** (T6); the Django serializer/snapshot keeps canonical-East 18 entries only.

#### B2.1c-0 Golden Fixture Audit (catalog = test `m3e`+`m0e`; golden 5×5, goal `(8,4)`)

| stage | m3e | m0e | total | note |
|-------|----:|----:|------:|------|
| canonical patterns | 1 | 1 | 2 | DB row count (test catalog = 2; real DB = 18) |
| D4 expanded (current key, incl. extractor R) | 4 | 4 | 8 | `enumerate_d4` as committed in B2.1b |
| D4 deduped (extension-only key) | 4 | 1 | 5 | **finding:** single-cell/symmetric genes over-enumerate when extractor R is in the key |
| boundary survivors (equipment ⊆ field) | 28 | 16 | 44 | ext-only dedup, all 16 rim anchors |
| output-face survivors (void-facing, unblocked) | 36 | 20 | 56 | independent faces |
| route survivors (BFS start→`(8,4)`) | 1 | 1 | **2** | only `(6,4)`-East: `route_probe_start = +2` lands in void exclusively at `(8,4)` |

**Findings:**
- The legacy golden count (`len == 2`, both `(6,4)` East, keys `[m3e, m0e]`) **stays valid as a contract-backed count** — the `route_probe_start = +2` void constraint admits only `(6,4)`-East on a convex 5×5 — **iff** D4 dedup uses the **extension-only key**. With the current B2.1b key (incl. extractor R) the pool is **5** (m0e duplicated ×4 by extractor R). So B2.1c-2 must dedup by extension layout (extractor `R` is independent per T7); `enumerate_d4` needs an extractor-R-independent dedup path.

**Test classification (`test_candidate_gen.py`):**

| test | class | action |
|------|-------|--------|
| `test_rotate_*` (3), `test_output_dir_rank_is_nesw`, `test_edge_rotation_k_*`, `test_*_r_not_nesw_rank_t4`, `test_rotation_transforms_coordinates_not_r_only_t2` | contract invariant (transform math, T2/T4/T5) | keep |
| `test_normal_pool_equipment_in_matching_field_r2` | contract invariant (R2) | keep |
| `test_normal_pool_output_stub_in_external_void_r3` | contract invariant (R3) | keep |
| `test_only_route_feasible_candidates_enter_normal_pool_r5` | route-feasibility invariant | keep (diagnostics non-empty should still hold) |
| `test_candidate_enumeration_order_equals_d1_sort_key` | ordering assertion (D1) | keep (stable sort) |
| `test_metrics_counts_match_pools` | relational invariant | keep |
| `test_golden_normal_pool_is_the_single_aligned_anchor` | **legacy exact count** (len==2, keys, dir) | convert to stage-count breakdown (B2.1c-3); value 2 remains but justified by the audit table |

---

## Phase C1 — Deterministic beam selector (v2 MVP)

### Task C1: Fitness + beam selection

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py`
- Test: `tests/unit/asteroid_lab/layers/test_beam_selector.py`

- [ ] **Step 1: Write failing tests**:
  - fitness = `Σ throughput_factor − route_fragility_penalty − shared_corridor_pressure_penalty`;
  - selected subset has **zero** equipment-cell overlaps (hard constraint);
  - **selector consults fitness/conflict state** — given two candidates at conflicting cells, the higher-fitness one is committed regardless of enumeration order (spec D2: prove score-driven choice, not literal order inequality);
  - deterministic: same inputs → identical selected `gene_id` sequence.

```python
def test_selector_prefers_higher_fitness_on_conflict(conflicting_pool_low_first):
    selected = select_beam(conflicting_pool_low_first, beam_width=4)
    # high-throughput candidate wins even though it is enumerated last
    assert selected[0].gene_id == "m3e_01"


def test_selected_placements_have_no_overlap(dense_pool):
    selected = select_beam(dense_pool, beam_width=8)
    cells = [c for cand in selected for c in cand.mining_occupied_cells]
    assert len(cells) == len(set(cells))
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `select_beam(candidate_set, *, beam_width: int) -> tuple[SelectedCandidate, ...]`: maintain top-`beam_width` partial selections ranked by fitness; expand by adding the next non-conflicting candidate (conflict = shared equipment/reserved cell); break ties by `(-fitness, gene_id, anchor)` for determinism. Return the best full selection. Penalties computed from probe `route_cost` and per-void-corridor usage counts.

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): deterministic beam selector with fitness`.

---

## Phase D — Finalize (commit-time re-probe)

### Task D1: Finalize selected placements

**Files:**
- Create: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/finalize.py`
- Modify: `.../layer_03_rim_greedy_placement/run.py` (orchestrate B → C1 → D)
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_finalize.py`, `tests/unit/asteroid_lab/layers/test_layer_03_run_v2.py`

- [ ] **Step 1: Write failing tests**:
  - re-probe on the latest `route_domain` (`RouteDomainSnapshotBuilder.build_snapshot`) drops a placement whose route is blocked by an earlier committed placement;
  - survivors populate `IntegratedRimGreedyResult.committed_placements` + overlay + metrics;
  - end-to-end `run_layer_03_rim_greedy_placement` with a valid `gene_catalog` returns non-empty `committed_placements` and `invalid_overlap_count == 0`.

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `finalize_placements(selected, complete_map, exterior_plan) -> tuple[CommittedRimSeedPlacement, ...]`: iterate selected in selection order; for each, build the latest route domain via `RouteDomainSnapshotBuilder.build_snapshot` (treating already-finalized equipment as hard blockers), re-probe; keep on success, drop on failure (R7). Wire `run.py` to call B → C1 → D and assemble the result with metrics + observability events (reuse existing builders; produce BEGIN/COMPLETE events).

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `feat(l3): finalize via commit-time re-probe; wire L3 v2 run`.

---

## Phase E — Tests, benchmark, gates

### Task E1: Determinism + architecture gate

**Files:**
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_determinism.py`
- Test (extend): `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` or a new `test_layer03_core_no_orm.py`

- [ ] **Step 1: Write tests**: same `(complete_map, exterior_plan, gene_catalog, seed)` → identical output hash (D4); core L3 modules import no `django`/ORM (grep-style import assertion).

- [ ] **Step 2: Run → FAIL/PASS as appropriate; fix.**

- [ ] **Step 3: Commit** — `test(l3): determinism + core no-ORM gate`.

### Task E2: L3-rim-only golden benchmark (spec Amendment 5)

**Files:**
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_golden_benchmark.py`
- Fixtures: [`tests/fixtures/asteroid_lab/golden_map_origin.txt`](../../../../tests/fixtures/asteroid_lab/golden_map_origin.txt), [`golden_map_result.txt`](../../../../tests/fixtures/asteroid_lab/golden_map_result.txt)

- [ ] **Step 1: Write the benchmark test** measuring L3-rim-only metrics on the golden origin:

```python
def test_l3_rim_benchmark_metrics(golden_origin_complete_map, golden_exterior_plan, full_gene_catalog):
    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_origin_complete_map,
        exterior_plan=golden_exterior_plan,
        budget_ctx=...,
        gene_catalog=full_gene_catalog,
    )
    metrics = compute_rim_benchmark(result)
    assert metrics.invalid_overlap_count == 0
    assert metrics.route_feasible_output_count == metrics.committed_rim_placement_count
    assert metrics.routed_rim_throughput <= GOLDEN_TOTAL_THROUGHPUT  # upper-bound sanity
    assert metrics.routed_rim_throughput >= BEAM_BASELINE_THROUGHPUT  # non-regression floor
    assert metrics.deterministic_output_hash == compute_rim_benchmark(rerun(...)).deterministic_output_hash
```

**Forbidden assertions (must NOT appear):** `result == golden_map_result`; `routed_rim_throughput == GOLDEN_TOTAL_THROUGHPUT`.

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `compute_rim_benchmark(result)` helper returning the metric dataclass; derive `GOLDEN_TOTAL_THROUGHPUT` from decoding the golden result fixture (miners × throughput_factor); set `BEAM_BASELINE_THROUGHPUT` to the first measured beam value (record in the test as a constant).

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `test(l3): L3-rim-only golden benchmark metrics`.

### Task E3: Full gate

- [ ] Run `ruff check .`, `mypy django_apps config src`, `black --check .`, `python -m pytest tests/unit/asteroid_lab/`. Fix failures; commit fixes.

---

## Self-review checklist (run before requesting approval)

- [ ] Every spec section maps to a task: §G→A1/A2, §M→A0/A5, §R→B1/B2/D1, §D→B2/C1/E1, Phase staging→C1 (C2/C3 deferred), benchmark→E2.
- [ ] No placeholders: each code step shows real code or exact modify instructions.
- [ ] Type/name consistency: `GeneCatalogSnapshot`, `Layer03SkipReason.MISSING_GENE_CATALOG/INVALID_GENE_CATALOG`, `gene_catalog` kwarg, `select_beam`, `finalize_placements`, `compute_rim_benchmark` used consistently.
- [ ] Forbidden shortcuts honored: no ORM in core, candidate ≠ commit, enumeration-shortcut ban (D2), commit-time re-probe canonical, no golden-equality assertion.

## Deferred (separate future checklist)

- Phase C2 — bounded deterministic local search over anchor-indexed genome.
- Phase C3 — bounded seed-stable GA-lite (only after C1/C2 baselines exist).
