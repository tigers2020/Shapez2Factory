# Test Coverage Gaps

## Execution confirmation

- structural suite: `python -m pytest tests/unit/asteroid_lab tests/unit/web/test_asteroid_lab_page_context.py tests/integration/web/test_asteroid_miner_layout_solver.py`
- result: `147 passed`

Current tests capture live lab shell stability fairly well but almost none block canonical solver drift.

## gap matrix

| Gap | Missing evidence | Existing nearby tests | Severity | Action |
|---|---|---|---|---|
| canonical/live alignment test | no verification mapping canonical docs to live package | none | `P1` | `test-only` |
| replay isolation test | no check that replay module does not import runtime calculation | `test_replay_snapshot_contract.py` validates payload only | `P1` | `test-only` |
| import graph / SCC test | substring prohibition only; no allowed-edge/SCC verification | `test_service_import_boundaries.py` | `P2` | `test-only` |
| validation contract test | assertion-only final validation surface itself absent | none | `P1` | `test-only` |
| recovery lifecycle test | no typed retry/rollback state | integration test verifies force rebuild only | `P1` | `test-only` |
| protected corridor test | related system absent | none | `P1` | `test-only` |
| DTO namespace split test | no semantic split of `services/dto.py` | some DTO usage tests only | `P2` | `test-only` |
| UI trace schema test | no canonical `trace_event` / `computation_cycle` / streaming cadence verification | partial page context / JS smoke | `P1` | `test-only` |
| dead model reachability test | no guard that unused models are not used outside admin/tests | none | `P2` | `test-only` |

## Already strong areas

- replay frame monotonic ordering
- full_map snapshot contract
- decode / existing-layout inspection functional behavior
- reconstruction topology pure behavior
- page rendering / replay cell lookup integration

## Recommended additional test order

1. AST import graph + no-SCC test
2. replay module no-runtime-import test
3. canonical/live namespace inventory test
4. serializer contract test for backend → UI payload
5. validation/recovery placeholder tests for future migration
