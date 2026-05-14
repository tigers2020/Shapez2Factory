---
name: STEP4 hard_protected_ring no_route 검토
overview: >
  no_route_exhausted breakdown에서 dominant_blocker_category가 hard_protected_ring인 경우,
  보호 복도(hard/soft) 의미·출처·STEP4 입력·P4 상호작용·finalize 가정을 문서·로그로 먼저 확정하고,
  hard 완화 없이 우회·soft 원자 치환 등 후속 옵션만 설계한다.
todos:
  - id: wire-audit
    content: solver_pipeline STEP4에 hard_protected_cells 주입 여부·소스 추적
    status: pending
  - id: sample-extract
    content: NDJSON routing_failures에서 hard_protected_ring 샘플 5건 추출 스크립트/절차
    status: pending
  - id: geometry-check
    content: 샘플별 링·트렁크 가시성·soft 치환 가능성 수동/반자동 판정표
    status: pending
  - id: followup-design
    content: 우회 vs 원자 치환 과제 분리 및 승인 게이트
    status: pending
---

# STEP4 `hard_protected_ring` — 보호 복도 장벽 검토 플랜 (2026-05-12)

## 0. 배경·목표

- **관측:** `step4_no_route_exhausted_breakdown.dominant_blocker_category == hard_protected_ring`.
- **코드 정본:** `step4_route_failure_diagnostic._stub_neighbors_all_hard_protected`가 참이면, `blocked_reason_near_stub`의 **모든** 이웃 항목의 `reason`이 **`hard_protected`**이다. 이는 `step4_route_failure_detail._neighbor_block_reason`에서 **`n in hard_extras`**일 때만 부여된다 (`hard_extras` = merge 라우팅의 `hard_protected_cells` 인자).
- **목표:** (1) hard/soft 풀의 **DTO·팩토리·우선순위**, (2) STEP4에서의 **입력 사용 방식**, (3) reclaim·finalize와의 **관계**, (4) 실패 샘플별 **기하·정책 판단**을 정리한 뒤, **hard 의미 완화 없이** 가능한 후속(우회·soft 원자 치환)만 분기한다.

---

## 1. 코드베이스 검토 체크리스트 (§1 요구: DTO / STEP4 / reclaim / 검증)

### 1.1 Protected corridor DTO·팩토리

| 구성요소 | 경로 | 역할 |
|----------|------|------|
| DTO | `reclaim/reclaim_corridor_contracts.py` — `ProtectedCorridorSets`, `ProtectedCorridors` | `hard` / `soft` / `source`, layout hint는 **soft에만** 병합되는 계약 주석 포함 |
| Reclaim용 선택 | `reclaim/reclaim_corridors.py` — `protected_corridors_for_reclaim`, `protected_corridors_read_for_reclaim` | `solver_routing_state` → `pass3_trace` → guarded `touched_*` 순 **소스 우선순위**; `source` 문자열 유지 |
| 라우팅 상태 읽기 | `reclaim/reclaim_corridor_read_factory.py` — `protected_corridors_read_from_routing_state`, `protected_corridors_overlay_from_routing_state` | flat `hard_protected_corridors` / nested `protected_corridors` 병합 규칙 |
| Soft 원자 치환 | `routing/protected_corridor_replace.py` — `try_atomic_replace_soft_corridor` | soft 복도 **치환 시** hard·committed와 충돌 검사; **hard 삭제 없음** |

### 1.2 STEP4에서의 사용 (입력 vs 출력 구분)

| 구분 | 경로 | 내용 |
|------|------|------|
| **입력 (탐색 장벽)** | `step4/step4_merge_routing.py` `run_step4_merge_aware_routing(..., hard_protected_cells=None)` | `hard_extras = frozenset(hard_protected_cells or ())` → `blocked`에 합쳐져 **통과 불가**(stub 제외 규칙은 docstring대로). |
| **실패 상세** | `step4/step4_route_failure_detail.py` `_neighbor_block_reason` | 이웃이 `hard_extras`에 있으면 `reason == "hard_protected"` → breakdown **hard_protected_ring** 후보. |
| **출력 (다운스트림 보존)** | `step4/step4_routing_state.py` `_routing_state_from_committed_routes` | 커밋된 경로로 **stub·경로 끝점을 hard**, 경로 중·merge soft를 **soft**로 넣는 **별 풀**(입력 `hard_protected_cells`와 동일 집합이 아님). |

**감사 필수 항목:** `solver_pipeline/step4.py`의 `run_step4_merge_aware_routing` 호출이 **현재 `hard_protected_cells`를 넘기는지** 여부. 넘기지 않으면 `hard_extras`가 비어 **이론상** `blocked_reason_near_stub`에 `hard_protected`가 찍히기 어렵다. 사용자 로그에 `hard_protected_ring`이 지배이면 **(a) 브랜치에서 인자 연결됨**, **(b) 테스트·로컬 패치**, **(c) 다른 경로로 `hard_extras` 주입** 중 무엇인지 1단계에서 확정한다.

### 1.3 Reclaim·overlay 상호작용

- P4 shadow/scan: `reclaim/reclaim_shadow_scan.py` 등에서 `protected_corridors_read_for_reclaim` → `hard` / `soft`로 mineable_cur·배치 거절 (`reclaim_map_ops._p4_overlap_reject_reason`).
- STEP4 **입력** hard는 “이미 지도에 materialized 된 동종 transport 복도 중 절대 침범 불가”에 가깝고, reclaim 측은 **pass3 이후 맵**과 `routing_state`를 함께 읽는다.
- **혼동 방지:** STEP4 라우팅 **전** 주입 hard와, STEP4 **후** `routing_state`에 기록되는 hard(엔드포인트)는 **다른 단계의 산물**이다.

