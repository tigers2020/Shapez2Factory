# boundary-m-repack PR-B — Execution Checklist

**Design (SoT):** [`../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md)
**Plan:** [`README.md`](README.md)

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[-]` skipped (document reason).

---

## Phase 1 — Audit (no code change)

- [x] A1 — decoded `m3e_01` topology = linear inward chain (`branch_count == 0`); straight-chain design confirmed
- [x] A2 — priority direction confirmed = codebase convention; rank/score mismatch flagged as follow-up
- [x] A3 — acceptance → test traceability mapping built

## Phase 2 — Tests first (red)

- [x] T1 — acceptance file `test_layer_03_boundary_m_repack_acceptance.py` (layout / degrade / run / domain / stack locks)
- [x] T2 — deep + shallow rim fixtures `fixtures/layer_03_deep_rim_map.py`
- [x] T3 — confirmed red/green split for the right reasons (9 red m3e behavior / 5 green locks), ruff clean

## Phase 3 — Implementation (red → green)

- [x] I1 — `layout_seed_at_anchor(extension_count)`: straight inward chain, degrade 3→2→1, reject at 0
- [x] I2 — `DEFAULT_GREEDY_SEEDS` = single `m3e_01` (ext3); in-layout degradation; default lock test
- [x] I3 — `greedy_pass1` / `greedy_pass2` pass `seed.extension_count`; full footprint reservation; score/`_hard_fail` hold
- [x] I4 — append N-safe; fixed replay chained-extension rotation (`_parent_coord_for_extension`) + regression test

## Phase 4 — Gates

- [x] G-A — `python -m pytest tests/unit/asteroid_lab/layers/ -v` — passed
- [x] G-A+ — `python -m pytest tests/unit/asteroid_lab/replay/ -v` — passed (replay regression)
- [x] G-A combined — `python -m pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/replay/` — 173 passed, 2 warnings
- [x] G-lint — ruff (changed modules) + black (changed test/fixture) — clean
- [x] G-type — mypy (changed L3 + replay modules) — Success, 13 files (repo-wide mypy NOT claimed)

## Phase 5 — Docs

- [x] D1 — design spec authored
- [x] D2 — this plan folder (README + checklist)
- [x] D3 — PR-CLI-2e gate doc + CLI-first checklist PR-CLI-2e block updated with Gate A evidence
- [x] D4 — `current_plan.md` ACTIVE row added

## Phase 6 — Gate C smoke (evidence only)

Constraints (per reviewer):
- Setting changes via per-command env override only.
- Do not depend on incidental local-DB slugs; use a deterministic fixture slug or record "not reproducible".
- Smoke output is evidence only; never reused as solver/algorithm input.

### Findings (2026-05-30)

- `ASTEROID_LAB_LAYER_02_SOLVER_ENABLED = True` is already the project default (`config/settings.py`).
  The settings comment ("L3–L5 not run") is **stale**: `run_layer02_solver_for_project` DOES run
  `run_layer_03_rim_greedy_placement` (L3) and merges the rim stack into the solver summary +
  `var/log/asteroid_lab_layer_stack/`. So the run-solver path exercises the new m3e_01 default.
- **No deterministic project fixture slug exists.** `run_solver --slug` reads `AsteroidProject` from
  the DB; the only seeders are `seed_exhaustive_sample_genes` / `seed_miner_patterns` (genes/patterns,
  not projects). Depending on incidental local-DB slugs is forbidden by the constraints, and adding a
  project seeder is out of PR-B scope.

- [-] S1 (manual DB smoke) — **NOT REPRODUCIBLE**: no deterministic project fixture slug; project
  seeding is out of PR-B scope. Recorded per the "else mark not reproducible" rule.

### Gate-C-equivalent deterministic evidence (used instead of manual DB smoke)

These tests build an in-test project + `AsteroidMapInput` (deterministic fixtures) and drive the full
`run_solver` / `run_layer02_solver_for_project` path, which now runs L3 with the `m3e_01` default seed:

- [x] `python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py tests/unit/asteroid_lab/test_run_solver_management_command.py tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py -v` — **7 passed**.
- Covers: L2-enabled persists plan + summary (incl. merged rim stack), run_solver management command
  JSON path, and L3 runtime replay timeline after a solver run.
- Note: evidence only; not reused as solver/algorithm input.

### Manual DB smoke template (only if a deterministic slug is later provided)

```text
Environment:
- ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=<value>
- DB: local/dev
- slug: <slug>
- fixture source: <how created or verified>

Command:
  python manage.py run_solver --slug <slug> --json

Observed:
- solver_run_id: <id>
- committed placement count: <n>
- m3e placement count: <n>
- max extension_count: <0..3>
- layer stack log dir: var/log/asteroid_lab_layer_stack/...

Conclusion:
- Smoke evidence only. Not solver input.
```

## Closing (only on explicit user request)

- [ ] full gate (`scripts/test_full.ps1` → ruff → mypy → black)
- [ ] commit / push / PR
- [ ] mark `CLOSED` in `current_plan.md`
