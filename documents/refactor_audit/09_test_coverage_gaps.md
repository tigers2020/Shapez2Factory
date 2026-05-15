# Test Coverage Gaps

## 총평

- import boundary, enum, FSM, read-only analysis 같은 “정적 계약” 테스트는 꽤 좋다.
- 반면 canonical pipeline의 핵심인 STEP 4/8/9/10 end-to-end semantics 테스트는 사실상 없다.
- 특히 일부 테스트는 `NotImplementedError`를 green condition으로 삼아 공백을 장기화한다.

## 부족한 테스트

| Gap | 현재 상태 | 관련 파일 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|---|
| STEP 4 full routing tests | 없음 | `routing/merge_aware_router.py`, `tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py` | `08_step4_routing.md` | P0 | 높음 | `test-only` |
| trunk seed semantic tests | 없음 | `routing/trunk_seed.py`, `tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py` | `08_step4_routing.md §9.2` | P0 | 높음 | `test-only` |
| final validation hard invariant suite | 없음 | `validation/final_validation.py`, `tests/unit/shapez_asteroid_v2/test_final_validation_contract.py` | `13_step9_validation.md` | P0 | 높음 | `test-only` |
| rollback/quarantine lifecycle tests | 부분만 존재 | `placement/placement_fsm.py`는 enum/FSM만 검증 | `08_step4_routing.md`, `11_step8_recovery.md` | P1 | 높음 | `test-only` |
| protected corridor lifecycle tests | 없음 | `domain/orchestration.py`, `domain/corridor.py`, `placement/corridor_opening.py` | `12_protected_corridor.md` | P1 | 높음 | `test-only` |
| replay isolation tests | import-only 위주 | `test_import_boundaries.py`, `test_replay_trace_is_output_only.py` | `14_step10_replay_ui.md` | P1 | 높음 | `test-only` |
| UI/backend replay contract tests | 없음 | `django_apps/web/templates/web/asteroid_optimizer.html`, `views.py`, `tests/unit/web/test_asteroid_optimizer_page.py` | `14_step10_replay_ui.md` | P1 | 높음 | `test-only` |
| transport separation tests | decode/enum 일부만 존재 | `decode/existing_layout_analysis.py`, `pass1_outer.py`, `corridor_opening.py` | `01_project_overview.md §3.6` | P1 | 중간 | `test-only` |
| recovery trigger path tests | enum/semantic validator만 존재 | `domain/enums.py`, `domain/trace_semantics.py` | `02_pipeline_control_flow.md §4.3` | P1 | 높음 | `test-only` |
| orphan trunk validation tests | 없음 | `validation/final_validation.py`, `decode/existing_layout_analysis.py` | `13_step9_validation.md §15.2` | P1 | 높음 | `test-only` |

## 현 테스트의 강점

- `tests/unit/shapez_asteroid_v2/test_import_boundaries.py`
- `tests/unit/shapez_asteroid_v2/test_domain_import_boundaries.py`
- `tests/unit/shapez_asteroid_v2/test_runtime_trace_import_boundaries.py`
- `tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py`
- `tests/unit/shapez_asteroid_v2/test_placement_fsm.py`
- `tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py`

이들은 early freeze 대상 파일의 회귀망으로 계속 유지할 가치가 높다.

## 권장 테스트 순서

1. DTO/domain/runtime cycle 해소 후 import boundary tests 확장
2. STEP 4 trunk seed / route generation golden tests 추가
3. final validation invariant matrix 추가
4. recovery/quarantine/corridor lifecycle state-machine tests 추가
5. UI/backend payload alignment tests 추가
