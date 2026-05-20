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

동일 `CandidateEquivalenceKey`는 **route_probe 이전**에 `candidate_id` 최솟값 승자만 probe한다.  
probe 후 `dedupe_gene_candidates`는 truncate 전 **2차 안전망**이다.

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

- [x] normal/rejected 분리 deterministic
- [x] dedupe 후 truncate 순서 고정
- [x] generator가 layout을 변경하지 않음

## 필수 테스트

```text
test_candidate_generator_reachable_only_enters_normal_pool
test_candidate_generator_rejects_unreachable
test_candidate_generator_dedupes_before_max_candidates
test_candidate_generator_does_not_commit_placements
test_candidate_generator_uses_server_coords_only
test_candidate_id_is_deterministic
test_dedupe_skips_duplicate_route_probe
test_candidate_generator_exposes_timing
```

## 관련 코드·문서

- 구현: `candidate_dtos.py` (`GeneCandidate`), `candidate_equivalence.py`, `candidate_generator.py`
- 레거시 RESEARCH의 `BundleCandidate` 명칭은 사용하지 않음
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md)

## 다음 Phase

→ [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)
