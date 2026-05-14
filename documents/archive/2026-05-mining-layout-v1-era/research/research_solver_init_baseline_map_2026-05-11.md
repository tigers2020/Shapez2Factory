# solver_init·STEP 0.5 베이스라인 맵 (with_transport + final interior)

## 변경 요약

- **문제**: `solver_timeline`의 `solver_init` 프레임과 `analyze_existing_layout_from_mining_map` 입력이 `map_timeline[0]`(`with_transport`)만 사용해, `fill_interior` 이후의 `role: inferred` 패치 내부가 UI·분석에서 빠져 보였다.
- **대응**: `merge_with_transport_and_final_mining_map(with_transport, final)` 헬퍼를 [`django_apps/shapez_asteroid/services/blueprint_map_summary.py`](../../django_apps/shapez_asteroid/services/blueprint_map_summary.py)에 둔다. **final의 `role: inferred` 셀**과 **with_transport에 없는 mineable 좌표**만 final에서 채우고, 이미 with_transport에 있는 행(활성 채굴기 등)은 final의 `asteroid_field`로 덮어쓰지 않는다(Pass12 `_merge_pass1_into_rows`의 전면 덮어쓰기와는 구분 — 표시·STEP0.5는 BP 원본 건물을 유지).
- **적용처**:
  - `build_final_solver_output`의 `SOLVER_FRAME_INIT` `mining_map`
  - `run_solver_timeline_pipeline`의 STEP 0.5 분석 입력
  - `copy_preview`의 `existing_layout_analysis` 분석 입력
- **유지**: Pass12 `working_map` 인자는 계속 `map_timeline[0]`(벨트/파이프 스크래치 수집 규약).

## 순환 import

`blueprint_map_summary` 모듈 로드 시 `asteroid_mining_layout` 패키지 `__init__`이 타지 않도록, 병합 함수 안에서만 mining_layout 서브모듈을 import한다.
