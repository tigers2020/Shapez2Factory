---
name: 알고리즘 완성도 갭 프로브 (STEP4 / Pass3 / Reclaim)
status: ACTIVE
overview: >
  D5 삭제 정리는 중단하고, 재현 가능한 입력 한 건에 대해 solver_summary·trunk_load·final_validation
  메트릭으로 병목을 분류한 뒤, STEP4 외곽 우선 job 정렬 및 trunk 공유율 관측 필드를 반영한다.
---

# 알고리즘 완성도 갭 프로브 (2026-05-12)

## 1. 재현 입력

| 항목 | 값 |
|------|-----|
| 식별자 | `tests.unit.shapez_asteroid.test_pass1_timeline_integration._decoded_ring_with_interior` |
| 설명 | 3×3 링 8개 ShapeMiner + 외곽 벨트 탈출 한 줄 (Pass1 3건 배치, Pass2 0) |

## 2. Phase 1 메트릭 스냅샷 (변경 전·동일 픽스처 기준 관측)

`solver_summary` / `final_validation` / STEP4 `trunk_load`에서 확인한 값:

| 메트릭 | 값 |
|--------|-----|
| `return_reason` | `ok` |
| `route_cell_count` | 10 |
| `trunk_load.route_metrics.route_cell_visits` | 11 |
| `trunk_load.route_metrics.unique_route_cell_count` | 10 |
| `shared_trunk_reuse_ratio` (파생) | 약 0.0909 (이번 변경으로 `route_metrics`에 명시 저장) |
| `after_internal_transport_count` | 10 |
| `placement_candidate_blocked_count` | 0 |
| `pass3_internal_transport_saved` | 0 |
| `p4_reclaim_candidate_count` | 0 |
| `p4_reclaim_loop_successful_commits` | 0 |
| `net_internal_transport_saved_after_reclaim` | 0 |
| `disconnected_stub_count` | 0 |
| `final_unfinalized_placement_count` | 0 |

Pass3 타임라인 요약: `pass3_connectivity_reject_sample`에 **희생 셀 제거 시 3개 stub 단절** 샘플이 기록됨 → 내부 벨트 일부는 제거 시 연결성이 깨져 Pass3가 합리적으로 이득 0을 유지.

## 3. Phase 2 단일 primary 원인

**1순위: Pass3가 연결성 제약으로 내부 수송 타일을 줄이지 못함** (`pass3_internal_transport_saved` = 0, connectivity reject 샘플 존재).

부수적으로 STEP4는 성공했으나 trunk 공유는 미미(방문 11 대 유일 10). 후속으로 **STEP4 비용·목표 지형**을 더 건드리기 전에, 이번 PR에서는 **외곽 근접 stub 우선 라우팅 순서**로 trunk 시드 품질을 소폭 개선하는 쪽을 택함 (§08 merge-aware 정렬과 정합).

## 4. Phase 3 구현 요약

| 파일 | 변경 |
|------|------|
| [step4_merge_routing.py](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_merge_routing.py) | `exterior_margin_cells` 계산 후 stub→margin 맨해튼 최소 거리 오름차순으로 job 재정렬 |
| [step4_trunk_load.py](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_trunk_load.py) | `route_metrics.shared_trunk_reuse_ratio` 관측 필드 추가 (알고리즘 분기 미사용) |
| 테스트 | `test_step4_merge_routing.py`, `test_step4_trunk_load_contract.py` 갱신·추가 |

## 5. 검증

- `python -m pytest tests/unit/shapez_asteroid/`
- `ruff check .` / `mypy .` / `black --check .`

## 6. 이후 진행

- 동일 픽스처에서 `route_cell_visits`·`shared_trunk_reuse_ratio`가 실제로 개선되는지 대규모 맵에서 재측정.
- Pass3 연결성과 이득을 동시에 보는 후보 평가는 별 PR에서 `pass3_e3_guarded` 쪽으로 한정하는 것이 안전.

## 7. 커밋 메시지 제안

```
feat(shapez_asteroid): STEP4 outside-in job order and trunk reuse ratio

- Sort merge-aware routing jobs by stub distance to exterior margin.
- Add trunk_load.route_metrics.shared_trunk_reuse_ratio (observation-only).
- Extend unit tests for ring fixture and trunk_load contract.
```
