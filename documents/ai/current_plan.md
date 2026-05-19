# Current plan

**상태 (2026-05-16)**: `django_apps.shapez_asteroid` 앱 제거 이후 웹·솔버·`asteroid_lab` green 유지.

## Asteroid reconstruction (topology fill)

- **`cleanup.wall_coords`**: 디코드 evidence + 제거된 extractor/extension 좌표; belt/pipe는 포함하지 않음 (기존 계약 유지).
- **`reconstruction` barrier**: `barrier_xy = wall_coords ∪ infer_shell_barrier_coords(...)` — **외부 `external_reachable` flood만** 차단하는 추론 shell(행·열 span 등). cleanup 산출물이 아님.
- **Fill 허가**: `passes_two_axis_evidence_guard`는 **원본 `wall_coords`만** 사용. `barrier_xy`를 guard에 넣지 않음(추론 벽으로 자기증명·과충전 방지).

## 현재 초점

- **Solver Runtime (PR1B–PR2.5–PR2):** `django_apps/asteroid_lab/optimization/` — 입력 adapter·capacity/route goals·geometry/route probe 완료. 다음 merge 단위 **PR3** (candidate pool).
- 웹·솔버·`asteroid_lab` 경로가 `manage.py check`·`pytest`·로케일 strict 빌드로 green인지 유지한다.
- 문서 링크 깨짐(`mining_solver_cursor_sessions` 등)은 inventory·README 수준에서 정리 완료. 세부 archive stem은 필요 시 사람이 선별한다.

## 금지

- 제거된 `shapez_asteroid` 패키지나 삭제된 테스트 경로를 전제로 한 새 기능 요구를 문서만으로 «살아 있는 계약»처럼 취급하지 않는다.
