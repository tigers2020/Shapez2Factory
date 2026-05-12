# 채굴 솔버 spatial authority (요약)

## 목적

`mining_map`, `Pass12LayoutScratch`, `routing_state` 보호 회랑, `route_zone` 등이 동시에 존재할 때 **어느 표현이 어느 단계의 정본인지**를 고정해 map desync를 예방한다.

## 단계별 정본

| 단계 | 정본 | 비고 |
|------|------|------|
| Pass1/Pass2 진행 중 | `Pass12LayoutScratch`의 `transport_cells`, `blocked_cells`, `placement_records` | 행 리스트는 `_merge_pass1_into_rows` 이후에야 스크래치와 정합 |
| Pass2 병합 직후 | `mining_map` 행 리스트 | 타임라인 Pass2 프레임 |
| STEP4 처리 중 | `step4_merge_routing` 내부 `cells` dict (입력 맵의 복사) | 성공 시 행 리스트로 반영; 예외 시 스냅샷 복원 |
| STEP4 완료 후 | `mining_map` + 행 메타(`placement_commit_state` 등) | |
| Pass3 | 커밋된 `mining_map` | |
| P4 reclaim | `SolverMutationTransaction.working_map` | 롤백 시 baseline 행으로 복귀 |
| 보호 회랑(soft/hard) | `routing_state` | STEP4 확정 루트에서 **파생**된 정책 오버레이; 별도 벨트 그래프가 아님 |

## 코드 진입점

- [`django_apps/shapez_asteroid/services/asteroid_mining_layout/spatial_authority.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/spatial_authority.py): `authority_note_for_phase`, `assert_scratch_transport_subset_of_map`.

## 후속

더 강한 불변식(예: STEP4 직후 `transport_coords_from_mining_map` vs `routing_state` 풀 교차 검증)은 비용·거짓 양성을 피하기 위해 별도 플랜에서 단계적으로 추가한다.

`route_id`·경로 소유 역인덱스 등 **그래프 권위** 방향은 [route_graph_authority_2026-05-10.md](route_graph_authority_2026-05-10.md) 참고.
