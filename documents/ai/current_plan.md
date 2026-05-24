# Current plan

**상태 (2026-05-24)**: **RTTP Hybrid C v0.1** + **3B-S** Lab replay compose. **Track B2 transport (T1–T3)** on `master` — T1 `1c4baecd`, T3 PR #61 `38042eed`, T2 PR #62 `94027496`. 다음 우선: **Track D** catalog footprint/connector (설계·plan 없음 — `brainstorming`부터). Reconstruction → RTTP pipeline → persist → Lab interleaved replay.

**Runtime (코드 정본):**

- `ASTEROID_LAB_RTTP_ENABLED=True` (기본) → `solver_runtime_entry`가 `run_rttp_pipeline` + replay sink를 실행한다.
- `ASTEROID_LAB_RTTP_ENABLED=False` → HTTP `Run Solver`는 **200** + `SOLVER_NOT_AVAILABLE` (reconstruction만 안내). 이것이 유일한 stub 경로다.
- “optimization 삭제·항상 stub”은 **아님** — strip-solver로 제거된 것은 **구 monolith/shadow/RD** 이며, RTTP Hybrid C는 별도 패키지로 복구·배선됨.

**Surgery (역사):** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) · 실행 기록: [`docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md`](../../docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md)

## ACTIVE 코드 경로

```text
django_apps/asteroid_lab/reconstruction/     ← topology, confidence, complete
django_apps/asteroid_lab/optimization/       ← RTTP Hybrid C (skeleton → candidates → regret → commit/LNS)
django_apps/asteroid_lab/contracts/          ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← RTTP runtime entry (config-gated)
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py  ← 3B-S product timeline projection
```

## ARCHIVED (문서·역사)

- strip-solver 이전 monolith optimization / shadow·RD gate — **CANCELLED**
- `solver_runtime/` Phase A–M — [`documents/Algorithm/solver_runtime/README.md`](../Algorithm/solver_runtime/README.md)
- `docs/superpowers/specs/2026-05-22-*commit*`, `*shadow*` — **CANCELLED** (strip spec으로 대체)

## 검증 (narrow)

**RTTP (paused macro track):**

```bash
python -m pytest tests/unit/asteroid_lab/ -k rttp
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

**Reconstruction replay · topology · island_bbox (별도 트랙):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

또는 동일 pytest만:

```bash
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py tests/unit/asteroid_lab/test_reconstruction_replay_merge.py tests/unit/asteroid_lab/test_island_bbox.py tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py tests/unit/asteroid_lab/test_replay_snapshot_contract.py
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/replay django_apps/asteroid_lab/snapshots/island_bbox.py django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
```

커버: fixture topology·export, replay `reconstruction_final` merge + `step4_10` parity, persist bbox vs replay complete, `full_map_island_bbox` read-compat (meta·BP·legacy server ignore), persist 경로 replay ORM 미참조, initial replay full_map contract.

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## 다음 초점

**우선순위:** **Track D** catalog footprint/connector consumption (post B2-T3; parent spec [`building-catalog-slice-first-consumption-design.md`](../../docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md)). **CLOSED:** B2-T3 route domain (PR #61, `38042eed`), B2-T2 per-cell transport (PR #62, `94027496`). **RTTP macro track PAUSE** — 추가 macro/E2E 없음. reconstruction replay/topology narrow gate 유지. 금지: macro 재작업·selection/fitness 변경·validation 완화·replay를 solver input으로 사용.

- Reconstruction replay·topology 회귀 유지 (narrow gate below)
- **CLOSED (2026-05-23):** `full_map_server_bbox` read-compat 제거 — `full_map_island_bbox` only (`island_bbox.py`); Lab HUD `xy` only (no server line).
- **CLOSED (2026-05-23):** RTTP v1 MacroBundleT3 **PR-A..J** on `master` — plan: [`2026-05-23-rttp-v1-macrobundle-t3.md`](../../docs/superpowers/plans/2026-05-23-rttp-v1-macrobundle-t3.md)
- **CLOSED (2026-05-23):** PR-K web `run-solver` POST → `run_solver_runtime_for_project(config=...)` (`macro_only_mode`, `rttp_record_replay`; invalid JSON → 400).
- **CLOSED (2026-05-23):** PR-L Lab UI macro-only checkbox + `fetch` body (`5b06d705`); OPS trial: checkbox + macro commit on real slug.
- **CLOSED (2026-05-23):** GitHub Actions `rttp-lab-macro-smoke` on `master` push/PR.
- **CLOSED (2026-05-23):** HUD `macro_commit_summary` (`#lab-macro-commit-hud`; output-only).
- **CLOSED (2026-05-23):** `manage.py run_solver --slug` + `scripts/run_solver.ps1` (HTTP 동일 runtime path).
- **CLOSED (2026-05-24):** 실맵 macro E2E — `tests/fixtures/asteroid_lab/macro_e2e_copy.code` + `test_rttp_macro_real_map_e2e.py` (no monkeypatch).
- **PAUSE (2026-05-24):** macro track — 추가 solver/macro/E2E 작업 없음. 로컬 `app.css` / `solver_runtime/*.md` / `migration 0012_*` 커밋 금지(별도 의도 확인 전).
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
  - Note: OPS slug `copy-import-495e552c` has `transport_component_count` 0 pre-reconstruction; topology strips top-level transport before adapter — mixed-kind **실맵 `run_solver` 관측은 현재 맵 클래스에서 불가**. 실맵 회귀는 smoke B + narrow RTTP tests.
- RTTP regression fixtures: `test_rttp_narrow_corridor.py` (10A), `test_rttp_reconstruction_fixture_e2e.py` (copy-code lines 0–2)
- ~~`asteroid_lab_10` Sequence 2–7 체크박스~~ → **done (2026-05-23)** [`asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) RTTP gate sync 절

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
