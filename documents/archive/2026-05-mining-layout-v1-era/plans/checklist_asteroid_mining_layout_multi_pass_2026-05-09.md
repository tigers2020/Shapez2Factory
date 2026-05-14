# 소행성 채굴 레이아웃 멀티패스 체크리스트 (정본)

**역할**: Solver Architecture Reviewer 판정 반영 (2026-05-09).

**정정 요지**

- **내부 void filling은 2차 알고리즘에 없음.** inferred mining field 변환은 decode / map reconstruction·timeline 시각화 쪽 개념이다.
- **3차는 중앙 belt 제거가 아니라**, 줄일 수 있는 belt/pipe를 줄이고 고가치 mining-priority 공간 위 transport를 외곽·저가치 셀로 재구성하는 최적화다.
- 핵심 유지: 소행성 **내부 transport cost를 높게** 두고 **fixed stub은 예외** 처리한다.

---

## 삭제된 항목 (2차에서 넣지 않음)

다음은 decode 후 map reconstruction / timeline 시각화 개념이며 **2차 배치 알고리즘 체크리스트에서 제외**한다.

```text
[ ] 외부와 연결되지 않은 내부 void 후보 탐색
[ ] 내부 void를 inferred mining field로 변환 가능 여부 확인
[ ] shape/fluid dominant surface 추정
[ ] accepted_inferred_field_count
[ ] inferred_shape_field_count
[ ] inferred_fluid_field_count
```

---

# 1차 Scan — 외곽 채굴 배치

## 목적

```text
소행성 외곽을 따라 extractor + extension bundle을 배치하고,
각 extractor output을 외부 방향 transport와 연결한다.
```

## 1A. 외곽 후보 스캔

```text
[ ] 소행성 field 좌표 집합 로드
[ ] field cell 중 외곽 boundary cell 탐색
[ ] 각 boundary cell의 4방향 void/outside 접촉 검사
[ ] extractor가 void/outside 방향으로 output을 낼 수 있는지 확인
[ ] output 앞 1칸 stub 설치 가능 여부 확인
[ ] extractor footprint 충돌 검사
```

### 결과값

```yaml
pass1_boundary_scan:
  boundary_cell_count: int
  extractor_candidate_count: int
  rejected_no_void_side: int
  rejected_output_blocked: int
  rejected_collision: int
```

---

## 1B. Extractor 배치

```text
[ ] 12시 방향에서 시작해 시계 방향 순회
[ ] 지정 cardinal order 적용
[ ] extractor 방향 결정
[ ] extractor body 배치
[ ] output stub 1칸 예약
[ ] occupied map 업데이트
```

### 결과값

```yaml
pass1_extractors:
  placed_extractor_count: int
  placed_shape_extractor_count: int
  placed_fluid_extractor_count: int
  fixed_stub_count: int
```

---

## 1C. Extension 배치

```text
[ ] extractor당 extension 최대 3개 제한
[ ] extractor output 방향 제외 3방향 후보 생성
[ ] extension은 extractor 또는 extension을 향하도록 배치
[ ] extension chain 연결성 확인
[ ] extension 충돌 검사
[ ] occupied map 업데이트
```

### 결과값

```yaml
pass1_extensions:
  placed_extension_count: int
  full_3_extension_bundle_count: int
  partial_bundle_count: int
  avg_extensions_per_extractor: float
  rejected_extension_collision: int
  rejected_extension_no_connection: int
```

---

## 1D. 1차 Transport 연결

```text
[ ] 각 extractor output stub에서 외부 anchor까지 pipe/belt 연결
[ ] 외부는 소행성 좌표 밖 최소 5칸 이상으로 확장
[ ] transport가 extractor/extension body와 겹치지 않음
[ ] 모든 output이 external network에 연결됨
```

### 결과값

```yaml
pass1_transport:
  transport_cell_count: int
  belt_cell_count: int
  pipe_cell_count: int
  connected_output_count: int
  disconnected_output_count: int
  internal_transport_cell_count: int
  boundary_transport_cell_count: int
  outside_transport_cell_count: int
```

---

# 2차 Scan — 내부 Spine 기반 배치

## 목적

```text
1차 외곽 배치 후 남은 내부 공간에서,
extension 쪽부터 외부로 직통하는 spine pipe/belt를 만들고,
그 spine 양쪽으로 extractor와 extension을 추가 배치한다.
```

중요:

