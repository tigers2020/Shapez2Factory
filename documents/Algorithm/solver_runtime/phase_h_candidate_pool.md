---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: H
pr: 3
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_03_candidate_generator.md
---

# Phase H — Candidate Pool Build / Dedupe / Truncate

## 목적

geometry + route probe를 통과한 attempt만 **normal candidate**로 만든다.

## 입력

```text
GeometryValidationResult (pass)
RouteProbeResult (reachable)
ProjectedGenePlacement
```

## 산출물

```text
CandidatePool (normal + rejected)
```

## 작업

### Normal candidate 조건

```text
geometry valid
route_probe_result.reachable is True
route_probe_result.reached_goal is not None
```

### Rejected candidate

```text
geometry failure
route_probe unreachable
budget exceeded
no goal cells
```

### Candidate ID

```text
{gene_id}:{anchor_x},{anchor_y}:{rotation}:{transport_kind}
```

### Equivalence key

```text
occupied_cells
route_probe_start
output_dir
transport_kind
base_throughput
topology_signature
```

### Dedupe

동일 key는 `candidate_id` 오름차순 **첫 번째만** 유지.

### Truncate

`max_candidates`가 있으면 dedupe 후:

```text
base_score desc
route_probe_result.cost asc
candidate_id asc
```

## 금지

- placement commit
- unreachable을 normal pool에 포함 ([§0.4](00_core_principles.md))
- server coord 이외 좌표

## 완료 조건

- [ ] normal/rejected 분리 deterministic
- [ ] dedupe 후 truncate 순서 고정
- [ ] generator가 layout을 변경하지 않음

## 필수 테스트

```text
test_candidate_generator_reachable_only_enters_normal_pool
test_candidate_generator_rejects_unreachable
test_candidate_generator_dedupes_before_max_candidates
test_candidate_generator_does_not_commit_placements
test_candidate_generator_uses_server_coords_only
test_candidate_id_is_deterministic
```

## 관련 코드·문서

- 예정: `candidate_dtos.py`, `candidate_equivalence.py`, `candidate_generator.py`
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md)

## 다음 Phase

→ [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)
