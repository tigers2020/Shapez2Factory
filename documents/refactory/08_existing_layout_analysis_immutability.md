# 목표: ExistingLayoutAnalysis(STEP 0.5) 불변·계약 강화

## 배경

- 정본: `02_pipeline_control_flow.md` STEP 0.5, `03_data_schema_dto.md` §E, `12_protected_corridor.md` §14.2.3 — **read-only context**, 배치 변경 없음.
- 구현: `existing_layout_analysis.py` 모듈 독스트링에 read-only 명시. 호출부는 주로 `.get` 조회.

## 현재 상태

- Python `dict` 반환이라 **실수로 변이** 가능성은 구조적으로 남는다(악의 없는 `.pop` 등).

## 목표 상태

- **A)** `TypedDict` + `typing.Mapping` 반환으로 읽기 전용 의도를 타입으로 표현.
- **B)** `frozen` dataclass 또는 `types.MappingProxyType`으로 얕은 불변 래핑(중첩 dict 정책 문서화).
- **C)** 현 상태 유지 + “변이 금지”를 리뷰 체크리스트에만 추가(비용 최소).

## 작업 항목

1. `existing_layout_analysis`를 쓰는 모든 모듈에서 대입 패턴 grep.
2. P4에 넘기는 `existing_layout_solver_hints` 등 **부분 복사**가 의도인지 확인.
3. 선택한 수준에 맞는 테스트 1건(동일 객체 변이 시도 시 실패 또는 no-op).

## 검증

- 정적/런타임: 가능하면 mypy strict 하위 경로에 한정해 적용.

## 위험

- 깊은 불변은 비용·직렬화 이슈 — **얕은 불변 + 문서**가 현실적일 수 있음.

## 참고 코드

- `existing_layout/existing_layout_analysis.py`
- `solver_pipeline/recovery_orchestrator.py`, `placement/pass1_timeline_integration.py`, `solver_pipeline/p4_reclaim.py`
