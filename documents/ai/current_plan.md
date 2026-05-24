# Current plan

**Status (2026-05-24)**: **RTTP Hybrid C v0.1** + **3B-S** Lab replay compose. **Track B2 transport (T1–T3)**, **Track D**, and **PR-A** doc authority repair on `master` (plan close `c20fc1e5`; PR-A merge `cd364b84`). Reconstruction → RTTP pipeline → persist → Lab interleaved replay.

**Runtime (code authority):**

- `ASTEROID_LAB_RTTP_ENABLED=True` (default) → `solver_runtime_entry` runs `run_rttp_pipeline` + replay sink.
- `ASTEROID_LAB_RTTP_ENABLED=False` → HTTP `Run Solver` returns **200** + `SOLVER_NOT_AVAILABLE` (reconstruction guidance only). This is the only stub path.
- "optimization removed · always stub" is **not** the case — strip-solver removed the **legacy monolith/shadow/RD**; RTTP Hybrid C was restored and wired as a separate package.

**Surgery (history):** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) · execution record: [`docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md`](../../docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md)

## Authority precedence

No global precedence rule between Algorithm vs superpowers on document conflicts — follow [`document_inventory.md`](../index/document_inventory.md) **§ Asteroid Lab authority by topic** rows.

1. Code + tests: `django_apps/asteroid_lab/{reconstruction,optimization,contracts}/`, `tests/unit/asteroid_lab/`
2. This file — active queue and runtime pointer
3. `docs/superpowers/specs/` — merged RTTP/B2 specs (per topic row)
4. `documents/Algorithm/asteroid_lab_*.md` — stable DTO / route / validation / replay semantics
5. `document_inventory.md` — doc status and topic routing
6. `documents/plans/asteroid_lab_optimization/` — **QUARANTINE** (historical snapshots only; `do_not_use_as_authority`)
7. `documents/Algorithm/solver_runtime/` — historical Phase A–M unless this file promotes a subsection
8. `REPORT`, `documents/debug/`, `documents/archive/` — observation only

Operational rules: [`contamination_policy.md`](contamination_policy.md). Design: [`docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md`](../../docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md).

## ACTIVE code paths

```text
django_apps/asteroid_lab/reconstruction/     ← topology, confidence, complete
django_apps/asteroid_lab/optimization/       ← RTTP Hybrid C (skeleton → candidates → regret → commit/LNS)
django_apps/asteroid_lab/contracts/          ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← RTTP runtime entry (config-gated)
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py  ← 3B-S product timeline projection
```

## ARCHIVED (documents · history)

- Pre strip-solver monolith optimization / shadow·RD gate — **CANCELLED**
- `solver_runtime/` Phase A–M — [`documents/Algorithm/solver_runtime/README.md`](../Algorithm/solver_runtime/README.md)
- `docs/superpowers/specs/2026-05-22-*commit*`, `*shadow*` — **CANCELLED** (replaced by strip spec)

## Verification (narrow)

**RTTP (paused macro track):**

