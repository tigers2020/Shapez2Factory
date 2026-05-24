# Current plan

**상태 (2026-05-24)**: **RTTP Hybrid C v0.1** + **3B-S** Lab replay compose. **Track A/B2** game_data provenance + `BuildingCatalogSlice` T1 on `master` (`1c4baecd`, CI green). 다음 우선: **Ops smoke** (Run Solver + provenance v2 + catalog slice 실맵). Reconstruction → RTTP pipeline → persist → Lab interleaved replay.

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

**우선순위 (2026-05-24, Release lead):** **B2-T2** per-cell transport resolution — 별도 PR, narrow scope (`writing-plans` first). **RTTP macro track PAUSE** — 추가 macro/E2E 없음. reconstruction replay/topology narrow gate 유지. 금지: macro 재작업·selection/fitness 변경·validation 완화·footprint/connector full geometry·replay를 solver input으로 사용.

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
  - Next: B2-T2 per-cell transport resolution

- Ops smoke A — provenance v2 + catalog slice on real slug
  - Status: CLOSED
  - Slug: `copy-import-495e552c`
  - Evidence: `manage.py run_solver` exit 0; provenance 10 keys; `SHAPE_BELT`; validation passed
