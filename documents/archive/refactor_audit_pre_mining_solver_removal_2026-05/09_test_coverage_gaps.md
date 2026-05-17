# Test Coverage Gaps

## 실행 확인

- structural suite: `python -m pytest tests/unit/asteroid_lab tests/unit/web/test_asteroid_lab_page_context.py tests/integration/web/test_asteroid_miner_layout_solver.py -q`
- result: `147 passed`

현재 테스트는 live lab shell의 안정성은 꽤 잘 잡지만, canonical solver drift를 막는 테스트는 거의 없다.

## gap matrix

| Gap | Missing evidence | Existing nearby tests | Severity | Action |
|---|---|---|---|---|
| canonical/live alignment test | canonical 문서와 live package 매핑 검증 없음 | 없음 | `P1` | `test-only` |
| replay isolation test | replay 모듈이 runtime calculation을 import하지 않는지 없음 | `test_replay_snapshot_contract.py`는 payload만 검증 | `P1` | `test-only` |
| import graph / SCC test | substring 금지만 있고 allowed-edge/SCC 검증 없음 | `test_service_import_boundaries.py` | `P2` | `test-only` |
| validation contract test | assertion-only final validation surface 자체가 없음 | 없음 | `P1` | `test-only` |
| recovery lifecycle test | typed retry/rollback state 없음 | integration test는 force rebuild만 검증 | `P1` | `test-only` |
| protected corridor test | 관련 시스템 부재 | 없음 | `P1` | `test-only` |
| DTO namespace split test | `services/dto.py` semantic 분리 없음 | 일부 DTO usage test만 존재 | `P2` | `test-only` |
| UI trace schema test | canonical `trace_event` / `computation_cycle` / streaming cadence 검증 없음 | page context / JS smoke 일부 | `P1` | `test-only` |
| dead model reachability test | unused model이 admin/tests 외에 쓰이지 않는지 감시 없음 | 없음 | `P2` | `test-only` |

## 이미 강한 영역

- replay frame monotonic ordering
- full_map snapshot contract
- decode / existing-layout inspection functional behavior
- reconstruction topology pure behavior
- page rendering / replay cell lookup integration

## 추천 추가 테스트 순서

1. AST import graph + no-SCC test
2. replay module no-runtime-import test
3. canonical/live namespace inventory test
4. serializer contract test for backend → UI payload
5. future migration용 validation/recovery placeholder tests
