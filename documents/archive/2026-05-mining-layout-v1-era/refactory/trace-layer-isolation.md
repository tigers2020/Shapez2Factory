# Epic D — Trace / NDJSON / summary 계층 격리

**역할:** replay·NDJSON·`solver_summary`를 **출력·디버그·보고** 계층으로만 두고, 라우팅·placement의 **1차 입력**이 되지 않게 한다.

## 원칙

```text
solver_summary, replay_events, NDJSON 파일 = UI / 리포트 / 회귀 비교 / 오프라인 감사
알고리즘 핵심 입력 = decoded map, placement records, routing_state, goal sets 등
```

## 금지 예시

```text
STEP4가 이전 NDJSON을 읽어 goal set을 바꿈
Pass3가 solver_summary의 rollup만 보고 정책 분기
Recovery가 trace rollup을 primary state처럼 사용
```

## 상세 티켓

| 문서 | 내용 |
|------|------|
| [06_replay_timeline_frames.md](./06_replay_timeline_frames.md) | 타임라인 프레임·§16.2 |
| [16_replay_trace_solver_summary_layer.md](./16_replay_trace_solver_summary_layer.md) | read path 차단·계약 |

## 완료 조건(요약)

- 알고리즘 모듈에서 NDJSON/`solver_summary` **read** 경로가 없거나, `scripts/`·리포트 전용으로 격리되어 문서화됨.
