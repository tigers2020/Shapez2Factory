# Dead / Duplicate / Shadow Code

## 총평

- `v1` 직접 import는 제거되어 있지만, 동일 역할의 non-v2 service가 남아 있어 shadow logic 위험이 크다.
- 특히 STEP 1 reconstruction, patch interior, preview timeline은 “옛 support stack”과 “v2 stack”이 병존한다.

## 중복/그림자 목록

| File | 유형 | 관측 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_reconstruction.py` | duplicate implementation | docstring이 STEP1 reconstruction을 직접 선언 | `05_step1_reconstruction.md` | P1 | 높음 | `migrate`, `deprecate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py` | canonical candidate | v2 STEP1 reconstruction 구현 | `05_step1_reconstruction.md` | P1 | 높음 | `keep`, `extract` |
| `django_apps/shapez_asteroid/services/asteroid_patch_interior.py` | duplicate utility | old interior fill utility | `05_step1_reconstruction.md` | P1 | 높음 | `extract`, `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/patch_interior.py` | duplicate utility | v2 interior fill utility | `05_step1_reconstruction.md` | P1 | 높음 | `extract`, `keep` |
| `django_apps/shapez_asteroid/services/blueprint_map_summary.py` | shadow preview stack | map timeline / copy preview / merge helper를 유지 | `14_step10_replay_ui.md` | P1 | 높음 | `deprecate`, `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/preview_reconstruction_timeline.py` | canonical candidate | v2 preview frame builder | `14_step10_replay_ui.md` | P1 | 높음 | `split`, `keep` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/step4_corridor_recovery.py` | stale wrapper | 실질 로직 없이 placement 함수 재노출 | `08_step4_routing.md`, `11_step8_recovery.md` | P1 | 높음 | `deprecate` |
| `tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py` | dead-gap lock-in | `NotImplementedError`를 green contract로 고정 | `08_step4_routing.md` | P2 | 높음 | `test-only` |
| `tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py` | dead-gap lock-in | trunk seed 미구현을 계약으로 고정 | `08_step4_routing.md` | P2 | 높음 | `test-only` |
| `tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py` | dead-gap lock-in | NDJSON reader 미구현을 계약으로 고정 | `14_step10_replay_ui.md` | P2 | 높음 | `test-only` |

## 삭제 대신 격리해야 하는 코드

- 즉시 삭제 금지:
  - `django_apps/shapez_asteroid/services/blueprint_map_summary.py`
  - `django_apps/shapez_asteroid/services/asteroid_reconstruction.py`
  - `django_apps/shapez_asteroid/services/asteroid_patch_interior.py`

이유:

- `views.py`와 copy-preview 경로에서 여전히 legacy-adjacent 의미를 가진다.
- 먼저 호출부를 완전히 `v2` adapter로 수렴시킨 뒤에만 삭제/rename이 안전하다.

## pure utility 추출 후보

- `asteroid_patch_interior.py` + `v2/reconstruction/patch_interior.py`
  - 공통 geometry util library 후보
- `routing/connectivity.py`
  - transport graph pure utility 후보
- `domain/trace_semantics.py`
  - semantic validator pure utility 후보
