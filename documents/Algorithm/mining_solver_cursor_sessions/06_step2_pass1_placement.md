# 06 — STEP 2: Pass1 outer-first placement (§7, P1)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 05

---

## 7. STEP 2 — Pass1: Outer-First Placement

### 7.1 목적

소행성 외곽부터 extractor bundle을 배치한다.

```text
목표:
- 외곽에서 외부로 나가기 쉬운 extractor를 우선 배치
- output stub를 확정
- 실제 route가 아니라 escape feasibility를 확인
- 내부 공간을 지나치게 막지 않는 초기 layout 생성
- **이미 존재하는 belt/pipe**와 **연계·공용**할 수 있는 후보를 배치 평가에 포함한다(§3.1, [`01_project_overview.md`](./01_project_overview.md))
```

---

### 7.2 원래 설계

```text
1. 동/서/남/북 외부 방향 후보를 선택한다.
2. 소행성 외곽을 기준으로 extractor 후보를 만든다.
3. extractor는 void 또는 외부 연결이 가능한 방향을 향한다.
   (주변에 저비용 탈출 후보가 여러 방향이면, [`01_project_overview.md`](./01_project_overview.md) §3.5 **output 방향(회전) 탐색**처럼 후보별 비용을 두고 돌릴 수 있다.)
4. extractor output 앞에 belt/pipe stub를 둔다.
5. **Pass1 extension topology (정본, 2026-05-14 갱신)**:
   - **기본**: extractor **output 반대 방향**으로 **1자형(straight) extension chain**을 우선한다(최대 3칸).
   - **출력 반대 ↔ 체인 방향**: output이 북(N)이면 체인은 남(S)으로만 이어진다. 동(E)이면 서(W), 남(S)이면 북(N), 서(W)이면 동(E).
   - **branching(ㅗ/ㅓ/ㅏ 등 3방 동시 전개)**는 Pass1 **기본 전략이 아니다**. 직선 체인이 막힐 때만 **fallback**으로 고려하거나, Pass2·후속 최적화 정책에 둔다.
6. 12시 방향부터 시계 방향으로 scan한다.
7. 후보 bundle을 배치하고 occupied map을 갱신한다.
8. **이미 존재하는 belt/pipe**와 연계·공용(merge) 가능한 후보는 평가·정렬에 반영한다(§3.1).
```

> **정본 vs 현재 v2 구현(고지)**: `asteroid_mining_layout_v2/placement/`의 Pass1 구현은 별도 배치 패치 전까지 **이전 generator(출력 제외 3방 + extension-to-extension BFS)**를 따를 수 있다. 본 §7.2·§7.5는 **목표 정책**이며, 구현을 바꿀 때 이 정본에 맞춘다.

### 7.1.1 좌표 격자 (STEP1과 동일)

```text
Pass1 입력 ``mineable_placement_cells``에는 **X==0 식별자가 없다**(STEP1 §6.2.1).
누락은 **라벨 규칙**이지 인접 열 사이 **물리 void**가 아니다.
escape BFS 등은 ``asteroid_bbox`` ± margin 창으로만 경계를 제한한다.
```

---

### 7.3 Pass1에서 확정되는 것과 확정되지 않는 것

| 구분                | 의미                                   | Pass2에서 blocked인가? |
| ----------------- | ------------------------------------ | -----------------: |
| extractor cell    | 실제 배치된 extractor                     |                  예 |
| extension cell    | 실제 배치된 extension                     |                  예 |
| output stub cell  | extractor output 앞 필수 belt/pipe cell |                  예 |
| cheap escape path | 연결 가능성 검사에 사용한 임시 탐색 경로              |                아니오 |
| final route       | STEP 4에서 확정되는 실제 route               |      Pass1 시점에는 없음 |

중요:

```text
cheap_transport_escape_exists()가 찾은 경로는 실제 route가 아니다.
따라서 Pass2에서 cheap escape path 전체를 occupied로 처리하면 안 된다.
```

---

### 7.4 권장 구현 윤곽(백지 전제)

Pass1은 **문서 정본(§0, `01_project_overview.md`)** 만을 따른다. 아래는 그에 맞춘 **절차 예시**이며, 함수명·모듈명은 고정이 아니다.

```text
- mineable cell을 extractor core 후보로 검사
- rotation 4방향 검사
- output cell이 barrier가 아닌지 확인
- cheap_transport_escape_exists()로 외부 연결 가능성 사전 검사
- beam search로 점수가 높은 placement 조합 유지
```

