# 07 — STEP 3: Pass2 internal fill (§8)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 06

---

## 8. STEP 3 — Pass2: Internal Fill Placement

### 8.1 목적

Pass1 이후 남은 내부 mineable area를 추가 활용한다.

```text
Pass1: 외곽 우선 배치
Pass2: 남은 내부 공간 보강 배치
```

Pass2 extractor 후보도 **이미 존재하는 belt/pipe와의 연계·공용**을 배치 평가에 넣을 수 있다(§3.1, [`01_project_overview.md`](./01_project_overview.md)).

---

### 8.2 Pass2에서 회피해야 하는 대상

```text
Pass2 시점에 존재하는 blocked cells:
- Pass1 extractor cells
- Pass1 extension cells
- Pass1 fixed output stub cells
- hard barrier cells
- 기존 blueprint에서 반드시 보존해야 하는 외부 구조물
```

```text
Pass2 시점에 존재하지 않는 것:
- STEP 4 final route cells
- Pass3 rerouted cells
```

```text
Pass2에서 occupied로 처리하면 안 되는 것:
- cheap_transport_escape_exists()가 사용한 임시 escape path
```

---

### 8.3 Pass2에서 해야 할 일

```text
1. Pass1 결과의 extractor/extension/output_stub cells를 고정한다.
2. fixed occupied cells를 제외한 mineable cell에서 후보를 만든다.
3. 남은 mineable cell에 extractor + extension bundle 후보를 생성한다.
4. cheap escape 가능성이 없는 후보는 낮은 priority 또는 reject 처리한다.
5. 후보 commit은 final route 확정 전 provisional placement commit이다.
6. 실제 route 가능성은 STEP 4 merge-aware routing에서 확정한다.
```

### 8.3.1 Pass2 번들 패킹 옵티마이저 (CP-SAT / greedy fallback)

내부 채움 단계에서 **순차 greedy commit 대신**, Pass1·장벽 기준선으로 생성한 모든 feasible ``Pass2BundleCandidate`` 풀을 만든 뒤, **셀 겹침이 없도록** 부분집합을 고른다.

- **점유 셀**: 각 후보의 ``extractor_cell``·``output_stub_cell``·각 extension 타일(``PlacementBundle`` geometry와 동일).
- **선택기**: OR-Tools CP-SAT가 설치되어 있으면 set packing으로 목적함수(정수 스케일된 score)를 최대화한다. **CP-SAT는 선택 의존성**이며, 미설치·시간 제한·비정상 종료 시 **결정적 greedy fallback**으로 동일 계약을 유지한다.
- **금지**: STEP 4 라우팅 수행·``final_route_cells`` 참조·``ROUTED_CONFIRMED`` 생성·replay/NDJSON을 알고리즘 입력으로 사용. 선택된 번들은 여전히 **PROVISIONAL_PLACED**만 사용한다.
- **cheap escape**: 기존과 같이 feasibility / scoring probe일 뿐, escape 경로를 occupied transport로 취급하지 않는다.

---

### 8.4 Pass2에서 하지 말아야 할 일

```text
- 내부 void를 새 mining field로 변환하지 않는다.
- cheap escape path 전체를 route처럼 occupied 처리하지 않는다.
- 외부 연결이 불가능한 단독 extractor를 억지로 배치하지 않는다.
- 채굴기 하나만 멀리 두고 긴 pipe만 연결하는 저효율 패턴을 방치하지 않는다.
```

---

### 8.5 route overlap 문제의 단계별 재정의

| 발생 시점                  | 올바른 설명                                     | 해결 위치                                          |
| ---------------------- | ------------------------------------------ | ---------------------------------------------- |
| Pass2 전                | final route는 아직 없으므로 route overlap 문제가 아님  | Pass2 blocked set 정리                           |
| STEP 4 이후 Reclaim loop | 기존 final route 위에 신규 placement가 올라갈 수 있음   | Reclaim placement에서 final_route_cells 제거       |
| Pass3 이후               | rerouted transport와 신규 placement가 충돌할 수 있음 | zone map 갱신 + incremental routing + validation |

`route_cells_pass를 mineable_cur에서 제거`하는 규칙은 **Pass2 일반 단계가 아니라 Reclaim placement loop와 incremental placement 단계에 적용**한다.

---

## Stabilization-P1 (2026-05-09): Pass2 번들 커밋 게이트

Pass2 spine·내부 보강 배치가 생기면 번들 커밋은 `try_commit_pass2_bundle`만 경유한다. Pass1과 동일하게 probe 성공 전 `transport_cells` / `blocked_cells` 직접 갱신은 금지. 계약·트레이스 구분은 [`06_step2_pass1_placement.md`](./06_step2_pass1_placement.md) § Stabilization-P1과 같다.

---

