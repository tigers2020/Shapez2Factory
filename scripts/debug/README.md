# Offline debug / report tools

이 디렉터리의 스크립트는 **런타임 솔버 알고리즘 밖**에서만 쓴다.

- **NDJSON** (`*.ndjson`, `latest.ndjson` 등), **`solver_summary`** 줄, **`replay_events`**/trace 행은 **검증·리포트·수동 리뷰용 산출물**이지, `documents/Algorithm/mining_solver_cursor_sessions/`에 정의된 파이프라인의 **입력 계약이 아니다** (`02` §4, `14` §16 참고).
- **`django_apps/`** 솔버·`solver_pipeline` 코드는 **`scripts/debug`를 import하지 않는다** (역방향 의존 금지).

## 포함 스크립트

| 스크립트 | 요약 |
|----------|------|
| `p4_pass3_trace_review.py` | NDJSON에서 마지막 `solver_summary` 등 요약 리뷰 |
| `aggregate_pass12_recoverability_from_ndjson.py` | NDJSON 다건 스캔·집계 |
| `pass12_preserve_recovery_ab.py` | preserve A/B·NDJSON/복사본 입력 실험 |
| `extract_step4_no_route_exhausted_samples.py` | NDJSON에서 no-route exhausted 샘플 추출 |

실행 예는 각 파일 상단 docstring을 본다. 레포 루트에서:

`python scripts/debug/<name>.py ...`
