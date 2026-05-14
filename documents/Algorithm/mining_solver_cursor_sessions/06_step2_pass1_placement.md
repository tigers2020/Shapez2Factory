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
5. output 방향 외 3방향에 extension 후보를 붙인다.
6. 12시 방향부터 시계 방향으로 scan한다.
7. 후보 bundle을 배치하고 occupied map을 갱신한다.
8. **이미 존재하는 belt/pipe**와 연계·공용(merge) 가능한 후보는 평가·정렬에 반영한다(§3.1).
```

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
- extension topology는 **3방향 branching** 목표를 만족해야 하며, straight chain 축소만으로 끝내지 않는다.
- output 방향 제외 3방향 extension 후보 생성을 빠뜨리지 않는다.
- extension-to-extension 연결·branching을 허용한다.
- Pass1과 Pass2의 책임 경계를 코드·문서에서 명확히 한다.
```

---


---

## Stabilization-P1 (2026-05-09): 번들 커밋 게이트

Pass1 배치 루프가 생기면 **extractor+extension+output stub 등 번들 단위**로 레이아웃을 바꿀 때는 다음만 사용한다.

- `django_apps.shapez_asteroid.services.asteroid_mining_layout.pass12_bundle_commit` 의 `try_commit_pass1_bundle`
- 후보가 `Pass12BundleCandidate`로 표현되고, **route probe 성공 전**에는 `Pass12LayoutScratch`의 `transport_cells` / `blocked_cells`를 직접 갱신하지 않는다.

`stub_cell`이 기존 transport와 `new_transport`의 합집합에 들어가지 않으면 라우트 실패가 아니라 후보 생성 버그로 간주되며, trace 메시지 `bundle_reject_invalid_stub`가 기록된다. 실제로 stub는 있으나 외부까지 경로가 없으면 `bundle_reject_no_route`이다.

---

## 부록: P1 체크리스트 (원문 §20)

### P1 — Extension Candidate Generator 교체

```text
[ ] straight chain 축소에 머물지 않고 3방향 topology 목표를 달성한다.
[ ] output 방향 제외 3방향 extension 후보 생성
[ ] extension-to-extension 연결 허용
[ ] extension orientation = parent를 바라보는 방향으로 고정
[ ] 최대 3 extension 제한 유지
[ ] canonical signature로 중복 후보 제거
[ ] extractor당 extension 효율 점수화
```