```text
2차는 내부 void를 inferred mining field로 바꾸는 단계가 아니다.
2차는 spine transport를 먼저 만들고, spine 주변에 채굴 bundle을 붙이는 단계다.
```

---

## 2A. 내부 진입점 / Extension Anchor 탐색

```text
[ ] 1차 배치 결과에서 내부 방향으로 확장 가능한 extension 후보 탐색
[ ] 기존 extractor/extension body와 충돌하지 않는 내부 anchor 선택
[ ] anchor에서 외부 방향으로 직통 spine을 낼 수 있는 방향 후보 계산
[ ] spine 방향별 길이와 충돌 비용 계산
[ ] spine이 extractor/extension body를 관통하지 않는지 확인
```

### 결과값

```yaml
pass2_anchor_scan:
  internal_anchor_candidate_count: int
  valid_spine_anchor_count: int
  rejected_anchor_collision: int
  rejected_no_spine_direction: int
```

---

## 2B. Spine Pipe/Belt 생성

```text
[ ] 선택된 internal anchor에서 외부 방향으로 spine route 생성
[ ] spine은 가능하면 직선 우선
[ ] spine 길이는 anchor에서 외부 연결까지 계산
[ ] spine은 extractor/extension body와 겹치지 않음
[ ] spine 양쪽에 배치 공간을 남기는지 확인
[ ] spine output이 external network와 연결됨
```

### 결과값

```yaml
pass2_spine:
  spine_count: int
  spine_transport_cell_count: int
  spine_internal_cell_count: int
  spine_boundary_cell_count: int
  spine_outside_cell_count: int
  spine_connected_to_external: bool
  rejected_spine_collision: int
```

---

## 2C. Spine 양쪽 Extractor 후보 스캔

```text
[ ] spine 좌우 양쪽 cell을 기준으로 extractor 후보 생성
[ ] extractor output이 spine을 향하도록 방향 설정
[ ] extractor body가 mining field 위에 있는지 확인
[ ] extractor output stub가 spine과 연결 가능한지 확인
[ ] 기존 occupied 및 spine transport와 충돌하지 않는지 확인
```

### 결과값

```yaml
pass2_spine_extractor_candidates:
  candidate_extractor_count: int
  candidate_shape_extractor_count: int
  candidate_fluid_extractor_count: int
  rejected_not_mining_field: int
  rejected_output_not_to_spine: int
  rejected_collision: int
```

---

## 2D. Spine 양쪽 Extension 후보 스캔

```text
[ ] 각 extractor 뒤쪽/측면 extension 후보 계산
[ ] extractor당 extension 최대 3개 제한
[ ] extension이 extractor 또는 extension chain에 연결되는지 확인
[ ] extension이 spine transport와 겹치지 않는지 확인
[ ] extension 배치 시 추가 extractor 후보를 막는지 평가
```

### 결과값

```yaml
pass2_spine_extension_candidates:
  candidate_extension_count: int
  candidate_full_bundle_count: int
  candidate_partial_bundle_count: int
  rejected_extension_collision: int
  rejected_extension_no_connection: int
  rejected_blocks_higher_value_candidate: int
```

---

## 2E. Spine 기반 Bundle 배치

```text
[ ] extractor + 최대 3 extension을 bundle로 평가
[ ] spine 양쪽에서 높은 score bundle부터 배치
[ ] bundle 간 충돌 검사
[ ] extractor output stub가 spine과 직접 연결되는지 확인
[ ] 배치 후 occupied map 업데이트
```

### 결과값

```yaml
pass2_placement:
  placed_extractor_count: int
  placed_extension_count: int
  placed_full_bundle_count: int
  placed_partial_bundle_count: int
  connected_to_spine_output_count: int
  failed_to_connect_to_spine_count: int
```

---

## 2F. 2차 결과 검증

```text
[ ] spine이 외부 network와 연결됨
[ ] spine 양쪽 extractor output이 spine에 연결됨
[ ] extractor/extension/transport overlap 없음
[ ] extractor당 extension 수 <= 3
[ ] 2차 spine이 지나치게 내부 mining-priority 공간을 낭비하는지 metric 기록
```

### 결과값

```yaml
pass2_result:
  total_pass2_extractor_count: int
  total_pass2_extension_count: int
  total_pass2_transport_count: int
  pass2_internal_transport_count: int
  pass2_spine_count: int
  pass2_spine_avg_length: float
  pass2_spine_max_length: int
  pass2_collision_count: int
  pass2_disconnected_output_count: int
```

---

# 3차 Scan — Transport Cost Reduction / Mining-Priority Reconstruction

