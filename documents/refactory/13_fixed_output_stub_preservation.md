# 목표: fixed output stub가 Pass3·Recovery·Reclaim에서 제거되지 않도록 보장

## 배경

- 정본: `09_step5_pass3_transport.md` §11.3, `13_step9_validation.md` §15.1 — stub는 고정 시작점; Pass3가 제거·우회 불가.
- Final validation은 stub 존재·종류를 검사한다.

## 현재 상태

- Pass3 greedy 등에서 `fixed_stubs` 집합으로 보존 패턴이 있다(`pass3_greedy_core.py` 등).

## 목표 상태

- **모든** Pass3 분기(greedy / lex shadow / guarded atomic / post-reclaim rerun)·P4 incremental·recovery 경로에서 동일 불변식.
- 제거 시도 전후에 stub 셀 역할 검사(단일 헬퍼 권장).

## 작업 항목

1. transport 셀 삭제·교체 진입점 전수에 `fixed_stubs` 또는 동등 가드가 있는지 표 작성.
2. reclaim soft replace·atomic swap이 stub를 건드릴 수 있는지 코드 경로 확인.
3. §15.1 체크리스트와 테스트 케이스 1:1 매핑.

## 검증

- 단위: stub 인접 transport 제거 시도 → 거절 또는 롤백.

## 참고 코드

- `pass3/pass3_greedy_core.py`, `pass3/pass3_e3_guarded.py`, `reclaim/reclaim_soft_replace.py`
- `validation/final_validation.py`
