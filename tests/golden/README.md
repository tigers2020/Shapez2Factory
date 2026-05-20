# Golden Test Data

이 디렉터리는 결정적 회귀 검증 데이터셋을 보관한다 (phase2 이후 채운다).

## 목적

- 입력/출력 쌍이 고정된 "골든" 데이터를 저장한다.
- 알고리즘 또는 도메인 로직 변경 시 의도치 않은 결과 변화를 감지한다.

## 파일 명명

```
<시나리오명>_input.<확장자>
<시나리오명>_expected.<확장자>
```

예: `solver_basic_input.json`, `solver_basic_expected.json`

## 사용 규칙

- golden 파일은 수동으로만 추가/수정한다.
- CI에서 실제 출력과 expected 파일을 비교한다.
- golden 데이터 변경은 ADR 또는 PR 설명에 이유를 반드시 기록한다.

## 활성화 조건 (phase2)

- Comparator: [`harness/validators/compare_golden.py`](../../harness/validators/compare_golden.py)
- 첫 시나리오: `candidate_selector_trunk_split_*` — [`tests/test_golden_candidate_selector.py`](../test_golden_candidate_selector.py)
- golden 변경 시 PR/ADR에 이유 기록
