# 목표: Final validation(STEP 9)은 assertion gate만 — 새 route/trunk 생성 금지

## 배경

- 정본: `13_step9_validation.md` §15 도입, §15.3 — overflow 해결용 split/additional trunk는 STEP4; Final validation은 새 route를 만들지 않는다.
- `validation_recovery`는 hard invariant용 최소 repair(§13.3).

## 현재 상태

- `validation/final_validation.py`는 geometry·connectivity 등 검사와 `probe_stub_to_external` 등 **가능성 판별**에 가깝고, 레이아웃에 belt를 새로 쓰지 않는다.

## 목표 상태

- 검증 모듈에 **라우팅 커밋 API를 import하지 않는다**는 레이어 규칙을 유지(또는 명시적 allowlist).
- `validation_recovery` 실행 경로가 실제로 맵에 transport를 추가한다면 §15.3과의 정합을 재검토한다.

## 작업 항목

1. `final_validation`·`validation_bridge`·recovery 루프에서 맵 변이 호출 목록화.
2. capacity hard fail을 켠 후에도 “STEP9만으로 trunk 신설”이 없는지 테스트.
3. 문서 §15.1–15.3 체크리스트와 코드 assert 매핑 표.

## 검증

- 아키텍처: domain/application 경계 매뉴얼과 충돌 시 플랜 우선.

## 참고 코드

- `validation/final_validation.py`, `solver_pipeline/validation_bridge.py`
- `solver_pipeline/recovery_orchestrator.py`