```bash
python -m pytest tests/unit/asteroid_lab/ -k rttp
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

**Reconstruction replay · topology · island_bbox (separate track):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Or pytest only:

```bash
powershell -File scripts/test_reconstruction_narrow.ps1
```

Or pytest only (seven modules — includes B-CS4 boundary; **no** `test_rttp_replay_*`):

```bash
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py tests/unit/asteroid_lab/test_reconstruction_replay_merge.py tests/unit/asteroid_lab/test_island_bbox.py tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py tests/unit/asteroid_lab/test_replay_snapshot_contract.py tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/replay django_apps/asteroid_lab/snapshots/island_bbox.py django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
```

Coverage: fixture topology·export, replay `reconstruction_final` merge + `step4_10` parity, persist bbox vs replay complete, `full_map_island_bbox` read-compat (meta·BP·legacy server ignore), persist path does not reference replay ORM (`filter`/`get`/`all` sentinels in B-CS4), initial replay full_map contract, AST boundaries for reconstruction + audited replay modules (B-CS4).

## Maintenance / Standing Gates

- **Replay contract narrow gate owner:** `powershell -File scripts/test_reconstruction_narrow.ps1`
  - Includes `test_b_cs4_reconstruction_replay_boundary.py`; **excludes** `test_rttp_replay_*`
  - Failure after B-CS4 CLOSED = maintenance regression track (reopen B-CS3/B-CS4 only if original closure evidence was invalid)

- **PR-B optimization contamination gate owner:** `powershell -File scripts/test_optimization_contamination.ps1`
  - Or: `python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short` + `ruff check django_apps/asteroid_lab/optimization tests/unit/architecture`
  - **Not** included in `test_reconstruction_narrow.ps1` (reconstruction-only)

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## Next focus

**Priority:** **Decontamination PR-B** optimization contamination gates (AST import canon). **Entry Gate A:** Gate 1–2 green on branch with B-CS3/4 before PR-B merge to `master`. **Axis B B-CS1–B-CS4 CLOSED**. **Axis A D+ PR-1..PR-3 CLOSED**. **RTTP macro PAUSE**. Next after PR-B: PR-D/E or RTTP core (deferred commit retry). Forbidden: validation repair · unmapped synthetic fail-closed · replay/NDJSON/solver_summary as algorithm input.

- Standing owner: reconstruction replay·topology + B-CS4 boundary (`test_b_cs4_reconstruction_replay_boundary.py` in narrow gate below)
- **CLOSED (2026-05-23):** `full_map_server_bbox` read-compat removed — `full_map_island_bbox` only (`island_bbox.py`); Lab HUD `xy` only (no server line).
- **CLOSED (2026-05-23):** RTTP v1 MacroBundleT3 **PR-A..J** on `master` — plan: [`2026-05-23-rttp-v1-macrobundle-t3.md`](../../docs/superpowers/plans/2026-05-23-rttp-v1-macrobundle-t3.md)
- **CLOSED (2026-05-23):** PR-K web `run-solver` POST → `run_solver_runtime_for_project(config=...)` (`macro_only_mode`, `rttp_record_replay`; invalid JSON → 400).
- **CLOSED (2026-05-23):** PR-L Lab UI macro-only checkbox + `fetch` body (`5b06d705`); OPS trial: checkbox + macro commit on real slug.
- **CLOSED (2026-05-23):** GitHub Actions `rttp-lab-macro-smoke` on `master` push/PR.
- **CLOSED (2026-05-23):** HUD `macro_commit_summary` (`#lab-macro-commit-hud`; output-only).
- **CLOSED (2026-05-23):** `manage.py run_solver --slug` + `scripts/run_solver.ps1` (same runtime path as HTTP).
- **CLOSED (2026-05-24):** Real-map macro E2E — `tests/fixtures/asteroid_lab/macro_e2e_copy.code` + `test_rttp_macro_real_map_e2e.py` (no monkeypatch).
- **PAUSE (2026-05-24):** macro track — no additional solver/macro/E2E work. Do not commit local `app.css` / `solver_runtime/*.md` / `migration 0012_*` without separate intent confirmation.
- **CLOSED (2026-05-24):** reconstruction replay·topology narrow gate — `scripts/test_reconstruction_narrow.ps1` + tightened `test_island_bbox` / `test_reconstruction_replay_merge`.
- **CLOSED (2026-05-24):** Ops smoke A — real lab slug `copy-import-495e552c`
  - `python manage.py run_solver --slug copy-import-495e552c` exit 0
  - `game_data_snapshot_provenance` v2 persisted with 10 keys
  - `catalog_slice_hash` parsed successfully
  - RTTP default transport resolved to `SHAPE_BELT`
  - `ok: true`, `validation_passed: true`, `issue_codes: []`
  - Note: `solver_summary_stack` file exists; latest run stack entry depends on stack-log env.
- **CLOSED (2026-05-24):** Ops smoke B — existing transport on real slug `copy-import-495e552c` (post B2-T2 PR #62)
  - `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` 45)
  - `game_data_snapshot_provenance` v2 (10 keys); `catalog_slice_hash` present
  - `ok: true`, `validation_passed: true`, `issue_codes: []`
  - `rttp.route_domain`: `mismatched_existing_transport_count` 0 (B2-T3 metrics; no `CATALOG_TRANSPORT_UNRESOLVED`)
- **CLOSED (2026-05-24):** Ops smoke C — B2-T3 mixed transport partition gate
  - `python -m pytest tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py tests/unit/asteroid_lab/test_optimization_input_adapter.py::test_mixed_existing_transport_partitions_for_shape_run` — pass
  - Proves wrong-kind existing transport excluded from trunk + `mismatched_existing_transport_*` metrics (`fluid_pipe` mismatch path)
  - Note: OPS slug `copy-import-495e552c` has `transport_component_count` 0 pre-reconstruction; topology strips top-level transport before adapter — mixed-kind **real-map `run_solver` observation is not possible with the current map class**. Real-map regression is smoke B + narrow RTTP tests.
