# Capacity C-GATE — Complete-Map Capacity Implementation Plan

**Status:** Proposed; execute only after docs PR merge and `current_plan.md` ACTIVE row  
**Spec:** [`../specs/2026-05-28-capacity-c-gate-complete-map-design.md`](../specs/2026-05-28-capacity-c-gate-complete-map-design.md)  
**Track:** v0.1 next-track selection → capacity C-GATE  
**Branch for implementation:** `feat/capacity-c-gate-complete-map`  
**Required workflow:** subagent-driven development or executing-plans; TDD red → green → review per task

---

## Hard constraints

- Do not execute tombstoned plan checklists.
- Do not restore `asteroid_field_cells_from_reconstruction(recon)` as production SoT.
- Do not change route probe, incremental commit, validation repair policy, FOT guards, macro mode, or GA.
- Do not read replay / NDJSON / solver_summary as algorithm input.
- Capacity numbers must come from `ReconstructionCompleteMap`.

---

## Target outcome

```text
ReconstructionCompleteMap.field_cells
  → capacity summary
  → OptimizationInput.mineable_cells
  → Lab summary/UI capacity cards
  → regression gates
```

All production capacity paths should be traceable to the same complete-map field-cell set.

---

## Task 0 — Branch and baseline

**Files:** none

- [ ] Create branch from current `master`.

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/capacity-c-gate-complete-map
```

- [ ] Baseline gates.

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v --tb=short
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
```

Expected: PASS or document pre-existing absence of new C-GATE tests before writing red tests.

---

## Task 1 — Complete-map parity tests

**Files:**

- `tests/unit/asteroid_lab/test_complete_map.py`
- `django_apps/asteroid_lab/reconstruction/complete_map.py`

### Steps

- [ ] Add/verify a test proving `build_reconstruction_complete_map(cleanup, recon).cells` equals merged display cells.
- [ ] Add/verify a test proving `len(complete_map.field_cells)` matches full-map field summary.
- [ ] Add a regression where overlay field count is smaller than complete-map field count on a canon fixture.
- [ ] Ensure `ReconstructionCompleteMap` is frozen and exposes shape/fluid counts.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction/complete_map.py tests/unit/asteroid_lab/test_complete_map.py
```

### Commit

```text
feat(reconstruction): enforce complete-map field-cell parity
```

---

## Task 2 — Field-cell public API cleanup

**Files:**

- `django_apps/asteroid_lab/reconstruction/field_cells.py`
- `tests/unit/asteroid_lab/test_field_cells.py`
- architecture guard test if needed

### Steps

- [ ] Public helpers accept only `ReconstructionCompleteMap`:

```python
asteroid_field_cells_from_complete_map(complete_map)
count_asteroid_field_cells_by_resource(complete_map)
```

- [ ] Remove or privatize overlay/reconstruction-based public helpers.
- [ ] Add tests that reject transport/miner/external void cells.
- [ ] Add architecture guard preventing production code from importing tombstoned overlay helpers.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py tests/unit/architecture/test_optimization_contamination_gates.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/reconstruction/field_cells.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/architecture
```

### Commit

```text
fix(reconstruction): restrict field-cell SoT to complete maps
```

---

## Task 3 — Capacity summary consumes complete map

**Files:**

- `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`
- `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py`

### Steps

- [ ] Change capacity summary API to require `complete_map` or to accept it as the authoritative source.
- [ ] Add test: many complete-map fields + sparse overlay fields still reports complete-map count.
- [ ] Add shape/fluid-specific count tests.
- [ ] Ensure `confirmed_cell_count` legacy JSON keys, if kept, are documented as complete-map field count aliases.
- [ ] Ensure theoretical max uses field count × active rule × 4.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py
```

### Commit

```text
fix(asteroid_lab): capacity summary uses complete-map field counts
```

---

## Task 4 — OptimizationInput mineable cells from complete map

**Files:**

- `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- `tests/unit/asteroid_lab/test_optimization_input_adapter.py`
- `tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py`

### Steps

- [ ] Thread `complete_map` into optimization input creation.
- [ ] Assert `OptimizationInput.mineable_cells == complete_map.field_cells`.
- [ ] Ensure existing trunk / external void topology remains derived from complete-map-compatible topology, not replay.
- [ ] Preserve existing RTTP candidate/commit behavior except changed terrain numerator.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/optimization/reconstruction_adapter.py tests/unit/asteroid_lab/test_optimization_input_adapter.py
```

### Commit

```text
fix(rttp): derive optimization mineable cells from complete map
```

---

## Task 5 — Runtime threading through solver entry

**Files:**

- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `tests/unit/asteroid_lab/test_solver_runtime_entry.py` or existing runtime tests
- `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

### Steps

- [ ] Build complete map once after reconstruction.
- [ ] Pass the same complete-map DTO to capacity summary and optimization input creation.
- [ ] Add spy/regression test proving the same field count reaches summary and RTTP input.
- [ ] Preserve `ASTEROID_LAB_RTTP_ENABLED=False` stub behavior.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
```

### Commit

```text
fix(runtime): thread complete map through capacity and RTTP input
```

---

## Task 6 — Lab/UI capacity observability

**Files:**

- `django_apps/web/templates/web/partials/lab_stat_cards.html`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py`
- `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

### Steps

- [ ] Ensure capacity card labels distinguish theoretical field capacity from committed route-confirmed throughput.
- [ ] Display footprint as field cells / map cells.
- [ ] Ensure resource capacity values come from complete-map-derived summary fields.
- [ ] Add template/string regression tests.

### Gate

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
python -m ruff check django_apps/web/static/web/js/asteroid_miner_layout_lab.js tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py
```

### Commit

```text
feat(web): show complete-map field capacity in Lab cards
```

---

## Task 7 — Contamination and boundary guards

**Files:**

- `tests/unit/architecture/test_optimization_contamination_gates.py`
- `tests/unit/architecture/test_catalog_consumption_boundaries.py`
- optional new `tests/unit/architecture/test_capacity_c_gate_boundaries.py`

### Steps

- [ ] Add AST guard: capacity production modules must not call overlay field-count helper names.
- [ ] Add AST guard: optimization input adapter must not read replay or solver summary.
- [ ] Add guard: validation remains read-only; no route repair from validation.
- [ ] Add guard: tombstoned plans contain no executable status such as `Ready for execution`.

### Gate

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
```

### Commit

```text
test(architecture): guard complete-map capacity boundaries
```

---

## Task 8 — Full verification and docs close

**Files:**

- `documents/ai/current_plan.md`
- `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- this plan and spec

### Steps

- [ ] Run narrow C-GATE gate.

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

- [ ] Run standing reconstruction gate.

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

- [ ] Run standing RTTP gate.

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

- [ ] Run architecture gates.

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
```

- [ ] Update `current_plan.md` from ACTIVE to CLOSED after implementation PR merge.
- [ ] Update roadmap capacity C-GATE row with PR and merge SHA.

### Commit

```text
docs(capacity): close C-GATE implementation track
```

---

## Self-review checklist

- [ ] No macro code or macro tests changed unless strictly incidental and justified.
- [ ] No GA / full evolutionary search work.
- [ ] No validation repair.
- [ ] No replay-as-input.
- [ ] No route probe / commit algorithm changes.
- [ ] Capacity and optimization use the same `ReconstructionCompleteMap.field_cells` set.
- [ ] Tombstoned plans remain non-executable.
- [ ] `current_plan.md` and roadmap match before merge.