## 목적

```text
2차 결과의 spine과 branch transport를 모두 없애는 것이 아니라,
줄일 수 있는 belt/pipe를 줄이고,
고가치 mining-priority 공간 위의 transport를 외곽/저가치 셀로 밀어낸다.
```

중요 수정:

```text
잘못된 표현:
내부 중앙 belt/pipe 제거

정확한 표현:
내부 중앙 belt/pipe 중 줄일 수 있는 부분을 줄이고,
필요한 연결은 유지하되 더 싼 route로 재구성한다.
```

---

## 3A. Pass2 Snapshot 보존

```text
[ ] pass2 최종 layout snapshot 저장
[ ] pass2 extractor/extension/transport map 저장
[ ] pass2 spine 정보 저장
[ ] pass2 score 저장
[ ] pass3 candidate layout을 별도로 생성
```

### 결과값

```yaml
pass3_snapshot:
  pass2_extractor_count: int
  pass2_extension_count: int
  pass2_transport_count: int
  pass2_internal_transport_count: int
  pass2_spine_count: int
  pass2_score: float
```

---

## 3B. Transport 분류

```text
[ ] extractor output 바로 앞 1칸은 fixed_stub로 분류
[ ] spine 중 반드시 필요한 segment와 줄일 수 있는 segment 분리
[ ] branch transport 중 중복/우회/고비용 segment 분류
[ ] external anchor와 외곽 trunk 분류
[ ] extractor/extension body는 blocked로 유지
```

### 결과값

```yaml
pass3_transport_classification:
  fixed_stub_count: int
  required_spine_segment_count: int
  reducible_spine_segment_count: int
  reducible_branch_segment_count: int
  high_cost_internal_transport_count: int
  external_trunk_count: int
```

---

## 3C. Cost Map 생성

```text
[ ] 소행성 내부 mining field 위 transport cost를 높게 설정
[ ] spine 양쪽 extractor/extension 후보 공간 cost를 매우 높게 설정
[ ] 외곽/void/이미 배치 불가 셀 cost를 낮게 설정
[ ] fixed_stub cost는 0 또는 start node 처리
[ ] blocked body는 INF 처리
```

### Cost Tier

```yaml
route_cost_tier:
  outside: 1
  boundary_void: 5
  low_value_void: 10
  internal_transport_reuse: 25
  internal_void: 50
  mining_candidate_space: 150
  extension_candidate_space: 200
  extractor_candidate_space: 300
  blocked: INF
  fixed_stub: 0
```

---

## 3D. 줄일 수 있는 Transport 후보 계산

```text
[ ] 현재 pass2 transport cell별 cost 계산
[ ] cost가 높은 spine/branch segment 탐색
[ ] 같은 connectivity를 더 적은 내부 transport로 유지할 수 있는지 후보 생성
[ ] 기존 segment 제거 시 끊기는 output 목록 계산
[ ] 제거/축소 가능한 segment만 reroute 대상 등록
```

### 결과값

```yaml
pass3_reduction_candidates:
  reducible_transport_count: int
  reducible_internal_transport_count: int
  high_cost_transport_count: int
  affected_output_count: int
  non_reducible_required_transport_count: int
```

---

## 3E. Weighted Rerouting

```text
[ ] fixed_stub는 유지
[ ] required spine segment는 유지 가능
[ ] reducible segment만 rerouting 대상
[ ] 외곽/저가치 route를 우선 탐색
[ ] 기존보다 내부 transport cost가 낮은 경우만 후보 채택
[ ] 연결 실패 시 기존 segment 유지
```

### Priority

```python
priority = (
    internal_transport_count,
    mining_candidate_block_score,
    extractor_candidate_block_score,
    extension_candidate_block_score,
    total_route_cost,
    turn_count,
    path_length,
)
```

### 결과값

```yaml
pass3_rerouting:
  reroute_attempt_count: int
  reroute_success_count: int
  reroute_failed_count: int
  kept_original_segment_count: int
  removed_transport_count: int
  added_transport_count: int
  net_transport_delta: int
  internal_transport_delta: int
  mining_candidate_block_score_delta: float
```

---

## 3F. 재배치 Scan

```text
[ ] rerouting 후 비워진 고가치 내부 cell 계산
[ ] 새 route가 막지 않는 extractor 후보 재스캔
[ ] extension 후보 재스캔
[ ] 추가 bundle 배치 가능성 평가
[ ] 추가 bundle이 실제 score gain을 만드는 경우만 candidate에 반영
```