- RTTP regression fixtures: `test_rttp_narrow_corridor.py` (10A), `test_rttp_reconstruction_fixture_e2e.py` (copy-code lines 0–2)
- ~~`asteroid_lab_10` Sequence 2–7 checkboxes~~ → **done (2026-05-23)** [`asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) RTTP gate sync section

## Closed

- Track A — GameDataSnapshotProvenance gate
  - Status: CLOSED
  - Merged into master: `1c4baecd`
  - PR: #57 / integration via B2 master fast-forward

- Track B2 — BuildingCatalogSlice first consumption
  - Status: CLOSED
  - Merged into master: `1c4baecd`
  - Plan: [`docs/superpowers/plans/2026-05-24-building-catalog-slice-first-consumption.md`](../../docs/superpowers/plans/2026-05-24-building-catalog-slice-first-consumption.md)
  - Ops smoke A: CLOSED (`copy-import-495e552c`, 2026-05-24)

- B2-T2 — Per-cell catalog transport resolution
  - Status: CLOSED
  - Merged into master: `94027496`
  - PR: #62
  - Plan: [`docs/superpowers/plans/2026-05-24-b2-t2-per-cell-transport-resolution.md`](../../docs/superpowers/plans/2026-05-24-b2-t2-per-cell-transport-resolution.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md)
  - Ops smoke B: CLOSED (`copy-import-495e552c`, 2026-05-24)

- B2-T3 — Transport-aware route domain
  - Status: CLOSED
  - Merged into master: `38042eed`
  - PR: #61
  - Plan: [`docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md`](../../docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md)
  - Ops smoke C: CLOSED (pytest partition + route-domain metrics gate, 2026-05-24)

- Ops smoke A — provenance v2 + catalog slice on real slug
  - Status: CLOSED
  - Slug: `copy-import-495e552c`
  - Evidence: `manage.py run_solver` exit 0; provenance 10 keys; `SHAPE_BELT`; validation passed

- Ops smoke B — existing transport + catalog registry on real slug
  - Status: CLOSED
  - Slug: `copy-import-495e552c`
  - Evidence: `manage.py run_solver` exit 0 post PR #62; provenance 10 keys; validation passed; route-domain mismatch metrics present (0 mismatch on shape run)

- Ops smoke C — B2-T3 mixed transport partition
  - Status: CLOSED
  - Gate: `test_rttp_transport_kind_route_domain.py` + `test_mixed_existing_transport_partitions_for_shape_run`
  - Evidence: pytest pass; `mismatched_existing_transport_by_kind` includes `fluid_pipe` on shape-active runs

- Track D — Catalog footprint & connector slice (v2)
  - Status: CLOSED
  - Merged into master: `f781d7df`
  - PR: #63
  - Plan: [`docs/superpowers/plans/2026-05-24-track-d-catalog-footprint-connector.md`](../../docs/superpowers/plans/2026-05-24-track-d-catalog-footprint-connector.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-track-d-catalog-footprint-connector-design.md`](../../docs/superpowers/specs/2026-05-24-track-d-catalog-footprint-connector-design.md)
  - Ops smoke D: CLOSED (`copy-import-495e552c`, 2026-05-24)
    - `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` 47)
    - `catalog_slice_version`: `building_catalog_slice_v2`; provenance 10 keys
    - `rttp.catalog_slice` metrics: variant_geometry_count 131, footprint_cell_count 362, connector_count 314
    - `ok: true`, `validation_passed: true`, `issue_codes: []`

- Ops smoke D — Track D catalog v2 on real slug
  - Status: CLOSED
  - Slug: `copy-import-495e552c`
  - Evidence: see Track D entry above

