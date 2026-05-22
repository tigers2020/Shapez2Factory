---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: ko
related_docs:
  - asteroid_lab_mining_installation/01_rule_reconciliation.md
---

# 문서 drift matrix — 채굴기·확장기 프로그램

D2 정본 우선순위 대비 **기존 문서** 상태를 추적한다. PR-0에서 `asteroid_lab_0*` 본문을 대량 수정하지 않는다. PR-1·PR-2 허브 산출(`03`·`04`)로 닫힌 조치는 아래 표에 반영한다.

## `drift_type` (고정)

`stale-canon-risk` · `wording-risk` · `ok-but-db-check-needed` · `missing-doc` · `strong-canon`

## 표

| 문서 | status | 주장 요약 | drift_type | 조치 | owner |
|------|--------|-----------|------------|------|-------|
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) | CANON | 처리량 ×4..×16 절대값 | stale-canon-risk | **완료(부분):** `03` rate 테이블 없음·variant 2종; `01` throughput `needs-review` 유지 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) | RESEARCH | linear 0–3 extension; `ExtensionAttachment` | ok-but-db-check-needed | **완료:** `03` footprint·variant; `04` §1·§3 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) | RESEARCH | rim-only; greedy 설치 없음 | wording-risk | **부분 완료:** `04` §핵심·§3; 선택적 `03` 본문 패치 잔여 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md) | RESEARCH | commit-time reprobe; `Gene.commit_order` | strong-canon | **완료:** 유지; `04` §5 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) | RESEARCH | placement ≠ commit; replay 입력 금지 | strong-canon | **완료:** 유지; `04` 인용 | asteroid-lab |
| [`documents/plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md`](../../plans/asteroid_lab_optimization/asteroid_lab_progress_report_2026-05-17.md) | REPORT | 진행 요약만 | ok-but-db-check-needed | 계약으로 취급하지 않음; `00`에서 링크 | asteroid-lab |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | — | replay 스크럽, solver 피드백 | missing-doc | **부분 완료:** `04` §6 이벤트 표; UI per-control 라벨 맵 잔여 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md) | ACTIVE | 통합 lab replay 타임라인 | strong-canon | **완료:** 유지; `04` §6 wire 값 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_09_replay_debug.md`](../asteroid_lab_09_replay_debug.md) | ARCHIVED | dual-track 역사 | ok-but-db-check-needed | CANON으로 인용하지 않음; 고고용 링크만 | asteroid-lab |
| [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) | RESEARCH | 런타임 replay 배선; output-only | strong-canon | **완료:** `04` §6; `09` 보완 | asteroid-lab |

## 갱신 시점

- [x] PR-1: `03` 반영 — `game_rules`·`asteroid_lab_02` 조치 완료(부분)
- [x] PR-2: `04` 반영 — `00`·`07`·`09`·`12`·replay JS 행 부분/완료
- [ ] throughput simulation import 후 `game_rules` `stale-canon-risk` 재평가
- [ ] 선택: `asteroid_lab_03` RESEARCH 본문 rim-only 문구 패치
