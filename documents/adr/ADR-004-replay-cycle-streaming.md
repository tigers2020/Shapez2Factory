---
status: ACCEPTED
owner: solver-architecture
last_reviewed: 2026-05-12
supersedes: []
superseded_by:
related_epics: [replay, trace]
---

# ADR-004: Replay Cycle Streaming

## 결정

Replay는 coarse timeline row보다 solver cycle/event stream을 우선한다.

## 근거

Timeline row는 사용자가 보는 단계 요약이고, solver cycle은 실제 상태 변화 단위다. Replay가 요약 행만 따르면 merge, recovery, reclaim, validation의 세부 상태 전이가 사라져 디버깅과 회귀 분석이 어려워진다.

## 결과

- replay payload는 event/cycle 단위 상태를 보존한다.
- timeline summary는 replay source of truth가 아니라 표시 계층이다.
- trace/replay/summary는 solver decision 입력으로 역참조하지 않는다.
