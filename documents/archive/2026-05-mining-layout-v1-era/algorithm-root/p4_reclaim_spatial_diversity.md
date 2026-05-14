# P4 reclaim spatial diversity (클러스터링 완화)

## 목적

- `MAX_RECLAIM_SHADOW_SCAN_LIMIT`(16)과 고정 앵커 순서 때문에 동일 perimeter 구역만 평가되는 경향을 줄인다.
- 루프 내 연속 커밋이 같은 trunk/merge 인근에 몰리는 현상을 **search pressure**로 완화한다.

## 고정 원칙

- **`gain_ratio` 임계 비교는 raw만 사용**한다 (`gain_slots / additional_route_cost`).
- diversity 항은 **앵커 스캔 순서**, **수락 후보 정렬(tie-break)**, **트레이스**에만 반영한다.
- `gain_ratio_adjusted`는 관측·정렬 보조용이며 임계에는 사용하지 않는다.

## 상수 (`foundation/constants.py`)

| 이름 | 값 | 의미 |
|------|-----|------|
| `RECLAIM_DIVERSITY_CLUSTER_RADIUS` | 12 | prior 앵커와의 Manhattan 거리 falloff 반경 |
| `RECLAIM_DIVERSITY_CLUSTER_MAX_PRIOR_PENALTY` | 0.08 | prior 하나가 거리 0일 때 falloff 항의 기여 상한에 맞춘 스케일 |
| `RECLAIM_DIVERSITY_CLUSTER_FALLOFF_K` | `MAX / RADIUS` | `max(0, R - d)`에 곱하는 계수 |
| `RECLAIM_ROUTE_ZONE_OVERLAP_PENALTY` | 0.015 | shadow stub 경로 셀 하나당, 이미 커밋된 incremental route zone과 겹칠 때 가중 |

## 패널티 정의

- **앵커 falloff**: 각 prior `p`에 대해 `d = manhattan(anchor, p)`, `local_cluster_density += max(0, R - d)`, `cluster_penalty = local_cluster_density * K_FALL`.
- **route zone overlap**: `shadow_route_path`의 셀 수 가운데 `p4_committed_route_cells_for_zone`(루프 누적 B2 경로)에 포함된 개수 × `RECLAIM_ROUTE_ZONE_OVERLAP_PENALTY`.
- **`total_diversity_penalty`**: `cluster_penalty + route_zone_penalty` (앵커 쪽 비중이 더 크도록 설계).

## `gain_ratio_adjusted` (트레이스·정렬 보조)

- raw가 유한일 때: `gain_ratio / (1.0 + total_diversity_penalty)` (`total`이 0이면 raw와 동일).
- raw가 `inf`이면 `None`.

## 스캔 앵커 순서

- prior가 없으면 기존과 동일: `(y, x)` 오름차순.
- prior가 있으면: `min_d = min_p manhattan(anchor, p)`에 대해 **`-min_d` 오름차순**(멀리 있는 앵커 먼저), tie는 `(y, x)`.

## 트레이스 `p4_diversity`

`p4_reclaim_best_candidate` 하위에 `p4_diversity` dict:

- `min_anchor_distance_to_prior`, `local_cluster_density`, `route_zone_overlap_cells`
- `cluster_penalty`, `route_zone_penalty`, `total_diversity_penalty`, `gain_ratio_adjusted`

## 후순위 (미구현)

- 임계까지 `additional_route_cost`에 패널티를 합산하는 방식은 회귀 면적이 커 별도 실측 후 검토한다.
