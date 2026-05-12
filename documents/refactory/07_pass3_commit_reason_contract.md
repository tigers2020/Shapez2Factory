# 목표: Pass3 `commit_reason`과 §13.5 스키마 정렬

## 배경

- 정본: `11_step8_recovery.md` §13.5 — 성공 `commit_reason`: `normal_gain`, `degraded_connected_recovery`.
- 구현: Pass3 guarded atomic 등에서 `COMMIT_REASON_GUARDED_ATOMIC` 등 **추가 문자열**이 trace/summary에 실릴 수 있다(`pass3_transport.py` 등).

## 현재 상태

- 기능상 문제가 없어도 §16.3 trace 스키마·외부 소비자가 “허용 enum”을 좁게 가정하면 깨진다.

## 목표 상태

- **A)** 정본 §13.5에 서브타입을 추가(예: `guarded_atomic_commit`)하고 문서·코드 enum을 동기화.
- **B)** 상위 `commit_reason`은 정본 두 값으로 **매핑**하고, 세부는 `pass3_commit_subtype` 등 별도 필드에 둔다.

## 작업 항목

1. `pass3_commit_reason` / `p3e3_*` / `p3f_commit_reason` 발생 경로 목록화.
2. `recovery_validation_outcome`와의 중복 제거(03 문서와 연계).
3. OpenAPI·주석·테스트 fixture 정리.

## 검증

- 단위 테스트: 각 commit 경로별로 기대 enum 한 줄 assert.

## 위험

- 문자열 비교 분기가 있는 레거시 UI 스크립트 파편 점검.

## 참고 코드

- `pass3/pass3_transport.py`, `pass3/pass3_greedy_core.py`, `pass3/pass3_f_branch_candidate.py`
- `solver_pipeline/pass3.py`