---

### 7.5 구현 시 스펙 정합 포인트

```text
- Pass1 extension topology **정본 정책**: **straight-chain-first** — output **반대** 방향으로 최대 3칸의 1자 체인을 우선한다. 각 extension은 여전히 **직계 parent**를 향해 orientation을 맞춘다.
- **Branching**(출력 제외 3방에 동시에 붙이거나, extension에서 갈라지는 ㅗ/ㅓ/ㅏ 형태)은 Pass1 **기본 목표가 아니다**. 직선 체인이 불가할 때의 **fallback** 또는 Pass2·후속 단계 정책으로만 둔다.
- output stub 방향은 예약(출력 방향)이며, stub·cheap escape·STEP4 경계는 기존 불변과 동일하다.
- Pass1과 Pass2의 책임 경계를 코드·문서에서 명확히 한다.
```

---


---

## Stabilization-P1 (2026-05-09): 번들 커밋 게이트

Pass1 배치 루프는 **extractor + extension(최대 3) + output stub** 번들 단위로 레이아웃을 갱신한다.

**v2 구현 정본 경로** (레포 활성 코드 — 문서 앵커는 아래만 본다):

- `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py` — `run_pass1_outer_placement`, `_build_candidate`, `_candidate_to_bundle`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/bundle_candidate.py` — `grow_extension_cells`, `side_directions_after_output`

**레거시 v1** (`try_commit_pass1_bundle`, `Pass12BundleCandidate`, `Pass12LayoutScratch` 등): 아카이브·역사 참고 전용. 동일 불변을 구현했더라도 **모듈 경로·타입명은 v2와 다르다**; 온보딩·감사 시 v1 경로를 현재 정본으로 착각하지 않을 것.

**`PlacementCommitState`와 output stub (§9.6 정합, B안)**: FSM 엔트리(`placement_commit_entries`)는 **장비 타일**인 extractor·extension의 `placement_id`만 대상으로 한다. `output_stub`은 extractor에 종속된 **고정 출력 인접 셀**이며 별도 `placement_id`·FSM 행을 두지 않는다. stub 점유·라우팅 앵커는 `Pass1Result`의 `output_stub_cells`·`occupied_cells` 등 DTO 필드로 추적한다.

**Pass1 extension topology (정본, §7.2·§7.5와 동일)**: 구현체는 **`grow_extension_cells` 등**으로 번들을 만들지만, **목표 정책**은 **output 반대 방향 1자 체인 최대 3칸**을 우선하고, 3방 branching·ㅗ/ㅓ/ㅏ 기본형은 **채택하지 않는다**(fallback은 별도 규칙). 코드가 아직 구 정책을 따를 때는 본 절을 **승격 기준**으로 삼는다.

**프로브 vs 커밋**: v2 Pass1은 `cheap_escape_feasible` 등 **탈출 가능성 프로브만** 수행하고, `SolverRunContext` 및 STEP 4 라우팅 geometry는 Pass1 본문에서 변형하지 않는다(`pass1_outer` 모듈 독스트링). v1에서 `Pass12LayoutScratch`로 막던 “route probe 성공 전 transport/blocked 무잔류” 의도는 이 분리로 대응한다.

v1 구현에서 `stub_cell`이 합성 transport 집합 밖이면 `bundle_reject_invalid_stub`, 외부 경로 없으면 `bundle_reject_no_route` 등으로 남기던 trace는 **아카이브 구현 참고**로만 본다.

---

## 부록: P1 체크리스트 (원문 §20)

### P1 — Extension Candidate Generator 교체

```text
[ ] Pass1 topology 정본: **output 반대 방향 straight-chain-first**, 최대 3 extension(각 칸은 parent-facing orientation).
[ ] 3방 동시 branching·ㅗ/ㅓ/ㅏ 형태를 Pass1 **기본 전략으로 두지 않는다**(직선 불가 시 fallback 또는 Pass2·후속 정책).
[ ] output 방향은 stub 전용으로 예약·belt/pipe와의 정합 유지
[ ] 최대 3 extension 제한 유지
[ ] canonical signature로 중복 후보 제거
[ ] extractor당 extension 효율 점수화(직선 체인 길이·외곽 거리 등 정본 가중과 정합)
```
