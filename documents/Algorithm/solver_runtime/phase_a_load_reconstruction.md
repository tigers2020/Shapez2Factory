---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: A
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/phase_b_optimization_input.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase A — Load Reconstruction Map

## 목적

DB에 저장된 reconstruction 결과를 solver 입력으로 로드한다.

## 입력

```text
Reconstruction map full_map
cell rows
bbox
existing layout metadata
resource kind metadata
```

## 산출물

```text
LoadedReconstructionSnapshot
```

## 작업

1. project의 최신 reconstruction map 조회
2. `full_map` / `bbox` / cell kind 로드
3. 기존 extractor / extension / belt / pipe 좌표 분리
4. raw blueprint 좌표가 남아 있으면 **adapter boundary에서만** server coord로 정규화

## 금지

- optimization 내부에서 raw X/Y 변환 호출
- DB 원본 cell kind 직접 수정
- server x/y 순서대로 실제 설비 설치 ([`00_core_principles.md`](00_core_principles.md) §0.1)

## 완료 조건

- [ ] `LoadedReconstructionSnapshot`이 bbox·셀 행·메타데이터를 보존
- [ ] extractor/extension/transport 좌표가 adapter로 넘길 수 있게 분리됨
- [ ] raw→server 변환이 adapter 밖에서 발생하지 않음

## 필수 테스트

PR1B — adapter·OptimizationInput 통합 테스트는 [`implementation_sequence.md`](implementation_sequence.md) § PR1B 및 [`phase_b_optimization_input.md`](phase_b_optimization_input.md) 참조.

## 관련 코드·문서

- `django_apps/asteroid_lab/adapters/` (decode/reconstruction adapter)
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) — Sequence 1B

## 다음 Phase

→ [`phase_b_optimization_input.md`](phase_b_optimization_input.md)