### 1.4 Final validation 가정

- `solver_pipeline/finalize.py`: `assert_protected_corridors_agree_with_transport_map(routing_state_summary, mining_map, transport_kind=...)` — **보호 좌표가 맵 상에서 해당 `want_role` transport로 실재**하는지 검증 (`placement/spatial_authority.py`).
- 의미: **복도 좌표는 “맵에 없는 허상”이면 안 됨**; soft/hard 완화가 아니라 **일관성** 가드.

---

## 2. 대표 실패 배치 추출 (§2 요구)

**데이터 소스:** `var/asteroid_mining_layout_debug/latest.ndjson` (또는 동일 스키마)의 `routing_failures[]` 행.

**필터:**

- `step4_route_failure_diagnostic.failure_reason == "no_route_exhausted"` 이고,
- `by_breaker_category` 집계와 맞추려면 동일 diagnostic에서 `breaker` 재계산 또는 trunk_load의 `step4_no_route_exhausted_breakdown.dominant_blocker_category == hard_protected_ring` 인 실행만 대상.

**추출 필드 (샘플당):** `placement_id`, `stub_cell`, `extractor_cell`, `transport_kind`, `blocked_reason_near_stub`, `step4_route_failure_diagnostic`의 `protected_hard_count` 등.

**도구:** 기존 `scripts/debug/extract_step4_no_route_exhausted_samples.py`를 **breaker_category == hard_protected_ring** 필터로 확장하거나, 동일 패턴의 소스 전용 스크립트 1개(진단 전용).

---

## 3. 샘플별 분석 템플릿 (§3 요구)

각 샘플(최대 5건)에 대해 아래를 **수동 또는 반자동**(맵 스냅샷 + 좌표)으로 채운다.

| 질문 | 산출 |
|------|------|
| stub 인접 **hard** 좌표 목록 | `blocked_reason_near_stub`에서 `reason == "hard_protected"`인 `cell` |
| 링 밖에 **동종 trunk**(외부 도달 transport) 존재 여부 | 실패 시점 `trunk_cells` / `goal_cells`와의 교차·BFS 가시성(로그에 이미 goal 수가 있으면 정성 판단 + 필요 시 리플레이 맵) |
| **Soft replacement** 안전성 | 인접 이웃이 전부 hard가 아니라 **soft**만 걸린 경우는 별 breaker; 전부 hard면 soft 치환 **해당 없음**. 일부 soft면 `try_atomic_replace_soft_corridor` 전제(맵·pass3_trace·solver_routing_state) 검토는 **후속 과제** |
| **hard를 넘지 않는 우회** 존재 가능성 | stub에서 동종으로 이웃 4칸 중 `ok`가 하나라도 있으면 “순수 링”이 아님 → 분류 재검토; 전부 `hard_protected`이면 **진짜 링** |

---

## 4. 비목표 (§4 요구)

- **즉시 `hard_protected` 완화·예외 삽입** (STEP4 `hard_extras`에서 임의 제거 금지).
- **복도 셀 무분별 삭제**; 치환이 필요하면 **`try_atomic_replace_soft_corridor` 수준의 원자 치환**만 후속 과제로 설계.
- Pass3 / P4 / Reclaim **정책 전면 변경**은 본 검토 범위 밖.

---

## 5. 권장 결론 (§ 기대: recommendation)

| 옵션 | 권장도 | 설명 |
|------|--------|------|
| **Hard 보호 유지** | **기본** | replay·reclaim·finalize 계약의 축; 의미 변경은 데이터 없이 금지. |
| **Local bypass (hard 미침범)** | **조건부 2순위** | `plan_step4_local_bridge_recovery` 계열로 **hard_extras 밖** 목표만 쓰는 보조 탐색; 이미 hard 밖 trunk가 있으면 의미 있음. **hard 관통 불가.** |
| **원자적 protected replacement** | **후속 과제** | soft 전용 primitive + P3 trace 계약; hard는 **치환 대상이 아님**. hard를 건드리는 설계는 **별 승인·리서치** 필요. |

**1차 권장:** **진단·배선 감사만** — `hard_protected_cells`가 실제 파이프라인에서 어디서 merge에 들어가는지, `hard_protected_ring`이 **진짜 기하 링**인지 **분류/데이터 오류**인지부터 분리한다. 그다음에만 local bypass 또는 soft 원자 치환 과제를 티켓으로 쪼갠다.

---

## 6. 후속 구현 시 터치할 수 있는 파일 (참고, 본 문서는 구현 안 함)

- `solver_pipeline/step4.py` — `hard_protected_cells` 연결 여부·소스(`routing_state` vs ELA).
- `step4/step4_merge_routing.py` — 입력 hard와 failure trace.
- `reclaim/reclaim_corridors.py`, `reclaim_corridor_read_factory.py` — 읽기 일관성.
- `routing/protected_corridor_replace.py` — soft 원자 치환만.
- `tests/unit/shapez_asteroid/test_step4_merge_aware_routing_skeleton.py` — 이미 `hard_protected_cells` fixture 존재; 회귀 기준으로 활용.

---

## 7. 검증 (검토 활동 자체)

- 문서·로그 분석 중심 → **pytest 필수 아님**.
- 배선 변경 시: `assert_protected_corridors_agree_with_transport_map` 통과·STEP4 단위 테스트·`test_reclaim_shadow` 일부.

본 문서는 **플랜/검토 전용**이며, hard 완화 없이 사실 관계를 확정한 뒤 후속 구현을 승인받는 것이 목적이다.
