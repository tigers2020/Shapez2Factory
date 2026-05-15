# Protected Corridor Drift

## 결론

- canonical 문서가 요구하는 `hard_protected` / `soft_protected` / `candidate_corridor` lifecycle은 아직 구현 레벨에서 완성되지 않았다.
- 현재 코드는 일부 snapshot 필드와 recovery cost 가드만 있을 뿐, candidate 생성/승격/폐기 lifecycle이 없다.

## drift 목록

| File | 관측 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/orchestration.py` | `RoutingStateSnapshot`에 hard/soft만 있고 candidate pool 없음 | `12_protected_corridor.md §14.2` | P1 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/corridor.py` | corridor DTO는 recovery result 위주이며 lifecycle model이 아님 | `12_protected_corridor.md §14.2~§14.3` | P1 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/corridor_opening.py` | hard corridor는 단순 금지 셀로만 소비 | `12_protected_corridor.md §14.3` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py` | trunk/cleanup hint는 잘 분리되지만 protected 승격 계층은 없음 | `12_protected_corridor.md §14.2.3` | P2 | 높음 | `keep`, `adapter 추가` |
| `django_apps/web/templates/web/asteroid_optimizer.html` | UI는 protected corridor overlay를 기대 | `14_step10_replay_ui.md §16.3` | P2 | 중간 | `investigate-further` |

## root cause

- STEP 4 라우터 자체가 skeleton이라 corridor commit/replace lifecycle이 들어갈 canonical 위치가 아직 없다.
- recovery helper가 placement 쪽에 있어서 corridor state를 routing authority에서 관리하지 못한다.
- trace/output schema가 먼저 잡히고 state authority가 뒤따르지 못했다.

## 초기 동결 영역

- `decode/existing_layout_analysis.py`
  - trunk/cleanup hint 생성은 현재 read-only contract와 잘 맞는다.
- 이 레이어는 early refactor에서 corridor authority로 승격하지 말고, 계속 hint producer로만 두는 것이 안전하다.

## 우선 작업

1. `candidate_corridor`를 포함한 `RoutingStateSnapshot` 재설계
2. STEP 4 commit/replacement authority를 `routing/`으로 이동
3. `hard_protected` 승격 조건과 trace adapter를 분리
4. replay overlay는 state authority 정리 후 마지막에 붙이기
