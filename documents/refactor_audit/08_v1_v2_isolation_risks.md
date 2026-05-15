# v1 / v2 Isolation Risks

## 현재 상태

- 긍정:
  - `v2` 내부에서 legacy `asteroid_mining_layout` 직접 import는 구조 테스트로 차단된다.
- 부정:
  - old support service와 UI contract가 여전히 남아 있어 **논리적 isolation**은 아직 불완전하다.

## 직접 import 상태

| 항목 | 판정 | 근거 |
|---|---|---|
| `v2 -> v1` 직접 Python import | 없음 | `tests/unit/shapez_asteroid_v2/test_import_boundaries.py` 통과 |
| `routing/placement/validation -> replay import` | 없음 | 동일 테스트 통과 |
| Django import in v2 tree | 없음 | 동일 테스트 통과 |

## isolation risk 목록

| File / Area | 위험 | 설명 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/blueprint_map_summary.py` | legacy-adjacent preview shadow | v2 preview와 역할 중복 | P1 | 높음 | `deprecate` |
| `django_apps/shapez_asteroid/services/asteroid_reconstruction.py` | old reconstruction shadow | v2 reconstruction과 의미 중복 | P1 | 높음 | `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_patch_interior.py` | shared mutable helper risk | geometry algorithm이 두 군데로 분기 | P1 | 높음 | `extract` |
| `django_apps/web/templates/web/asteroid_optimizer.html` | replay schema leakage | legacy `solver_timeline`/`solver_replay`/`ui_frames` 가정 | P1 | 높음 | `isolate` |
| `django_apps/shapez_asteroid/views.py` | adapter stack 혼합 | copy-preview, debug dump, behavior artifact, dev report를 한 view path에 수렴 | P2 | 중간 | `split` |
| `documents/archive/2026-05-mining-layout-v1-era/**` | documentation leakage | 구현 판단에 쓰면 안 되는 historical v1 근거가 매우 많음 | P2 | 높음 | `freeze`, `keep_as_history` |

## mixed routing pipeline 위험

- 현재 repo에는 실제 v1 runtime package는 없지만, 프론트와 support service 이름이 여전히 예전 solver contract 언어를 사용한다.
- 따라서 위험은 “v1 코드 호출”보다 “v1-era contract vocabulary가 v2 adapter에 계속 남는 것”이다.

## 안전한 migration 원칙

1. old support service 삭제 전 호출부를 모두 `v2` adapter로 수렴
2. UI에서 `solver_replay`/`solver_timeline` 요구를 partial preview와 분리
3. archive 문서는 구현 근거가 아니라 역사 레이어로만 유지
4. `tests/unit/shapez_asteroid_v2/` 외에 `tests/unit/web/`도 v2-only payload 기준으로 재편