### 결과값

```yaml
pass3_replacement_scan:
  freed_high_value_cell_count: int
  new_extractor_candidate_count: int
  new_extension_candidate_count: int
  new_full_bundle_candidate_count: int
  placed_extra_extractor_count: int
  placed_extra_extension_count: int
  placed_extra_full_bundle_count: int
```

---

## 3G. Throughput / Connectivity 검증

```text
[ ] 모든 extractor output이 external network와 연결됨
[ ] spine을 줄인 후에도 network disconnected 없음
[ ] pipe/belt 종류별 network 분리 유지
[ ] 한 segment에 load가 과도하게 몰리지 않는지 확인
[ ] bottleneck score 계산
```

### 결과값

```yaml
pass3_connectivity:
  transport_connected: bool
  connected_output_count: int
  disconnected_output_count: int
  max_segment_load: float
  over_capacity_segment_count: int
  bottleneck_score: float
```

---

## 3H. Score 비교 및 Commit

```text
[ ] pass2 score와 pass3 candidate score 비교
[ ] yield gain 계산
[ ] transport cost 감소량 계산
[ ] 내부 transport 감소량 계산
[ ] route length 증가량 계산
[ ] pass3가 이득이면 commit
[ ] pass3가 손해거나 동일하면 rollback
```

### Score

```python
score =
    produced_resource_value
  + placed_extractor_value
  + placed_extension_value
  - occupied_mining_space_cost
  - belt_pipe_cost
  - bottleneck_cost
  - excessive_length_cost
```

### 결과값

```yaml
pass3_score:
  pass2_score: float
  pass3_score: float
  score_gain: float
  yield_gain: float
  belt_pipe_cost_delta: float
  internal_transport_delta: int
  route_length_ratio: float
  committed: bool
  rollback_reason: string | null
```

---

# 최종 결과값

```yaml
final_result:
  total_extractor_count: int
  total_extension_count: int
  total_transport_count: int
  total_internal_transport_count: int
  total_boundary_transport_count: int
  total_outside_transport_count: int

  pass1_extractor_count: int
  pass1_extension_count: int
  pass1_transport_count: int

  pass2_added_extractor_count: int
  pass2_added_extension_count: int
  pass2_added_transport_count: int
  pass2_spine_count: int
  pass2_internal_transport_count: int

  pass3_removed_transport_count: int
  pass3_added_transport_count: int
  pass3_net_transport_delta: int
  pass3_internal_transport_delta: int
  pass3_added_extractor_count: int
  pass3_added_extension_count: int
  pass3_score_gain: float
  pass3_committed: bool
```

---

# 최종 합격 조건

```text
[ ] 모든 extractor output이 외부와 연결됨
[ ] extractor/extension/transport overlap 없음
[ ] extractor당 extension <= 3
[ ] 2차 spine이 정상 생성됨
[ ] spine 양쪽 extractor/extension 배치가 정상 연결됨
[ ] 3차에서 줄일 수 있는 transport만 줄임
[ ] required spine/fixed_stub는 유지됨
[ ] pass3 결과가 pass2보다 나쁘면 rollback됨
[ ] pass3 결과가 pass2보다 좋으면 commit됨
[ ] 최종 결과값에 transport 감소량과 yield gain이 기록됨
```

---

## 수정 요약

```text
1차 = 외곽 extractor/extension 배치 + 외부 연결
2차 = 내부 extension anchor에서 외부 직통 spine 생성 + spine 양쪽 배치
3차 = transport 제거가 아니라 고비용 내부 transport 축소/재구성
```

| 항목 | 기존 체크리스트 문제 | 수정 판정 |
|------|---------------------|-----------|
| 2차 내부 void 탐색 | 현재 알고리즘 의도와 다름 | 삭제 |
| 2차 inferred mining field 변환 | decode/map reconstruction 단계 개념 | 삭제 |
| 2차 spine 생성 | 누락 | 추가 |
| 2차 spine 양쪽 배치 | 누락 | 추가 |
| 3차 중앙 belt 제거 | 표현이 과함 | 「줄일 수 있으면 줄임」으로 수정 |
| 3차 목적 | transport 제거로 오인 | mining-priority 공간 보존 중심으로 수정 |

---

## 관련 문서

- 입력 매핑·repair·timeline frame id: [`plan_asteroid_mining_layout_solver_inputs_2026-05-08.md`](plan_asteroid_mining_layout_solver_inputs_2026-05-08.md)