- PR-A — Repo decontamination authority repair
  - Status: CLOSED
  - Merged into master: `cd364b84`
  - PR: #64
  - Plan: [`docs/superpowers/plans/2026-05-24-repo-decontamination-authority-pr-a.md`](../../docs/superpowers/plans/2026-05-24-repo-decontamination-authority-pr-a.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md`](../../docs/superpowers/specs/2026-05-24-repo-decontamination-authority-design.md)
  - Gate: grep acceptance + `tests/unit/architecture/` (docs-only; no runtime change)

- Track D+ PR-2 — Mapped fail-closed catalog placement validation
  - Status: **CLOSED**
  - Merged into master: `d676286f`
  - PR: #65
  - Plan: [`docs/superpowers/plans/2026-05-24-track-d-plus-pr2-catalog-placement-validation.md`](../../docs/superpowers/plans/2026-05-24-track-d-plus-pr2-catalog-placement-validation.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-track-d-plus-catalog-placement-validation-design.md`](../../docs/superpowers/specs/2026-05-24-track-d-plus-catalog-placement-validation-design.md)
  - Ops smoke E4: `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` 51, `run_key` `rttp-71d2b0725d54`)
  - Evidence: `catalog_validation_mode` `mapped_fail_closed`; `validation_passed` / `run_success` true; `issue_codes` `[]`; one `rttp.catalog_placement_validation` step; `catalog_warning_codes` `['catalog_variant_mapping_missing']` (unmapped synthetic, non-failing); `catalog_error_issue_codes` `[]`
  - Includes B-CS1 regression pack restored: `tests/unit/asteroid_lab/test_rttp_commit_survivability.py` (prerequisite gate; not on `master` at PR-1 base)
  - Forbidden preserved: no validation repair; unmapped fail-closed; read-only validation; `final_validation.py` untouched

- Track D+ PR-3 — Catalog-native candidate generation
  - Status: **CLOSED**
  - Merged into master: `dfbda7b8`
  - PR: #66
  - Plan: [`docs/superpowers/plans/2026-05-24-track-d-plus-pr3-catalog-native-generator.md`](../../docs/superpowers/plans/2026-05-24-track-d-plus-pr3-catalog-native-generator.md)
  - Spec: [`docs/superpowers/specs/2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md`](../../docs/superpowers/specs/2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md)
  - Ops smoke E5: `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` 54)
  - Evidence: `normal_count` 127; `unmapped_candidate_count` 0; `validation_passed` true; `catalog_placement_ref` on all normal candidates; `lin_*` test-only

- B-CS4 — Reconstruction / Lab replay boundary audit
  - Status: **CLOSED**
  - Spec: [`docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md`](../../docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md)
  - Evidence: `powershell -File scripts/test_reconstruction_narrow.ps1` — 55 PASS; `test_b_cs4_reconstruction_replay_boundary.py` — 31 PASS
  - PR-C: reconstruction/replay contamination portion absorbed (B-CS4-9); validation portion remains B-CS3
  - No production reconstruction/replay code changes

- B-CS3 — Validation gate boundary audit
  - Status: **CLOSED**
  - Spec: [`docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md`](../../docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md)
  - Evidence: `python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py` — 11 PASS; B-CS1 + `test_validation_readonly_guards` + narrow RTTP (`-k "rttp and not macro_real_map"`) PASS
  - PR-C: validation/replay contamination portion absorbed (B-CS3-9); broader PR-B/D/E not closed here
  - No production solver code changes

- B-CS2 — Trunk-connected commit ops smoke (real slug)
  - Status: **CLOSED**
  - Slug: `copy-import-495e552c`
  - Spec: [`docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs2-trunk-ops-smoke-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-b-cs2-trunk-ops-smoke.md`](../../docs/superpowers/plans/2026-05-24-b-cs2-trunk-ops-smoke.md)
  - Evidence: `python manage.py run_solver --slug copy-import-495e552c` exit 0 (`solver_run_id` 55, `run_key` `rttp-3afe34cb62c4`)
  - `confirmed_count` 1; `commit_order` length 1; `rttp.commit` passed with non-empty `committed_ids`; `conflict_count` 0
  - `rttp.route_domain`: `skeleton_id` `e2af30c1ea51d853`; `mismatched_existing_transport_count` 0
  - `validation_passed` / `run_success` true; `issue_codes` `[]`; B-CS2-17 step order verified (catalog_slice → route_domain → … → commit → catalog_placement_validation)
  - Prerequisite: B-CS1 `test_rttp_commit_survivability.py`; not a substitute for E5

- Decontamination PR-B — Optimization contamination gates
  - Status: **CLOSED** (branch `feat/decontamination-pr-b-optimization-gates` @ `590c387c`; merge to `master` pending)
  - Spec: [`docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md`](../../docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-decontamination-pr-b-optimization-gates.md`](../../docs/superpowers/plans/2026-05-24-decontamination-pr-b-optimization-gates.md)
  - Evidence: `test_optimization_contamination_gates.py` 3 PASS; `test_optimization_milestone_import_boundary.py` absorbed and removed; standing `scripts/test_optimization_contamination.ps1`
  - Entry Gate A (2026-05-24): reconstruction narrow 55 PASS; RTTP narrow 127 PASS on integration branch (pre-`master` B-CS3/4 merge)
  - No production solver behaviour change
