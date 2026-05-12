# Shapez2 Asteroid Mining Solver 개발 진행 보고서 v5.3

**Role: Solver Architecture Reviewer**

---

## 0. 보고서 목적

본 문서는 지금까지 논의·설계해 온 **Shapez2 소행성 채굴 배치 최적화 Solver**의 알고리즘 로직, 요구·진행·리스크, 핵심 제약 조건, 그리고 최종 목표를 정리한 개발 보고서다.

**문서 전제 — 구현 백지**: 본문의 파이프라인·규칙·스키마·상수는 **레포지토리에 solver 코드가 얼마나 들어와 있는지를 가정하지 않는다.** 문서가 **설계 정본**이며, 구현은 이 정본에 맞추어 **새로 작성하거나 기존 코드를 폐기·재배치**해도 된다. 등장하는 모듈명·파일명·함수명은 **배치 예시**일 뿐, 필수 구현 계약이 아니다.

v4에서는 v3 검토 피드백에서 지적된 **control flow 완결성 문제**를 중심으로 수정했다.

v5에서는 v4 문서 검토에서 나온 **세부 정합**(§4.3.1 STEP 5 시점, §12.2 누적 budget, cascade 보정 카운터·컨텍스트 분리, routing 동점 해소 방향, validation_recovery vs STEP 4, trace 필드)을 반영했다.

v5 후속 개정(알고리즘 로직 분석 피드백): **STEP 8 슬롯 vs 비선형 Recovery**, trigger별 복귀 경로 표 정렬, `MAX_POST_RECLAIM_PASS3_RERUNS` 스코프, cascade vs `validation_recovery`, recovery 시 soft corridor 규칙, Pass1 commit 상태, `hard_protected` 승격 시점, `external_margin` 입력 선택 정책, Reclaim budget 규범 단일화, `PlacementCommitState` FSM, gain ratio·Dijkstra tie-break·Pass3 rerun metric 기준선·연결성 검사·replay 스냅샷·내부 DTO 스키마 초안을 명시했다.

v5.1 문서 정합(구현 직전 엣지): **§4.3 단일 정본 표** + §13.2 요약만 유지, Reclaim loop 종료 목록에서 `MAX_VALIDATION_RECOVERY_ATTEMPTS` 제거(파이프라인 전역은 §4.4·§13.1), §12.5 rerun 진입 `net` 시점·`baseline_route_length` 재계산 명시, §12.3 `FINAL_ROUTE`/`SOFT_PROTECTED` 분기·§14.2.1 연결, §9.6 `ROUTED_CONFIRMED` vs **route 단위** 재검증·§9.6 규칙 7 문구 오탈자 수정, §19.1 `reconstruction` 좌표 형·`RecoveryResult.context_chain`, §12.2 gain/비용 단위, §13.3 `merge_partial_failure` 감지 조건, §20.2 ↔ §15.2 연결성 문구 동기화.

v5.2 문서 정합: `pass3_internal_transport_saved`·`baseline_internal_transport_at_reclaim_entry` **동일 시점 스냅샷** 보장, §4.3.1 3번과 §4.3 표 **실패 시** 열 정렬, **`RecoveryResult.context_chain` trace 정본 확정**, `additional_route_cost`에 **output stub 포함** 명시, `beam_trace` 최소 필드, §12.2 budget **평가·누적 2단계** 수식, `mineable_reclaim`에 **soft_protected** 반영, §15.4 **optimization baseline** 정의.

v5.3 문서 정합: §15.4 optimization baseline **기본 측정 시점 고정**(STEP 4 이전), §4.3.1 remedial **Pass3 재시도 실패 시 rollback** 명시, §19.1 **`routing_failures` 원소 스키마**, §12.2 **`pass3_internal_transport_saved` ≤ 0(음수 포함)** budget 분기, §14.2.2 **candidate exhaust** 측정 가능 정의.

v5.4 문서 정합: **STEP 10 실시간 UI streaming** — 솔버 계산 **매 10 cycle**마다 visualization 갱신(§16.1), `computation_cycle` trace·cycle 정의 정본.

v5.5 문서 전제: **solver 구현 백지** — 본 문서군은 기존 코드 완성도를 전제로 하지 않으며, 구현은 설계 정본에 맞춘다(§0 본문).

v5.6 문서 정합: **extractor 배치 시 기존 belt/pipe 연계·공용**(§3.1·§3.5 merge), Pass1 목표 보강.

v5.7 문서 정합: **RouteZone 기본 cost**(`mining_solver_cursor_sessions/03_data_schema_dto.md` §11.1, `PLACEMENT_OCCUPIED` 등).

v5.8 문서 정합: **§3.4 출하량·extension 비례·벨트/스페이스 벨트·유체·구간 누적 유량**, §3.6 capacity 표 갱신.

v5.9 문서 정합: **1차 transport — max capacity 무시·누적 합산만**(§3.4·§3.6·§2.2, 후속에 capacity 검증 선택).

```text
1. Reclaim loop가 Pass3의 내부 transport 절약분을 역행하지 못하도록 budget gate 추가
2. Final validation failure → Recovery 무한 루프 방지를 위한 attempt limit 추가
3. Recovery trigger별 복귀 경로 명시
4. trunk seed 정의 추가
5. Reclaim 이후 zone map 갱신 규칙 추가
6. Pass2 placement commit 후 routing 실패 시 rollback/quarantine 처리 정의
7. baseline route length ratio의 단계별 적용 기준 분리
8. trace의 transport_kind: mixed 모순 해소
9. output stub를 cost 0 cell이 아니라 fixed start point로 확정
10. 외부 판정 5칸 기준을 동적 external margin으로 보완
11. lexicographic Dijkstra 성능 제한 및 fallback 정의
```

---

## 1. 근거 및 신뢰도 평가

| 근거          | 내용                                                                                                 | 신뢰도 |
| ----------- | -------------------------------------------------------------------------------------------------- | --: |
| 기존 알고리즘 논의  | 1차 외곽 배치, 2차 내부 보강, 3차 transport 최적화 방향이 반복적으로 정리됨                                                 |  높음 |
| 목표 소프트웨어 구조 | 파이프라인(§4)·레이어·포트를 만족하는 구현을 **백지 또는 재정렬**로 맞춘다. 레거시 모듈 존재는 본 표의 **신뢰도 근거가 아니다.** |  중간 |
| 사용자가 확정한 규칙 | extractor output, extension 최대 3개, transport overlap 금지, 외부 연결 규칙 등이 명확히 정리됨                       |  높음 |
| 최근 실패 로그 분석 | disconnected transport, budget recovery 실패, terminal overflow recovery 실패, 중앙 pipe/belt 과다 문제가 확인됨 |  높음 |
| v2 피드백      | Pass2 route 회피 대상, Pass3 feedback loop, capacity/recovery/protected corridor 문제가 정리됨               |  높음 |
| v3 피드백      | Reclaim loop 역행 가능성, recovery 무한 루프, trigger별 복귀 경로, trunk seed 미정의가 지적됨                           |  높음 |
| 레거시·프로토타입 참고 | 과거 시도·패치는 **아이디어 출처**로만 쓰고, 문서 규칙과 충돌하면 문서가 이긴다. |  중간 |

---

## 2. Solver 최종 목표

### 2.1 한 줄 정의

```text
Shapez2 asteroid mining layout optimizer
```

Shapez2 blueprint 또는 map data에서 소행성 채굴 영역을 복원하고, extractor / extension / belt / pipe를 재배치하여 채굴량과 transport 효율을 최대화하는 Solver다.

---

### 2.2 최종 목표 요약

| 목표                  | 설명                                                      |
| ------------------- | ------------------------------------------------------- |
| 채굴량 최대화             | 가능한 많은 extractor bundle을 배치한다.                          |
| extension 효율 최대화    | extractor 1개당 최대 3개의 extension을 붙이는 방향을 우선한다.           |
| transport 내부 점유 최소화 | belt/pipe가 소행성 내부 채굴 후보 공간을 막지 않도록 한다.                  |
| 외부 연결 보장            | 모든 extractor output은 최종적으로 소행성 외부 trunk와 연결되어야 한다(**기존 belt/pipe와 merge·공용** 포함, §3.1).      |
| overlap 0건          | extractor / extension / belt / pipe가 같은 셀을 점유하지 않도록 한다. |
| capacity 보장         | **1차(우선)**: 연결 trunk·edge별 **출하량 합산(총합)** 만 산출·trace한다(**max capacity·포화 상한과의 비교는 생략**). **후속**: rated capacity 대비 초과 검증을 켤 수 있다(§3.6).      |
| bounded recovery    | recovery와 reclaim 반복이 무한 루프를 만들지 않도록 제한한다.              |
| replay 가능성          | 모든 pass와 commit/reject 과정을 trace로 남기고 UI에서 재생한다. solve **진행 중**에는 계산 cycle **매 10회**마다 STEP 10 visualization을 갱신해 실시간 스트리밍한다(§16.1).        |

---

## 3. 핵심 게임/배치 규칙

### 3.1 Extractor 규칙

```text
- extractor는 반드시 한 방향으로 output을 가져야 한다.
- extractor output 앞 1칸에는 belt 또는 pipe stub가 반드시 필요하다.
- output stub는 최종 external route와 연결되어야 한다.
- extractor가 있는 셀에는 belt/pipe가 겹칠 수 없다.
```

**기존 belt/pipe 연계·공용**: extractor **배치**(후보 생성·점수화·확정) 단계에서부터, **이미 맵에 존재하는 belt/pipe**와 **연계하여 공용**할 수 있다. output 이후 경로는 **기존 trunk에 merge**하거나 **이미 깔린 구간을 그대로 활용**하는 후보를 허용한다(동일 **TransportKind**·**capacity**·merge 규칙을 만족할 때). **셀 겹침**은 금지이다 — extractor/extension **점유 셀**과 기존 transport **점유 셀**은 동일 셀을 공유하지 않는다(§2.2, §3.5 상단 bullet).

---

### 3.2 Extension 규칙

```text
- extractor 1개당 최대 3개의 extension을 붙일 수 있다.
- extension은 extractor output 방향을 제외한 3방향(인접 칸)에 붙을 수 있다.
- extension끼리도 연결 가능하며, 체인은 FIFO처럼 parent→child 순으로 이어진다.
- extension이 있는 셀에는 belt/pipe가 겹칠 수 없다.
```

---

### 3.3 Extension 방향 정의

extension은 자신이 연결되는 **parent**를 바라본다.

```text
parent = extractor 또는 다른 extension
extension_orientation = extension cell에서 parent cell을 향하는 방향
```

예시(parent는 항상 extension의 **인접 칸**에 있다고 본다):

```text
- extractor가 extension 칸의 북쪽 인접에 있으면, extension은 북쪽(parent)을 향한다.
- extractor가 extension 칸의 서쪽 인접에 있으면, extension은 서쪽(parent)을 향한다.
- extension이 다른 extension에 이어 붙는 경우에도, 직접 붙은 parent extension 칸을 향한다(체인은 FIFO).
```

예: extractor의 output이 **북쪽(북향)**이면, extension은 extractor의 **남·동·서** 인접 칸에만 둘 수 있고, 각 extension은 각각 **북·서·동**을 향해 extractor(또는 체인 상의 parent)와 맞닿는다.

즉, extractor output 방향 쪽 인접 셀은 belt/pipe stub용으로 비워두고, 나머지 3방향 인접 셀에는 parent를 바라보는 extension 후보를 둘 수 있다.

구현 목표는 **3방향 branching extension topology**다. 단순 `straight extension chain`만 지원하는 형태는 **축소 예시**일 뿐, 문서 목표와 동일시하지 않는다.

---

### 3.4 채굴량·출하량 / capacity 규칙

#### 도형(extractor bundle)

- extractor의 **도형 출하량(items/time)** 은 **본인에 결합된 extension 수**(및 동일 체인의 채굴 슬롯 규칙)에 **비례**해 계산한다. 구현은 `slots(extractor)`(또는 게임과 동일한 산식)을 **단일 정본**으로 두고, trace에 extension 개수·슬롯 합을 남긴다.
- **기본층(레벨 1) 단독 extractor** 기준 **0.4 items/s = 24 items/min** 을 사용한다(게임 근거; 밸런스 패치 시 문서·상수 동기화).

```text
- 슬롯 모델 예(기존 논의와 정합): extractor 기본 4 slots, extension 1개당 +4 slots, extractor당 extension 최대 3 → 최대 16 slots
  (실제 items/min은 이 슬롯 합에 비례; 24/min은 “기본 4슬롯·기본층 1기”에 대한 참고 기준값으로 둔다).
```

#### 벨트·스페이스 벨트(도형)

- **벨트 1 lane** 운반 **2 items/s** (= **120 items/min** / lane).
- 한 lane를 **연속 포화**시키려면 그 lane으로 합류하는 extractor 쪽 **합산 출력 ≥ 2 items/s** 이어야 한다. **기본층 extractor만**으로 환산할 때 **5기(×0.4/s = 2.0/s)** 가 1 lane에 대한 **참고 스케일**이다(실제로는 extension·레벨·슬롯으로 달라짐).
- **Space belt(12 lanes)**: lane별로 위 포화 조건을 만족시켜야 하며, 플레이에서는 **층마다 3기 bundle을 4세트** 두는 식으로 12-lane을 채우는 예가 자주 인용된다.
- 광맥을 최대한 쓰려 **Space belt 4본**까지 올리는 구성에서는 **총 48기** extractor 규모가 예시로 자주 나온다(필수 정답 배치는 아님).

#### 유체(fluid)

- 유체 extractor·펌프 묶음의 **부피 유량(L/min)** 도 **결합된 채굴 단위(세트 수·슬롯)** 에 비례해 계산한다(도형과 **동일한 “비례 + 용량” 패턴**).
- **유체 펌프 한 세트(4기)** 출력 **1,800 L/min** 참고값.
- **Space pipe** 한 줄 **7,200 L/min** — 펌프 세트를 **4세트** 합류하면 상한에 맞닿는 스케일(플레이 참고).

#### 트렁크·엣지 누적 유량

- **각 belt/pipe 구간**(셀 또는 **방향 edge**)마다 **upstream에서 합산한 총 출하량(누적 합)** 을 유지한다.
- **1차(우선)**: **lane·pipe의 max capacity(rated 상한)** 는 **검사하지 않는다.** 목표는 **합산 총량**을 외부까지 전파해 **어디서 얼마가 합쳐지는지**를 계산·기록(trace)하는 것이다.
- **후속(선택)**: 동일 `trunk_load`에 대해 **max capacity 초과**를 hard/soft constraint로 붙일 수 있다(STEP 4·9, overflow·recovery).

정확도: 0.4/s·2/s·12-lane·유체 수치는 **게임·커뮤니티 기준 근사**이며, 세부는 연구 문서·QA로 고정한다.

---

### 3.5 Transport 규칙

```text
- belt/pipe는 extractor/extension 위에 올라갈 수 없다.
- belt/pipe가 이미 지나가는 셀에는 extractor/extension이 배치되면 안 된다.
- belt/pipe는 소행성 좌표 밖으로 확장 가능하다.
- 모든 extractor output은 최종적으로 외부와 연결되어야 한다.
```

#### 경로 탐색·셀 가중치(기본: Dijkstra)

라우팅은 **가중 그리드 최단 경로**로 두고, 기본 알고리즘은 **Dijkstra**(음수 가중치 없음)를 따른다. 이웃 셀로 진입할 때의 **대표 가중치(설계 기준)**는 아래와 같다.

```text
void(암석 밖 빈 공간)           = 25
이미 깔린 belt/pipe가 있는 셀   = 10
extractor가 점유한 셀(경로 회피)= 150
extension이 점유한 셀(경로 회피) = 50
```

맵 위에서 **extractor·extension이 밀집한 구간**일수록 인접·같은 축 구간에 **추가 비용을 가산**해, 트렁크가 한 갈래로만 몰리지 않도록 유도한다(누적 규칙은 구현 튜닝).

레거시 코드에 남아 있는 상수·함수명은 **참고**일 수 있다. 구현 시에는 **이 절 표를 설계 정본**으로 삼고 코드를 맞춘다(파일 경로·이름은 고정 아님).

#### extractor output·외부 병합

```text
- 각 extractor의 output에는 belt 또는 pipe **stub가 정확히 1개** 붙는다.
- 그 stub에서 나간 경로는, **이미 존재하는 belt/pipe(trunk)** 와 **공용·연계**(merge·기존 lane 활용)할 수 있으며, 최종적으로 **외부와 연결된 trunk**에 **merge**되어 한 덩어리의 외부 연결이 되어야 한다.
```

#### output 방향(회전) 탐색

extractor **주변에 void(또는 저비용 통과) 후보가 여러 방향**으로 열려 있으면, **가능한 output 방향마다** 동일 목표(외부 merge 지점 등)까지의 **최소 비용 경로를 각각 평가**한다. 다른 방향이 **더 짧거나(또는 총 비용이 더 낮으면)** extractor의 **output 방향을 돌리는** 선택을 허용한다.

#### 외부 판정 기준

기존 “소행성 bbox 기준 최소 5칸 밖”은 작은 소행성에서 과도할 수 있다. v4에서는 동적 margin을 사용한다.

```text
external_margin = clamp(
    ceil(max(asteroid_width, asteroid_height) * 0.15),
    min=3,
    max=7,
)
```

초기 기본값은 5칸을 유지하되, 실제 외부 판정은 위 동적 margin으로 계산한다.

```text
external cell = asteroid bbox에서 external_margin 이상 떨어진 셀
```

`asteroid_width`, `asteroid_height` 측정 기준(동적 margin 입력):

```text
기본: mineable_placement_cells의 axis-aligned bounding box 변 길이(셀 수).
대안(정책 스위치): extraction_shell_cells bbox — 내부 void 제외 외곽만 볼 때.
```

**입력 기준 선택 정책(정본)**:

```text
1. 기본값은 mineable_placement_cells bbox를 사용한다.
2. 다음 중 하나라면 extraction_shell_cells bbox로 자동 전환을 검토하고 trace에 이유를 남긴다:
   - mineable bbox 대비 실제 mineable cell 수가 매우 적음(예: 채움 비율이 낮음) — “헐거운 bbox” 의심
   - mineable bbox가 L/U 자 형태 등 비정형이라 외곽 판정에 과대 margin이 예상됨
3. 스위치 판정은 결정론적 규칙으로 구현한다(예: mineable count / bbox area 비율 threshold).
   threshold 초안은 튜닝 후보로 두고, 실제 값은 QA 기준으로 고정한다.
4. 최종적으로 어떤 기준을 썼는지 trace 필드 `external_margin_bbox_source: mineable | shell`로 기록한다.
```

비정형(L자 등) 소행성에서는 bbox가 실제 점유보다 크게 나와 margin이 과대될 수 있다. 위 정책으로 완화하고 `mineable` vs `shell` 중 무엇을 썼는지 trace에 남긴다.

정확도: 중간. 3~7 범위와 0.15 계수는 튜닝 후보이며, 실제 맵 크기별 QA 결과에 따라 조정한다.

---

### 3.6 Belt vs Pipe 구분

belt와 pipe는 같은 `transport`로 뭉뚱그리면 안 된다.

```text
TransportKind.SHAPE_BELT
TransportKind.FLUID_PIPE
```

| 항목                  |                                     Belt |              Pipe |
| ------------------- | ---------------------------------------: | ----------------: |
| 대상                  |                           shape resource |    fluid resource |
| capacity (참고)     | **2 items/s per lane**; Space belt **12 lanes** → 합산 **24 items/s** 규모(1차 계산에서는 **상한 비교 없이** 참고값으로만 쓴다) | Space pipe **7,200 L/min**; 펌프 세트(4기) **1,800 L/min**(동일) |
| route geometry cost |                        RouteZone cost 사용 | RouteZone cost 사용 |
| **1차** 합산·constraint | **max capacity 무시**, edge·lane마다 **누적 합만** 산출·trace | 동일 |
| **후속** capacity 검증 | (선택) 누적 합 ≤ rated **max capacity**·overflow 분기 | 동일 |
| 누적 유량             | 구간(edge)·lane마다 upstream **합산 총량** 유지, 외부까지 전파 | 동일 |
| merge 가능 대상         |                              belt trunk만 |       pipe trunk만 |
| 서로 merge 가능 여부      |                                       불가 |                불가 |

RouteZone cost는 동일한 공간 비용 모델을 공유할 수 있지만, **merge / trunk topology** 판단은 transport kind별로 분리한다. **누적 합** 필드는 kind별 단위(items/s 또는 L/min)로 저장한다. **max capacity 대비 overflow**는 **1차 범위 밖**(후속 단계·플래그)으로 둔다.

---

## 4. 전체 Solver Pipeline v5.3

v5에서는 Reclaim loop와 Recovery branch가 무한 루프를 만들지 않도록 **bounded control flow**를 명시한다.

```text
STEP 0. Shapez2 copy code decode
STEP 1. Asteroid reconstruction
STEP 2. Pass1 outer-first placement
STEP 3. Pass2 internal fill placement
STEP 4. Merge-aware capacity-aware routing
STEP 5. Pass3 internal transport minimization
STEP 6. Reclaim placement loop
STEP 7. Optional post-reclaim Pass3 rerun
STEP 8. Recovery branch (비선형 분기; 매 solve마다 실행되는 선형 STEP 아님 — §13)
STEP 9. Final validation
STEP 10. Replay visualization
```

**STEP 8 번호 부여**: 목차상 슬롯 번호일 뿐이다. Recovery는 항상 실행되는 단계가 아니라 **실패·보정 조건에서만 진입하는 bounded branch**(§4.1, §13)다.

핵심:

```text
Pass3가 확보한 공간은 Reclaim loop에서 다시 활용한다.
단, Reclaim loop가 Pass3의 internal transport 절약분을 과도하게 되먹으면 reject한다.
Recovery는 branch이며, trigger별 복귀 지점과 attempt limit을 가진다.
```

---

### 4.1 Pipeline control flow

```text
Decode
→ Reconstruction
→ Pass1 placement
→ Pass2 placement
→ Merge-aware routing
    ├─ routing/capacity 실패 → recovery(trigger=step4_routing_failure)
    └─ 성공 → Pass3
→ Pass3 internal transport minimization
    ├─ 연결성 파괴 → rollback 또는 recovery(trigger=pass3_connectivity_break)
    └─ 성공 → Reclaim loop
→ Reclaim placement loop
    ├─ 신규 placement 없음 → Final validation
    ├─ 신규 placement 있음 → incremental routing
    ├─ incremental routing 실패 → candidate rollback 또는 recovery(trigger=reclaim_incremental_failure)
    ├─ internal transport budget 초과 → 해당 후보만 reject(§12.6); loop은 다음 후보 계속
    └─ loop limit 도달 → Final validation
→ Optional post-reclaim Pass3 rerun (STEP 7)
    ├─ 연결성 파괴 → recovery(trigger=post_reclaim_pass3_connectivity_break) 또는 rerun 변경 rollback
    └─ 성공 → Final validation
→ Final validation
    ├─ success → Replay visualization
    └─ failure → bounded recovery(trigger=final_validation_failure)
```

---

### 4.2 Bounded loop 제한

```text
MAX_RECLAIM_ITERATIONS = 2 또는 3
MAX_POST_RECLAIM_PASS3_RERUNS = 1
MAX_VALIDATION_RECOVERY_ATTEMPTS = 1 또는 2
MAX_TOTAL_RECOVERY_ATTEMPTS = 3
MAX_CASCADE_CORRECTIVE_ATTEMPTS = 2  # 튜닝: STEP 4 rollback 직후 연결성 보정 한도
```

`MAX_CASCADE_CORRECTIVE_ATTEMPTS`(§9.6): placement rollback으로 인한 **즉시 연결성 보정**만 카운트한다.
**`MAX_TOTAL_RECOVERY_ATTEMPTS`에는 포함하지 않는다**(메인 recovery 예산 고갈 방지). 대신 이 상한으로 무한 cascade를 막는다.

`MAX_POST_RECLAIM_PASS3_RERUNS` **스코프(정본)**: 소행성 **1회 solve 전체**에서 post-reclaim Pass3 rerun **호출(블록 실행) 횟수** 상한이다. `MAX_RECLAIM_ITERATIONS`와 독립이며, Reclaim loop **iteration마다 리셋되지 않는다**. 한 번의 rerun 블록 안에서 실패 시 재탐색 루프가 아니라 §4.3.2대로 즉시 rollback 후 STEP 9로 진행한다.

**Canonical — Reclaim 내부 transport·gain 규칙**: 후보 채택·누적 budget·`gain / additional_route_cost` threshold 수치의 규범 정의는 **§12.2**다. §4.2 본 절은 **반복 한도·상한 상수**와 루프 수준의 계속/종료 요약만 둔다. §12.6의 “후보 reject”는 §12.2 budget 규칙의 직접 적용으로 읽는다.

Reclaim loop **계속** 요약(상세 조건·수식은 §12.2):

```text
- §12.2 후보 체크리스트·budget·gain ratio(DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD)를 만족하는 신규 후보가 남아 있음
- MAX_RECLAIM_ITERATIONS 미도달
```

**종료** 요약(위 조건의 부정 또는 한도 소진; 단일 후보 budget reject는 iteration 전체 종료가 아님):

```text
- §12.2를 만족하는 신규 후보 없음 / 동일 iteration에서 후보 소진 후 전역 지표 개선 없음
- MAX_RECLAIM_ITERATIONS 도달
```

`MAX_VALIDATION_RECOVERY_ATTEMPTS`·`MAX_TOTAL_RECOVERY_ATTEMPTS` 등 **파이프라인 전역 attempt 한도**는 Reclaim loop **내부** 종료 조건이 아니다. Final validation 이후 recovery·solver 종료 등은 **§4.4**·**§13.1**에서만 다룬다.

---

### 4.3 Recovery trigger별 복귀 경로

| Trigger                       | 발생 지점                                     | Recovery 후 복귀                                           | 실패 시                                           |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| `step4_routing_failure`       | STEP 4 route 생성 실패                        | STEP 4 재시도, 해당 placement rollback 또는 alternate trunk 사용 | unrouted placement rollback 후 STEP 4 재시도       |
| `step4_capacity_failure`      | STEP 4 capacity split/additional trunk 실패 | STEP 4 재시도, trunk split 후보 변경                           | offending placement rollback                   |
| `pass3_connectivity_break`    | STEP 5 Pass3가 연결성 파괴                      | **§4.3.1** 절차 적용 → 복귀 **STEP 6 Reclaim placement loop**            | Pass3 변경 rollback 후 마지막 known-good 유지      |
| `post_reclaim_pass3_connectivity_break` | STEP 7 post-reclaim Pass3 rerun이 연결성 파괴 | rerun 변경 rollback → STEP 9(**추가 rerun 없음**, §4.3.2) | 기존 connected layout 유지, partial success 가능   |
| `reclaim_incremental_failure` | STEP 6 신규 placement routing 실패            | 해당 reclaim candidate rollback 후 STEP 6 계속               | 후보 exhausted 시 Final validation                |
| `final_validation_failure`    | STEP 9 invariant 실패                       | recovery 후 STEP 9 재검증 (**STEP 4 재진입 없음**)              | attempt 초과 시 partial success 또는 solver failure |

`final_validation_failure` 복구로 STEP 4 본 파이프라인을 자동 재실행하지 않는다. 용량 재설계가 필요하면 상위 오케스트레이터가 별도 실행한다.

#### 4.3.1 `pass3_connectivity_break` 복귀 결정 (STEP 5 전용)

STEP 7에서 동일 현상은 `post_reclaim_pass3_connectivity_break`로 분리한다.

```text
1. Pass3 시도를 rollback하여 직전 known-good transport로 복원한다.
2. STEP 5 직후 파이프라인 순서상 Reclaim은 아직 실행 전이므로,
   복귀 지점은 STEP 6 Reclaim placement loop다.
3. (선택 remedial) Pass3 실패 원인이 STEP 4 배치/merge·trunk goal 불일치로 판단되면:
   **§4.3 표 `step4_routing_failure` 행의 “Recovery 후 복귀” 절차를 한 번만 인플레이스 재사용**한다
   (별도 trigger 문자열을 붙이지 않아도 된다; trace에는 `remedial_after_pass3_connectivity_break=true` 등으로 구분).
   - 성공 시: 갱신된 transport로 Pass3를 **한 번** 재시도할 수 있다(3번 경로당 Pass3 재시도 **최대 1회**).
   - 위 remedial Pass3 재시도가 연결성·hard invariant를 깨면 **§4.3.1 1번과 동일하게 해당 Pass3 시도를 rollback**하여 직전 known-good으로 복원한다. **그 뒤로 Pass3를 또 재시도하지 않는다**(무한 재시도 금지).
   - 실패 시: **§4.3 표 `pass3_connectivity_break` “실패 시” 열**과 동일하게 Pass3 변경은 rollback된 채 known-good을 유지하고,
     이어서 **`step4_routing_failure`와 동일한** unrouted quarantine·STEP 4 재시도 루틴(표 1행)으로 넘긴다.
```

**§4.3.1 3번 vs 표 “실패 시”**: 표의 “실패 시”는 **Pass3 rollback·연결성 회복 시도 전부가 소진된 뒤**의 최종 상태다. 3번은 그 **이전**에 허용하는 **한 번의 STEP 4 remedial**이다. 3번이 성공해 Pass3가 통과하면 표의 “실패 시” 열은 적용되지 않는다.

“Reclaim 종료 후” 연결성 깨짐은 STEP 5 시점에 발생할 수 없다. 그 경우는 STEP 7에서 `post_reclaim_pass3_connectivity_break`(§4.3.2)로 처리한다.

#### 4.3.2 STEP 7(post-reclaim Pass3 rerun) 실패 처리

```text
- 연결성 파괴: trigger=post_reclaim_pass3_connectivity_break (trace·rollback_reason 등에 기록).
- 복귀: STEP 6 재진입이 아니라, rerun으로 깬 Pass3 변경만 rollback하고 STEP 9 Final validation.
- 재시도 정책(정본):
  - MAX_POST_RECLAIM_PASS3_RERUNS = 1 이면 “소행성 1회 solve당 post-reclaim Pass3 rerun 호출은 최대 1번”이다.
  - 동일 rerun 블록 안에서 실패 → rollback 후 재탐색 루프를 또 도는 것이 아니라,
    즉시 known-good으로 복구하고 STEP 9로 진행한다(추가 rerun 없음).
  - 호출 자체를 0으로 두고 조건만 만족할 때 1회 실행하는 구현이 이와 동치다.
```

---

### 4.4 Solver 종료 상태

```text
SUCCESS:
- geometry/connectivity/capacity invariant 모두 통과
- (선택) §15.4 optimization 목표까지 통과한 경우 “full success”로 trace 구분 가능

PARTIAL_SUCCESS:
- 기존 connected layout은 유지했지만 신규 reclaim placement 일부 rollback
- 또는 일부 low-priority placement를 제거하고 valid layout 반환
- invariant는 통과했으나 §15.4 optimization 항목만 미달인 경우: **solver 실패가 아니라**
  PARTIAL_SUCCESS 또는 SUCCESS + `optimization_warnings`(정책에 따라 택일)

SOLVER_FAILURE:
- connected transport를 만들 수 없음
- capacity-safe trunk를 만들 수 없음
- attempt limit 초과
```

§15.4의 항목은 **hard invariant(§15.1–15.3)** 와 **soft optimization(품질 목표)** 을 분리해 해석한다. optimization만 실패하면 Final validation을 “실패 → validation_recovery”로 보내지 않고,
결과 등급과 trace 경고로 처리한다(§15.4 참고).

---

## 5. STEP 0 — Shapez2 Copy Code Decode

### 5.1 목표

Shapez2 copy string을 내부 solver가 사용할 수 있는 JSON/DTO 형태로 변환한다.

```text
SHAPEZ2-4-
→ Base64 decode
→ gzip decompress
→ JSON parse
→ blueprint entities 추출
```

---

### 5.2 역할

```text
- 기존 건물 좌표 추출
- belt / pipe / extractor / extension / asteroid shell 구분
- solver grid coordinate 생성
- 이후 reconstruction 단계의 입력 데이터 생성
```

---

### 5.3 진행 상태

| 항목                 |       상태 |
| ------------------ | -------: |
| copy string decode |      구현됨 |
| gzip/base64 처리     |      구현됨 |
| JSON parse         |      구현됨 |
| solver DTO 정규화     |    부분 구현 |
| DB 저장 및 SVG 연동     | 추가 개발 필요 |

---

## 6. STEP 1 — Asteroid Reconstruction

### 6.1 목표

기존 blueprint에서 소행성 채굴 가능 영역을 복원한다.

```text
full_barrier_cells        # 기존 건물/장애물 전체
extraction_shell_cells    # 소행성 shell / 외곽 채굴 영역
belt_cells                # 기존 belt
pipe_cells                # 기존 pipe
interior_patch_cells      # decode 후 추론된 내부 patch
mineable_placement_cells  # 실제 배치 후보 셀
```

---

### 6.2 핵심 로직

```text
1. blueprint에서 asteroid shell cell을 수집한다.
2. 기존 belt/pipe/extractor/extension을 분리한다.
3. 소행성 boundary를 기준으로 외부 flood fill을 수행한다.
4. 작은 gap 때문에 내부가 외부로 새는 문제를 막기 위해 Chebyshev 8-neighbor closing을 적용한다.
5. 외부가 아닌 빈 공간을 내부 채굴 후보 patch로 추론한다.
```

---

### 6.3 중요한 정정 사항

다음 로직은 **재배치 중에 수행하면 안 된다.**

```text
내부 void를 나중에 inferred mining field로 변환한다.
```

올바른 기준:

```text
- mineable field 추론은 decode/reconstruction 단계에서만 한다.
- Pass1/Pass2/Pass3/Reclaim loop는 이미 확정된 mineable field 위에서 placement와 routing을 최적화한다.
```

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
- **이미 존재하는 belt/pipe**와 **연계·공용**할 수 있는 후보를 배치 평가에 포함한다(§3.1)
```

---

### 7.2 원래 설계

```text
1. 동/서/남/북 외부 방향 후보를 선택한다.
2. 소행성 외곽을 기준으로 extractor 후보를 만든다.
3. extractor는 void 또는 외부 연결이 가능한 방향을 향한다.
4. extractor output 앞에 belt/pipe stub를 둔다.
5. output 방향 외 3방향에 extension 후보를 붙인다.
6. 12시 방향부터 시계 방향으로 scan한다.
7. 후보 bundle을 배치하고 occupied map을 갱신한다.
8. **이미 존재하는 belt/pipe**와 연계·공용(merge) 가능한 후보는 평가·정렬에 반영한다(§3.1).
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

Pass1은 **문서 정본(§0)** 만을 따른다. 아래는 그에 맞춘 **절차 예시**이며, 함수명·모듈명은 고정이 아니다.

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

## 8. STEP 3 — Pass2: Internal Fill Placement

### 8.1 목적

Pass1 이후 남은 내부 mineable area를 추가 활용한다.

```text
Pass1: 외곽 우선 배치
Pass2: 남은 내부 공간 보강 배치
```

Pass2 extractor 후보도 **이미 존재하는 belt/pipe와의 연계·공용**을 배치 평가에 넣을 수 있다(§3.1).

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

## 9. STEP 4 — Merge-Aware Capacity-Aware Routing

### 9.1 목적

모든 extractor output stub를 소행성 외부 trunk와 연결한다.

```text
extractor
→ output stub
→ local route
→ merge-aware trunk
→ exterior margin
```

---

### 9.2 Trunk seed 정의

```text
trunk_seed = 여러 output route가 합류할 수 있는 초기 연결 후보 셀 또는 셀 집합
```

trunk seed 후보는 다음에서 생성한다.

```text
1. external margin에 인접하거나 margin 바깥에 있는 candidate exit cells
2. Pass1/Pass2 output stub들이 공통으로 접근하기 쉬운 boundary ring cells
3. 기존 blueprint에서 보존 가능한 같은 TransportKind trunk cells
4. RouteZone cost가 낮고 capacity 확장이 가능한 boundary / outside cells
```

trunk seed가 아닌 것:

```text
- 모든 output stub의 단순 집합
- cheap_transport_escape_exists()가 사용한 임시 path
- belt와 pipe가 섞인 mixed trunk
```

trunk seed와 **route goal set**은 역할이 다르다.

```text
- trunk_seed: merge가 일어날 수 있는 후보 좌표(탐색 힌트·중립 연결점).
- route goal set: 단일 목적지가 아니라 “도달하면 성공인 셀 집합”.
```

첫 번째 extractor를 라우팅할 때는 **existing trunk cells가 비어 있다**. 이 경우 goal set은 `exterior margin cells ∪ trunk_seed_candidates`(해당 output의 TransportKind에 맞는 것만)로 둔다. 첫 route가 commit되면 그 결과 trunk 경로·merge 지점이 **existing trunk**로 승격되고, 이후 bundle은 기존 문장대로 `existing trunk cells + exterior margin`을 goal로 사용한다.

첫 route가 **commit되지 않고** `QUARANTINED_UNROUTED` 또는 `ROLLED_BACK`으로 끝나면 **existing trunk 승격은 발생하지 않는다**. `trunk_seed_candidates`·exterior margin 기반 goal set 구성은 유지되며, 이후 extractor 라우팅도 동일 규칙(빈 trunk일 때의 goal set)을 따른다.

---

### 9.3 Routing과 Merge의 내부 순서

```text
1. trunk seed 후보 생성
2. route goal set 구성 (§9.2 trunk seed와의 관계 참고):
   - existing trunk가 비어 있으면 exterior margin ∪ trunk_seed_candidates
   - 이후에는 existing trunk cells + exterior margin cells
3. extractor bundle을 priority 순서로 정렬
   - 동점 해소(위에서 아래 순): cheap_escape/외부 도달 예상 비용 ↓,
     stub에서 exterior margin까지 맨하탄 거리 ↓, bundle slot 수(생산량) ↑ (큰 bundle이 trunk 선점),
     Pass1 출처 bundle을 Pass2보다 우선, 같은 pass 내에서는 안정 정렬(스캔 인덱스 등)
4. 각 output stub에서 가장 좋은 merge target 또는 exterior target까지 route 탐색
5. route commit 시 trunk load와 capacity를 즉시 갱신
6. capacity 초과 시 alternate trunk, split route, additional trunk 후보를 탐색
7. 모든 route가 connected + capacity-safe이면 STEP 4 성공
```

priority 순서는 라우팅 선점 효과가 있으므로, 구현은 위 튜플을 **고정**하고 trace에 사용한 키를 남긴다.

즉, 기본 전략은 다음이다.

```text
Routing 후 Merge가 아니라,
Merge-aware Routing을 우선한다.
```

---

### 9.4 Capacity와 누적 합산(1차 우선)

[`mining_solver_cursor_sessions/01_project_overview.md`](./mining_solver_cursor_sessions/01_project_overview.md) §3.6에 따라 **1차(우선)** STEP 4에서는 **lane·pipe max capacity(rated 상한)와의 비교를 하지 않고**, trunk·edge별 **upstream 출하량 합산(총합)** 만 계산·trace한다.

**후속(선택)**: 아래 **trunk capacity 초과 없음** 등을 hard constraint로 켜면, commit·recovery에서 overflow를 처리한다.

용량 검증을 **완전히 생략**한 채 STEP 9만 두면 문제가 늦게 드러날 수 있으므로, **후속 단계에서 capacity를 켤 때**에는 STEP 4에서 즉시 처리하는 편이 낫다.

```text
route candidate commit 조건(1차 — geometry·연결성):
- geometry valid
- output stub connected
- target trunk 또는 exterior connected
- transport kind 일치
- trunk_load 합산 필드 갱신(총량만; max capacity 미검사)

route candidate commit 조건(후속 — capacity 검증 활성 시 추가):
- trunk capacity 초과 없음
- capacity 초과 시 split/additional trunk 대안 존재
```

Final validation은 **후속 단계에서 capacity 검증을 켠 경우**에만 capacity를 assertion gate로 다시 확인한다(1차만 구현이면 합산·연결성 중심으로 완화).

---

### 9.5 Transport kind별 routing

```text
shape extractor output → TransportKind.SHAPE_BELT route만 허용
fluid extractor output → TransportKind.FLUID_PIPE route만 허용
```

서로 다른 transport kind는 같은 trunk로 merge하지 않는다.

```text
1차: belt/pipe trunk_load는 §3.6에 따라 **누적 합(총량)** 만 갱신한다(max capacity 미검사).
후속: 동일 필드에 대해 rated capacity·overflow 판단을 붙일 수 있다.
```

---

### 9.6 Pass1 / Pass2 placement commit과 STEP 4 실패

```text
- Pass2에서 placement-only commit은 route 확정 전이므로 아래 PlacementCommitState를 명시적으로 탄다.
- Pass1 placement도 STEP 4에서 라우팅·**(후속)** capacity 실패 시 동일하게 rollback·quarantine의 대상이 될 수 있다.
  구현은 Pass1/Pass2를 구분하는 `placement_pass` 태그만 두고 동일 enum을 쓰거나, 별도 타입으로 분리한다.
- Pass1 시점에는 아직 STEP 4 전이므로, 상태 의미상 Pass2의 PROVISIONAL_PLACED와 동일하게 “routing 미확정 배치”로 취급한다.
```

Pass2에서 placement는 route 확정 전의 provisional commit이다. STEP 4에서 route를 만들지 못하면 해당 placement는 유효하지 않다.

```text
PlacementCommitState:
- PROVISIONAL_PLACED
- ROUTED_CONFIRMED
- QUARANTINED_UNROUTED
- ROLLED_BACK
```

**상태 전이(FSM, 정본)**

```text
PROVISIONAL_PLACED
  → ROUTED_CONFIRMED      (STEP 4 routing·capacity 성공, route commit)
  → QUARANTINED_UNROUTED  (STEP 4 routing 실패 등 — 유지 가능 상태)
  → ROLLED_BACK           (recovery 실패 또는 명시적 rollback)

QUARANTINED_UNROUTED
  → ROUTED_CONFIRMED      (recovery 성공)
  → ROLLED_BACK           (recovery 실패)

ROLLED_BACK               (terminal — 동일 placement 재사용·candidate 풀 재진입 금지)
ROUTED_CONFIRMED          (terminal — placement 단위로는 정상 확정; §9.6 처리 규칙·route 재검증 참고)
```

**Placement 상태 vs route 자원**: `ROUTED_CONFIRMED`는 **해당 placement의 라우팅 성공 확정**을 뜻한다. 인접 placement가 `ROLLED_BACK`되어 **이미 commit된 route가 점유하던 셀이 해제·차단 집합에서 빠지는** 등으로, 그 route가 더 이상 유효한 geometry·연결성을 만족하지 않으면 **route 단위 재검증·corrective reroute 또는 `cascade_corrective_recovery`**가 여전히 필요하다. “cascade 보정 대상에서 제외”는 **동일 placement를 다시 quarantine 대상으로 흔들지 않는다**는 의미이지, **고아·파손 route segment를 방치**한다는 뜻이 아니다.

처리 규칙:

```text
1. Pass2 commit 직후 placement는 PROVISIONAL_PLACED 상태다.
2. STEP 4에서 output route와 capacity가 확정되면 ROUTED_CONFIRMED가 된다.
3. STEP 4 routing 실패 시 해당 placement는 QUARANTINED_UNROUTED로 이동한다.
4. recovery가 성공하면 ROUTED_CONFIRMED로 승격한다.
5. recovery가 실패하면 ROLLED_BACK 처리하고 occupied cells를 해제한다.
6. Final validation에는 QUARANTINED_UNROUTED placement가 남아 있으면 안 된다.
7. ROLLED_BACK 또는 placement 해제 후 **연결성·geometry 재검증**: 다른 placement/route가 해제된 셀을
   waypoint·blocked 가정으로 사용했는지 확인한다. 연결이 깨지면 해당 route를 대상으로
   최소 corrective reroute 또는 **cascade_corrective_recovery**(§13.3)를 호출한다.
   overlap 제거는 deterministic tie-break로 하며 무작위 삭제는 금지한다.
8. 단순히 경로가 비효율적으로 남는 경우(더 짧은 우회가 생김)는 필수 수정 대상이 아니며,
   trace에 `suboptimal_route_after_neighbor_rollback` 등으로 기록할 수 있다.
```

cascade 보정은 Final validation의 `validation_recovery`와 **다른 컨텍스트**다. 시도 한도는 `MAX_CASCADE_CORRECTIVE_ATTEMPTS`(§4.2)이며 `MAX_TOTAL_RECOVERY_ATTEMPTS`와 별도 집계한다.

**`cascade_corrective_recovery` vs `validation_recovery`**

```text
- cascade_corrective_recovery: STEP 4 처리 중·직후 placement rollback으로 연결성·geometry가 깨진 경우에만 진입(§13.3).
- validation_recovery: STEP 9에서 hard invariant가 깨졌을 때만 진입; STEP 4 본 파이프라인 자동 재진입 없음.
- cascade가 성공하면 해당 rollback 직후 보정 시도는 종료된 것으로 본다. 이후 파이프라인을 진행해 STEP 9에 도달했을 때
  **새로** 드러난 불변 조건 위반은 별도 시도로 validation_recovery를 트리거할 수 있다(attempt 카운터 분리, §4.2).
  “동일 버그가 두 번”이 이상 징후면 구현·trace에서 원인 분석 대상이다.
```

`rejected_by_no_replacement_route`: **commit_reason이 아니다.** replacement route 확보 없이 corridor/셀을 비우려 할 때의 **route reject 사유**이며, 동일 결정이 placement 제거로 이어지면 **`rollback_reason`(또는 `rejected_reason`)**에 기록한다. `commit_reason`은 **성공 커밋 분류만** 담는다(§13.5).

---

### 9.7 구현 스펙 범위(백지 전제)

STEP 4 routing은 **최소 목표인 “외부로 연결되는가”만으로는 부족**하다. 다음을 **동시에** 다루는 설계를 전제로 한다(구현 백지: §0).

```text
- 연결성
- route 길이
- 내부 transport cell 수
- mineable candidate 점유 손실
- trunk merge 가능성
- throughput/capacity
- 회전 수
- congestion
```

---

## 10. STEP 5 — Pass3: Internal Transport Minimization

### 10.1 Pass3의 정확한 정의

Pass3는 단순 재연결 단계가 아니다.

정확한 목적은 다음이다.

```text
중앙 belt/pipe를 무조건 제거하는 것이 아니라,
줄일 수 있는 내부 transport를 줄이고,
transport line을 외곽 / void / 저가치 cell / 기존 trunk 쪽으로 밀어내는 단계다.
```

---

### 10.2 기존 문제

최단거리 중심 BFS/A*는 다음 문제를 만든다.

```text
- 중앙 spine 생성
- 내부 mineable 후보 공간 점유
- extractor/extension 후보 감소
- pipe/belt 과다 생성
- extractor가 route 위에 올라가는 overlap 문제
- isolated extractor + long route 패턴 증가
```

---

### 10.3 Pass3의 새 목적함수

```text
소행성 내부 transport 사용량 최소화
→ mining opportunity loss 최소화
→ route cost 최소화
→ congestion/load penalty 최소화
→ turn_count 최소화
→ path_length 최소화
```

---

### 10.4 Lexicographic routing priority

```python
priority = (
    asteroid_internal_transport_count,
    mining_opportunity_loss,
    total_route_cost,
    congestion_penalty,
    turn_count,
    path_length,
    cell_row,      # 최종 tie-break: 결정론적 탐색·replay 재현용
    cell_col,
)
```

**동점 해소**: 위 튜플이 전부 동일한 후보가 남으면 마지막에 **`(cell_row, cell_col)` 사전순**으로 한 칸을 고른다(일반적으로 frontier에서 현재 확장 노드 좌표). 구현은 동일 규칙을 고정하고 trace에 사용한 tie-break 키를 남긴다.

이 방식의 장점:

```text
- 내부 transport 최소화를 1순위로 고정할 수 있다.
- cost 숫자 튜닝이 흔들려도 의사결정 우선순위가 유지된다.
- 거리만 짧고 내부 공간을 망치는 route를 막을 수 있다.
- congestion을 turn_count와 분리해 trunk 과밀을 직접 제어할 수 있다.
```

---

### 10.5 A* admissibility 처리 방침

`asteroid_internal_transport_count` 같은 값은 불규칙한 소행성 형태에서 admissible heuristic을 만들기 어렵다. 따라서 최적성 보장이 필요하면 다음 방식을 우선한다.

```text
기본 구현:
lexicographic Dijkstra / uniform-cost search
```

A*를 사용할 경우:

```text
- heuristic은 보수적 lower bound만 사용한다.
- internal_transport_count, opportunity_loss, congestion_penalty에 대해 안전한 lower bound가 없으면 0을 사용한다.
- path_length에 대해서만 Manhattan lower bound를 사용할 수 있다.
```

goal set이 여러 셀일 때 path_length 항의 Manhattan 휴리스틱은 **목표별 거리의 최소값**이어야 한다.

```text
manhattan_to_goal_set = min_{g in route_goal_set} manhattan(current, g)
```

권장 tuple heuristic:

```python
h = (
    0,
    0,
    0,
    0,
    0,
    manhattan_to_goal_set,
)
```

정확한 global optimal보다 속도가 더 중요하면 weighted A*를 사용할 수 있지만, 그 경우 문서와 trace에 `optimality_guarantee=false`를 남긴다.

A*·weighted 탐색에서 frontier 동점은 §10.4와 동일하게 **좌표 사전순**으로 해소해 결정론을 유지한다.

---

### 10.6 성능 제한 및 fallback

lexicographic Dijkstra는 정확성은 높지만 대형 맵에서 탐색 비용이 커질 수 있다. 웹 UI replay를 목표로 하므로 탐색 예산을 둔다.

```text
MAX_EXPANDED_NODES_PER_ROUTE = 20_000  # 초기 튜닝값
MAX_ROUTE_SEARCH_MS = 150~300ms        # interactive mode 기준
MAX_BATCH_SOLVE_MS = 3~10s             # full solver 기준
```

fallback 순서:

```text
1. lexicographic Dijkstra 시도
2. budget 초과 시 bounded weighted A*로 전환
3. 그래도 실패 시 baseline shortest feasible route 시도
4. baseline도 실패하면 recovery 또는 placement rollback
```

trace에는 다음을 남긴다.

```text
search_mode: lexicographic_dijkstra | weighted_astar | baseline_shortest | failed
expanded_nodes: int
search_time_ms: int
optimality_guarantee: bool
fallback_reason: string | null
```

정확도: 중간. node/time 예산은 튜닝 후보이며 실제 맵 크기 기준으로 조정한다.

---

## 11. Pass3 Route Cost Model

§11.1 **RouteZone 기본 cost** 수치는 [`mining_solver_cursor_sessions/03_data_schema_dto.md`](./mining_solver_cursor_sessions/03_data_schema_dto.md) §11.1과 동일(정본).

### 11.1 Route Zone 정의

| Zone                 | 의미                          | 기본 cost |
| -------------------- | --------------------------- | ------: |
| OUTSIDE              | 소행성 bbox 밖                  |       1 |
| BOUNDARY_VOID        | 소행성 외곽 / boundary ring      |       5 |
| INTERNAL_VOID        | 소행성 내부 빈 공간                 |      50 |
| FILLABLE_INTERIOR    | 내부 배치 가능성이 높은 공간            |     150 |
| PLACEMENT_CANDIDATE  | extractor/extension 후보 셀    |     400 |
| PLACEMENT_OCCUPIED   | extractor/extension 점유 셀    |     900 |
| BLOCKED              | extractor/extension 등으로 경로 관통 불가한 점유 셀 |     INF |

---

### 11.2 Transport kind별 cost override

기본 RouteZone cost는 공유하되, transport kind별 보정값을 둘 수 있다.

```python
route_cost = ROUTE_ZONE_COST[zone] * KIND_COST_MULTIPLIER[transport_kind]
```

초기값:

```python
KIND_COST_MULTIPLIER = {
    TransportKind.SHAPE_BELT: 1.0,
    TransportKind.FLUID_PIPE: 1.0,
}
```

초기에는 동일하게 두되, capacity / merge / load 계산은 반드시 kind별로 분리한다.

---

### 11.3 중요한 예외: output stub는 fixed start point

extractor output 앞 1칸은 필수 stub다.

```text
extractor → output stub → route search 시작
```

v4에서는 하나로 확정한다.

```text
output stub는 route search의 fixed start point다.
```

처리 규칙:

```text
- output stub는 candidate route가 반드시 포함해야 한다.
- 다른 route가 optional하게 통과하는 일반 cost 0 cell이 아니다.
- route search의 start node는 extractor core가 아니라 output stub다.
- Pass3도 fixed output stub를 제거하거나 우회할 수 없다.
```

구현 형태:

```python
start = fixed_output_stub[cell_for_extractor]
route = find_route(start=start, goals=goal_set, ...)
assert route[0] == start
```

---

### 11.4 baseline_route_length 정의 및 단계별 ratio

`baseline_route_length`는 다음처럼 정의한다.

```text
baseline_route_length = 같은 start stub와 같은 goal set에 대해,
geometry constraint만 적용한 shortest feasible route length
```

기준 route:

```text
- extractor/extension/hard barrier는 blocked
- fixed output stub에서 시작
- RouteZone penalty는 사용하지 않음
- capacity penalty는 사용하지 않음
- 같은 TransportKind goal set 사용
```

단계별 ratio는 동일하게 두지 않는다.

| 단계                                 |                   제한 | 이유                                            |
| ---------------------------------- | -------------------: | --------------------------------------------- |
| STEP 4 initial merge-aware routing | `<= baseline * 1.50` | trunk merge와 capacity split 때문에 약간 긴 route 허용 |
| STEP 5 Pass3 rerouting             | `<= baseline * 1.35` | 내부 transport 최적화 목적이지만 과도한 우회 방지              |
| STEP 6 Reclaim incremental routing | `<= baseline * 1.20` | 추가 extractor 하나 때문에 긴 내부 route가 생기는 것을 강하게 제한 |
| Recovery routing                   | `<= baseline * 2.00` | 연결성 회복이 우선이므로 예외적으로 완화                        |

Recovery routing에서 길이 비율을 완화하더라도 **soft_protected corridor 교체는 §14.3의 atomic replace 규칙을 따른다**(replacement 없이 기존 통로만 버려 orphan trunk를 만들지 않음). recovery 전용 추가 규칙은 §14.3 참고.

**`baseline_route_length` 재계산(정본)**: `baseline_route_length`의 **정의**(§11.4 본문)는 고정이다. Reclaim commit으로 `all_committed_placements`·`final_route_cells`·blocked 집합이 바뀌면, **ratio 검사 직전**마다 해당 stub·goal set에 대해 baseline을 **다시 계산**한다(이전 스냅샷 baseline을 그대로 쓰지 않는다). **Post-reclaim Pass3 rerun(§12.5)**: rerun **직전** 스냅샷의 placements·blocked·goal set으로 baseline을 구한 뒤, rerun 산출 route와 비교한다. `baseline_internal_transport_at_reclaim_entry` 같은 **metric 스냅샷**과 혼동하지 않는다(내부 transport 지표 vs route geometry baseline).

정확도: 중간. ratio는 튜닝 후보이며 QA 결과로 조정한다.

---

## 12. STEP 6 — Reclaim Placement Loop

### 12.1 목적

Pass3가 내부 transport를 줄여 확보한 공간을 실제 placement 개선으로 연결한다.

v3의 문제는 다음이었다.

```text
Pass3가 내부 transport를 줄였지만,
Reclaim loop의 incremental route가 다시 내부 transport를 늘려 Pass3 최적화를 역행할 수 있었다.
```

v4에서는 Reclaim loop에 **internal transport budget**을 추가한다.

```text
Pass3 reroute
→ internal_transport_saved 계산
→ reclaimed_cells / freed_candidate_cells 계산
→ zone map 갱신
→ 신규 extractor + extension 후보 scan
→ incremental routing
→ internal transport budget 검사
→ capacity/connectivity validation
→ 필요 시 bounded post-reclaim Pass3 rerun
```

---

### 12.2 Reclaim candidate 조건

§4.2의 루프 요약과 달리, 본 절이 **후보 채택·gain·누적 internal transport budget의 규범(canonical) 정의**다.

```text
DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD = 1.5   # gain / additional_route_cost 최소 비율 (튜닝 범위 예: 1.2 ~ 2.5)
```

**`gain` · `additional_route_cost` 단위(정본)**: 비율 threshold가 의미 있으려면 분자·분모가 **동일 차원**이어야 한다.

```text
- gain: 신규 placement로 인해 **기대 채굴량 증가분**(slots·`slots * slot_throughput` 등으로 환산한 **expected_output/min**). 구현은 slots를 쓰되 trace에는 환산된 수치를 함께 남긴다.
- additional_route_cost: **incremental route 전체**(§11.3: **fixed output stub 셀 포함**, stub는 “cost 0 고정”이 아니며 RouteZone·KIND 보정을 **합산에 포함**한다)에 대한 **RouteZone 기반 route cost 합**(§11.1·§11.2). trace에는 필요 시 `route_cost_including_stub` / `route_cost_after_stub`로 분해해 기록해 튜닝을 돕는다. capacity penalty는 본 ratio에 넣지 않고 STEP 4·검증에서 별도 처리.
```

위 정의로 `gain / additional_route_cost`는 “채굴 이득 대비 공간·내부 우회 비용”의 **무차원 비율**로 읽는다. 다른 정의로 바꿀 경우 상수 `DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD`를 함께 재튜닝한다.

**`pass3_internal_transport_saved` · 내부 transport 스냅샷 정렬(정본)**: `pass3_internal_transport_saved`는 **STEP 5 Pass3 성공 커밋 직후** 레이아웃에서 산출한다. `baseline_internal_transport_at_reclaim_entry`(§12.5)는 **Reclaim loop 진입 직전** 스냅샷이다. **두 값 모두** “Reclaim이 아직 아무 commit도 하기 전” 동일 물리 시점의 transport를 기준으로 하므로, **STEP 5 직후 ~ Reclaim 진입 사이**에 transport를 바꾸는 처리(예: `cascade_corrective_recovery`, 수동 repair)가 있었다면 **Pass3 절약분을 그 시점 레이아웃으로 재측정**해 `pass3_internal_transport_saved`를 갱신하거나, 동일 스냅샷에서 `pass3_internal_transport_saved`와 `baseline_internal_transport_at_reclaim_entry`의 **내부 transport 집계 정의를 동일 함수**로 맞춘다. §12.2 budget 수식의 `pass3_internal_transport_saved`와 §12.5·rerun 검증의 `net_internal_transport_saved_after_reclaim` 기준선이 **서로 다른 시점 레이아웃**을 가리키면 안 된다.

신규 placement 후보는 다음 조건을 만족해야 한다.

```text
[ ] reclaimed 또는 여전히 비어 있는 mineable cell 위에 있다.
[ ] final_route_cells 위에 올라가지 않는다.
[ ] hard_protected corridor를 침범하지 않는다.
[ ] output stub를 만들 수 있다.
[ ] incremental routing이 가능하다.
[ ] capacity를 초과하지 않는다.
[ ] gain / additional_route_cost >= DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD (튜닝 시 상수명 유지·값만 변경).
[ ] incremental route length ratio가 STEP 6 제한 이내다.
[ ] 누적 `incremental_internal_transport_added`가 Pass3 절약분 budget 이내다(아래 누적 규칙).
```

권장 budget:

```text
MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO = 0.35
MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS = 1  # 튜닝: 1~2 cells
```

내부 transport budget은 **Reclaim loop 한 번의 실행 동안 누적**한다. 아래는 **commit 전 평가**와 **commit 성공 후 누적 갱신**을 분리한다.

```python
# 1) 후보 평가 (commit 전)
incremental_added = compute_incremental_internal_transport(candidate)
projected_total = total_reclaim_internal_added_so_far + incremental_added

# pass3_internal_transport_saved > 0 만 절약분으로 본다. == 0 또는 < 0(STEP 5 실패·보정으로 내부 transport가 늘어난 경우)은 동일 분기.
base_spend = floor(pass3_internal_transport_saved * MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO)
allowed_internal_spend = (
    base_spend if pass3_internal_transport_saved > 0
    else MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS
)

accept_reclaim = (
    projected_total <= allowed_internal_spend
    and (
        pass3_internal_transport_saved <= 0
        or (pass3_internal_transport_saved - projected_total) > 0
    )
)

# 2) commit 성공 시에만 누적치 갱신
if accept_reclaim and commit_succeeds:
    total_reclaim_internal_added_so_far = projected_total
```

둘째 줄은 `pass3_internal_transport_saved > 0`일 때만 “Reclaim 누적 후에도 Pass3 절약분이 남는가”(`net_internal_transport_saved_after_reclaim`과 동일 집계 정의)와 동치다.
`pass3_internal_transport_saved <= 0`(0 또는 음수)이면 **net 조건을 적용하지 않는다**(바닥 허용분만으로 전멸하는 모순 방지, §v5 Major 4). 음수는 assert로 막기보다 **절약분 없음과 동일**하게 위 분기로 처리한다.

`pass3_internal_transport_saved <= 0`인 경우에도 `allowed_internal_spend`가 0이 되면
모든 incremental 내부 경유가 금지되어 reclaim이 전멸할 수 있다. 위 **최소 바닥값**은 누적 한도가 0이 되지 않게 한다.

즉, Pass3가 내부 transport를 10칸 줄였으면 Reclaim incremental route는 기본적으로 3칸까지만 내부 transport를 다시 쓸 수 있다.

---

### 12.3 Reclaim 이후 zone map 갱신

Reclaim loop는 Pass3 당시의 zone map을 그대로 쓰면 안 된다. 신규 extractor/extension이 배치되면 zone classification이 바뀐다.

```text
Reclaim candidate provisional commit 후:
- 신규 extractor/extension cells → BLOCKED
- 신규 output stub → FIXED_STUB
- 신규 incremental route cells → zone 분류(아래). §14.2.1 **candidate_corridor → soft_protected** 승격 규칙과 동일하게,
  “replacement 검증(§14.3)까지 통과한 뒤 commit된 transport”는 **soft_protected**로 올리고,
  그 외 **일회성 probe·미검증 shadow**는 candidate_corridor로만 남긴다(§14.2.1 폐기 규칙 적용).
- 기존 placement candidate 중 점유된 셀 → candidate set에서 제거
```

**`FINAL_ROUTE` vs `SOFT_PROTECTED` (STEP 6 incremental)**:

```text
- 해당 incremental route segment가 STEP 4·Pass3와 동일하게 “최종 확정 trunk/연결 통로”로 취급될 때 → FINAL_ROUTE(또는 구현 명칭 final_route_cells에 합류).
- 위 soft 승격 조건을 만족한 corridor(§14.3 atomic replace 전제) → SOFT_PROTECTED. Reclaim에서도 **corridor를 비우기 전 replacement 선계산** 원칙은 STEP 4·recovery와 동일하다(§14.3).
```

구현 규칙:

```python
route_zone_map = rebuild_route_zone_map(
    mineable_cells=mineable_base,
    committed_placements=all_committed_placements,
    final_route_cells=final_route_cells,
    fixed_output_stubs=fixed_output_stubs,
    hard_protected_corridors=hard_protected_corridors,
    soft_protected_corridors=soft_protected_corridors,
)
```

incremental routing은 항상 **갱신된 zone map**을 사용한다.

---

### 12.4 Reclaim loop에서 route 제거 규칙

`route_cells_pass를 mineable_cur에서 제거`하는 규칙은 여기서 적용한다.

```text
Reclaim placement scan 전:
mineable_cur = mineable_base - final_route_cells - hard_protected_corridors - soft_protected_corridors - all_committed_placements
```

`soft_protected_corridors`는 §14.3 replacement·atomic replace로 해제되기 전까지 **mineable 후보에서 제외**한다(§18.2와 동일). 해제된 셀만 `mineable_cur`에 다시 포함된다.

단, soft_protected_corridor는 Pass3 또는 recovery가 replacement route를 성공적으로 검증하면 해제 가능하다.

---

### 12.5 Post-reclaim Pass3 rerun 조건

Reclaim 후 내부 transport가 budget 이내이지만 여전히 개선 여지가 있으면 Pass3를 한 번만 재실행할 수 있다.

```text
post-reclaim Pass3 rerun 조건:
- reclaim placement가 1개 이상 commit됨
- incremental_internal_transport_added > 0
- net_internal_transport_saved_after_reclaim > 0 — **의미는 아래 “진입 시점”**
- 소행성 1회 solve 기준 MAX_POST_RECLAIM_PASS3_RERUNS 미도달(§4.2)
```

**`net_internal_transport_saved_after_reclaim > 0` (rerun 진입 vs 사후)**: 목록의 `net > 0`은 **Pass3 rerun 블록을 실행하기 전**에 평가한다. 값은 **`baseline_internal_transport_at_reclaim_entry`(Reclaim loop 진입 직전 스냅샷)** 대비, **Reclaim loop가 끝난 직후·rerun 이전**에 재측정한 내부 transport 지표로부터 계산한 **잠정(provisional) net**이다. **rerun을 한 번 돌린 뒤**에야 알 수 있는 net으로 진입 여부를 판단하면 안 된다. 아래 “rerun 완료 후 검증” 블록의 `net > 0`은 **rerun 이후 metric 재계산** 결과다.

**`net_internal_transport_saved_after_reclaim` 기준선(정본)**: **Reclaim loop 진입 직전 스냅샷**의 내부 transport 지표를 `baseline_internal_transport_at_reclaim_entry`로 저장한다. Reclaim commit 및 (있을 경우) rerun 후 metric과 비교해 net 절약을 계산한다. 최초 Pass3 단독 시점과 혼동하지 않도록 스냅샷 phase를 trace에 기록한다.

**§12.2 budget과 동일 집계(정본)**: `net_internal_transport_saved_after_reclaim`(진입·rerun 후 모두)의 “내부 transport 칸 수” **집계 함수·소행성 내부 정의**는 §12.2의 `pass3_internal_transport_saved`·`incremental_internal_transport_added`와 **동일**해야 한다. §12.2 **스냅샷 정렬**절에 따라 `pass3_internal_transport_saved`를 Reclaim 직전에 재동기화했다면, `baseline_internal_transport_at_reclaim_entry`는 그 **직후** 측정값과 일관되게 둔다.

rerun 이후에도 다음이 유지되어야 한다.

```text
[ ] 모든 output connected
[ ] capacity safe
[ ] hard_protected corridor 유지
[ ] fixed output stub 유지
[ ] net_internal_transport_saved_after_reclaim > 0
```

rerun **완료 후 검증**은 STEP 5 Pass3와 **동일한 invariant**(연결성·capacity·hard protected·stub)를 적용한다.
route length ratio는 **rerun 직전**에 재계산한 **`baseline_route_length`(§11.4 재계산 절)** 대비 `<= baseline * 1.35`(§11)를 사용한다.
원본 Pass3 대비가 아니라, reclaim 이후 상태를 기준으로 한다. `net_internal_transport_saved_after_reclaim`은 rerun 후 metric을 **재계산**한다.

---

### 12.6 Reclaim loop 실패 처리

§12.2 budget·후보 조건을 만족하지 못하면 해당 후보만 reject한다. 의미는 §4.2와 동일하며 본 절은 요약이다.

```text
- 신규 placement가 없으면 loop 종료
- 신규 placement는 있으나 incremental routing 실패 시 해당 후보 reject
- internal transport budget 초과 시 해당 후보 reject(§12.2); iteration은 다음 후보 계속
- 여러 후보가 모두 routing 실패하면 Pass3 route만 유지하고 종료
- 기존 connected layout을 악화시키는 commit은 금지
```

---

## 13. Recovery Branch (파이프라인 목차 슬롯 STEP 8, 비선형)

### 13.1 Recovery는 선형 단계가 아니라 bounded branch다

Recovery는 항상 실행되는 STEP이 아니다(§4 STEP 8 슬롯 참고). 다음 실패가 발생했을 때만 진입한다.

```text
Recovery trigger:
1. STEP 4 merge-aware routing에서 output route를 만들 수 없음
2. STEP 4 capacity-aware routing에서 capacity split/additional trunk가 실패함
3. STEP 5 Pass3가 기존 connected transport를 깨뜨림
4. STEP 6 Reclaim placement의 incremental routing이 전체 연결성을 깨뜨림
5. STEP 7 post-reclaim Pass3 rerun이 기존 connected transport를 깨뜨림
6. STEP 9 Final validation에서 connectivity/capacity invariant가 깨짐
```

Recovery는 반드시 attempt limit을 가진다.

```text
MAX_TOTAL_RECOVERY_ATTEMPTS = 3
MAX_VALIDATION_RECOVERY_ATTEMPTS = 1 또는 2
```

attempt 초과 시 solver는 다음 중 하나로 종료한다.

```text
- PARTIAL_SUCCESS: offending placement/reclaim을 rollback하고 valid layout 반환
- SOLVER_FAILURE: connected/capacity-safe layout 자체를 만들 수 없음
```

---

### 13.2 Recovery trigger별 복귀 경로

**정본**: trigger별 **표 형태의 복귀 경로는 §4.3만** 유지한다. 본 절은 표를 다시 만들지 않고, 구현·리뷰용 **글머리 요약**만 둔다(§4.3·§4.3.1·§4.3.2와 문구가 다르면 §4.3이 이긴다).

```text
- STEP 4 계열 trigger: STEP 4 재시도·rollback·alternate trunk 등(§4.3 표).
- pass3_connectivity_break: Pass3 rollback → §4.3.1 절차 → **STEP 6 Reclaim placement loop**로 복귀.
- post_reclaim_pass3_connectivity_break: rerun 변경 rollback → **STEP 9**(추가 rerun 없음, §4.3.2).
- reclaim_incremental_failure: 후보 rollback → **STEP 6** 계속.
- final_validation_failure: recovery 후 **STEP 9 재검증**(STEP 4 자동 복귀 없음).
```

---

### 13.3 Recovery context 정의

```text
budget_recovery:
- demolition / reroute / corridor 변경 예산 때문에 정상 commit이 막힌 경우
- 목표: 최소 변경으로 connected route 회복

terminal_overflow_recovery:
- terminal 또는 external margin 주변에서 route/capacity overflow가 발생한 경우
- 목표: additional trunk 또는 split route 확보

merge_partial_failure:
- 일부 output stubs는 trunk에 merge되었지만, 하나 이상의 stub가 merge되지 못한 상태
- 감지 조건(정본): `routed_stub_count < total_stub_count` 이고,
  **어떤 stub s에 대해** “s에서 시작한 transport가 외부 trunk·external margin 도달 영역(§15.2)에 들어가지 못함”이 참일 때.
  (`transport_connected == false`만으로는 부족하다: 일부 stub만 trunk에 붙고 나머지는 고립인데 그래프 전체가 connected로 보일 수 있음.)
- 목표: 실패한 stub만 우회 routing하거나 soft corridor를 교체해서 전체 연결성 회복

cascade_corrective_recovery:
- STEP 4 라우팅 도중 placement rollback(§9.6) 직후 연결성·geometry가 깨진 경우에만 진입한다.
- 목표: 최소 corrective reroute 또는 국소 rollback으로 invariant 회복. Final validation(STEP 9)과 무관하다.
- 한도: MAX_CASCADE_CORRECTIVE_ATTEMPTS(§4.2). MAX_TOTAL_RECOVERY_ATTEMPTS와 별도 집계한다.

validation_recovery:
- Final validation에서 geometry/connectivity/capacity **hard invariant**가 깨진 경우에만 진입한다.
- 목표: 새 최적화(Pass3 재탐색 등)를 하지 않고 invalid 원인만 rollback 또는 최소 repair.
- invariant 유형별 처리:
  - overlap / geometry: 관련 엔티티 중 **최근 commit·낮은 우선순위 placement**부터 제거한다.
    동점이면 deterministic tie-break(예: reclaim > pass2 > pass1, 또는 placement_id).
  - connectivity 파손: 해당 구간을 사용하는 route에 대해 **replacement route가 먼저** 확보될 때만
    corridor/셀을 제거한다(§14.3 soft/hard 규칙 준수). replacement 없이 통로만 삭제하지 않는다.
  - capacity: 이 컨텍스트는 **STEP 4를 재호출하지 않는다**(§15.3: Final validation에서 새 route/trunk 생성 금지).
    routing split / additional trunk가 필요한 수준의 overflow면 근본 해결은 STEP 4 시점의 재실행·상위 오케스트레이터로 미루고,
    여기서는 **낮은 우선순위 출구를 quarantine** 하거나 이미 존재하는 할당·soft corridor만 롤백한다.
- repair 후에도 깨지면 다음 rollback 대상으로 진행하거나 attempt 소진 시 종료한다.
```

---

### 13.4 Recovery commit의 목적

일반 commit은 gain/length 조건을 엄격하게 본다.

```text
normal commit:
- gain 충분
- length 허용
- connected true
- capacity safe
```

recovery context에서는 다음 기준을 사용한다.

```text
recovery commit:
- gain/length 조건이 약해도
- 전체 연결성을 회복하고
- capacity invariant를 깨뜨리지 않으면
- 제한적으로 commit 허용
```

---

### 13.5 `commit_reason` · `rollback_reason` · `recovery_trigger` 분리

세 네임스페이스를 혼용하지 않는다.

```text
recovery_trigger:
  - STEP 4~9에서 recovery 분기로 들어갈 때만 설정(예: step4_routing_failure, pass3_connectivity_break, …).

rollback_reason / rejected_reason (committed=false 또는 placement 제거 시):
  - rollback_unrouted_placement
  - rollback_reclaim_candidate
  - rejected_by_gain_or_length
  - rejected_by_connectivity
  - rejected_by_overlap
  - rejected_by_capacity
  - rejected_by_internal_transport_budget
  - rejected_by_hard_protected_corridor
  - rejected_by_no_replacement_route   # replacement 없는 corridor 삭제 시도·실패 등
  - solver_failure_attempt_limit

commit_reason (committed=true 인 성공 커밋 분류만):
  - normal_gain
  - degraded_connected_recovery
```

`post_reclaim_pass3_connectivity_break` 같은 문자열은 **recovery_trigger**(또는 `event_type`) 전용이다. `commit_reason`에 넣지 않는다(§16.3).

---

## 14. Protected Transport Corridor

### 14.1 필요성

Pass2 / Pass3 / recovery 사이에서 이미 검증된 route가 다음 pass에서 파괴되면 연결성이 다시 깨진다.

따라서 다음 개념이 필요하다.

```text
protected_transport_corridors
```

---

### 14.2 보호 등급

| 등급                 | 의미                                             | Pass3에서 변경 가능? |
| ------------------ | ---------------------------------------------- | -------------: |
| hard_protected     | output stub, 외부 연결을 유지하는 필수 trunk, 대체 route 없음 |            아니오 |
| soft_protected     | 현재는 유효하지만 대체 route가 있으면 교체 가능한 route/corridor  |         조건부 가능 |
| candidate_corridor | probe 결과 또는 아직 commit 전 corridor               |             가능 |

#### 14.2.1 candidate_corridor 생명주기

```text
생성: routing probe / shadow 경로 계산 시 corridor 후보로 표시될 때.
승격 soft_protected: 해당 경로가 replacement 검증(§14.3 조건)까지 통과해 commit되면.
승격 hard_protected: 대체 route가 없고 trunk 불가결 조건으로 고정될 때(정책적으로 드묾).
폐기: probe 실패, 더 나은 candidate로 대체, 또는 부모 placement rollback으로 무효화될 때.
```

동일 공간에 candidate가 중복되면 최신 검증 통과 경로가 우선하고 나머지는 폐기한다.

#### 14.2.2 `hard_protected` 판정 시점(정본)

```text
- soft_protected 승격과 동일하게, **STEP 4에서 해당 trunk/route가 commit될 때** 기본 분류를 한다.
- “대체 route 없음 + trunk 불가결” 판정은 **commit 직후 증명**으로 hard로 승격할 수 있다. **candidate exhaust(정본)**: 대체·우회 route 존재를 부정하기 위해 **§10.6·구현 합의 검색 예산**(`MAX_EXPANDED_NODES_PER_ROUTE`, `MAX_ROUTE_SEARCH_MS` 등)을 소진했거나, 동일 예산·동일 tie-break 하에 **feasible 후보가 더 없음**이 결정론적으로 판정된 상태(frontier empty, goal unreachable, 또는 정책상 허용 split 후보 소진)를 뜻한다. trace에는 `replacement_search_exhausted: true`, 사용한 예산 키, 마지막 frontier 크기 등을 남긴다.
- Pass3 시작 전: STEP 4 완료 시점의 hard/soft 집합이 Pass3 허용 변경 범위의 기준이다.
- Pass3·recovery가 진행되며 교체가 일어나면 **교체 성공 시점**에 protected 집합을 갱신한다.
- Final validation은 사후 검증만 하며, 이때 새로 hard를 “발명”하지 않는다(불일치면 버그 또는 validation_recovery).
```

---

### 14.3 보호 해제 조건

soft protected corridor는 다음 조건을 모두 만족할 때만 해제할 수 있다.

```text
[ ] replacement route가 먼저 계산됨
[ ] replacement route가 connected true
[ ] replacement route가 capacity safe
[ ] output stub 전체가 여전히 외부와 연결됨
[ ] route score가 기존보다 개선됨 또는 recovery context에서 연결성 회복에 필요함
```

즉, Pass3는 hard_protected corridor를 건드리지 않고, soft_protected corridor만 **atomic replace** 방식으로 교체한다.

**Recovery routing(§11.4 ratio 완화) 추가 규칙**: 연결성 회복을 위해 긴 우회를 허용하더라도, soft corridor를 바꿀 때는 위 조건의 **replacement 선계산·atomic replace**를 완화하지 않는다. “회복에 필요함”은 새 경로가 commit된 뒤에야 기존 soft 구간을 제거할 수 있음을 뜻한다. 기존 통로만 남기고 새 우회가 그 통로에 의존하는 줄기를 **reachable에서 제외**시키는 형태는 금지한다.

---

### 14.4 trace에 필요한 필드

```text
before_return_validate:
- extractor_count
- extension_count
- baseline_after_pass2_extensions
- protected_corridor_pool_len
- hard_protected_count
- soft_protected_count
- transport_connected
```

---

## 15. Final Validation

최종 결과를 반환하기 전 반드시 검증해야 할 항목이다.

Final validation은 문제를 처음 해결하는 단계가 아니라, 앞 단계가 만든 결과를 확인하는 **assertion gate**다.

---

### 15.1 Geometry validation

```text
[ ] extractor와 extension이 겹치지 않는다.
[ ] extractor/extension 위에 belt/pipe가 없다.
[ ] belt/pipe 위에 extractor/extension이 없다.
[ ] output stub는 모든 extractor에 존재한다.
[ ] fixed output stub가 Pass3에서 제거되지 않았다.
[ ] QUARANTINED_UNROUTED placement가 남아 있지 않다.
```

---

### 15.2 Connectivity validation

```text
[ ] 모든 extractor output이 외부 route에 연결되어 있다.
[ ] transport graph가 하나의 connected component로 이어져 있다.
[ ] 모든 transport cell이 “외부 trunk 도달 가능” 영역에 속한다:
      ∀ transport cell c, ∃ path c → … → 어떤 external_margin 도달 셀 e (동일 TransportKind subgraph).
      (단순히 extractor별 외부 연결만 보는 것과 별개로, orphan belt/pipe 덩어리를 금지한다.)
[ ] external margin까지 도달하는 trunk가 존재한다.
```

**구현 참고**: 위 항목은 단일 undirected component 검사와 동일하지 않을 수 있다. extractor output에서 outward BFS와 전역 transport adjacency 검사를 함께 쓰거나, “임의 external trunk 셀 집합에서 도달 가능한 transport 전체 = 배치된 transport 전체”로 명시 검사한다.

---

### 15.3 Capacity validation

§3.6: **1차(우선)** 구현에서는 **max capacity(rated)와의 비교를 하지 않고**, 아래 항목은 **선택·후속**으로 둔다. `trunk_load` **합산 총량**은 §15.2 연결성과 별도로 trace에 남긴다.

```text
[ ] (후속) trunk capacity가 extractor output 총량(rated)을 넘지 않는다.
[ ] (후속) shape belt lane별 초과가 없다.
[ ] (후속) fluid pipe 구간별 초과가 없다.
[ ] (후속) overflow가 발견되면 validation failure이며, bounded recovery로만 되돌아간다.
```

중요:

```text
capacity overflow 해결책인 routing split / additional trunk 생성은 STEP 4에서 수행한다.
Final validation에서는 새 route를 만들지 않는다.
Final validation recovery는 MAX_VALIDATION_RECOVERY_ATTEMPTS를 초과할 수 없다.
```

---

### 15.4 Optimization validation

아래는 **품질·최적화 목표**다. §15.1–15.3 hard invariant와 구분한다.

**`baseline BFS/A*` (정본)**: 아래 조건으로 **한 번** 라우팅한 counterfactual 레이아웃의 `asteroid_internal_transport_count`를 `optimization_baseline_internal_transport`로 저장한다.

**기본 측정 시점(정본, v5.3)**: **Pass1·Pass2 placement 확정 직후, STEP 4 merge-aware routing 이전**의 occupied/blocked 맵을 입력으로 쓴다. 구현체 간 수치 비교 가능성을 위해 **이 시점을 기본값으로 고정**한다. 연구·A/B용으로 STEP 4 직후 맵을 쓰는 변형이 필요하면 **별도 필드**(예: `optimization_baseline_phase: pre_step4 | post_step4`)와 별도 수치를 trace에 **추가**하고, 본 문서 §15.4 첫 항목 checklist는 **pre_step4**만을 말한다.

```text
- 입력 레이아웃: 위 기본 시점의 동일 occupied/blocked 맵.
- goal set: STEP 4 첫 extractor와 **동일 규칙**의 exterior margin ∪ trunk_seed(§9.2)만 사용한다. merge·capacity는 적용하지 않는다.
- 라우팅: RouteZone penalty·lexicographic tuple **없이**, geometry blocked만 적용한 **단순 BFS**(또는 동일 비용의 uniform-cost)로 각 stub→goal set 최단에 가까운 feasible route를 구성.
- 집계: §12.2·§12.5와 **동일한** “소행성 내부 transport 셀” 정의로 내부 칸 수를 센다.
```

최종 solver 결과의 내부 transport가 이 baseline보다 **감소**했는지를 §15.4 첫 항목으로 본다(미달이면 optimization warning, §15.4 하단).

```text
[ ] optimization_baseline_internal_transport 대비 asteroid_internal_transport_count가 감소한다.
[ ] placement_candidate 위 transport 점유가 감소한다.
[ ] route length 증가율이 단계별 허용 범위 안에 있다.
[ ] Reclaim loop 이후에도 net_internal_transport_saved_after_reclaim > 0 이다.
[ ] Reclaim loop가 Pass3 절약분의 허용 budget 이상을 되먹지 않는다.
[ ] Pass3 이후 reclaim placement loop가 실행되었거나 불필요 사유가 trace에 기록된다.
```

**실패 시 종료 등급**: 위 항목만 불충족이고 §15.1–15.3이 모두 통과하면 **SOLVER_FAILURE가 아니다**.
기본 권장: **SUCCESS** 또는 **PARTIAL_SUCCESS**(내부 transport 목표 미달 시) + `optimization_warnings` trace.
bounded recovery(`validation_recovery`)로 묶지 않는다. recovery는 hard invariant 실패(§15.1–15.3)에만 연결한다.

Recovery routing(§11)은 길이 비율 완화로 내부 transport를 다시 늘릴 수 있다. optimization 목표와 별개로 trace에 `recovery_internal_transport_delta`(recovery 직전·직후 내부 transport 칸 수 차이)를 남긴다(§16.3).

---

## 16. Replay Visualization 목표

### 16.1 UI 요구사항

solver는 버튼 클릭 후 자동 실행된다.

**실시간 streaming(진행 중)**: 솔버 내부 **계산 cycle**을 카운트하고, **매 10 cycle마다** STEP 10(map visualization 단계)의 표시 상태를 갱신해 UI에 반영한다. 목적은 긴 탐색·배치 루프에서도 진행 상황이 끊기지 않고 스트리밍처럼 보이게 하는 것이다.

**cycle 정의(정본)**: “한 cycle”이 무엇인지(예: beam 평가 1회, 라우팅 frontier 확장 1회, reclaim 후보 시도 1회 등)는 구현에서 **단일 규칙**으로 고정하고, 재현·디버깅을 위해 trace에 `computation_cycle` 또는 동등 필드로 누적값을 남길 수 있다. UI 갱신은 **cycle % 10 == 0**일 때(0 포함) 또는 동등한 “10회마다 1회” 규칙으로 결정론적으로 수행한다.

**완료 후 replay**: solve가 끝나면 trace·pass 스냅샷을 기준으로 **step-by-step 재생**(슬라이더·play/pause 등)이 가능해야 한다. 위 streaming 간격은 **완료 후 재생 속도**와 별개다.

```text
decode 단계는 내부적으로 처리해도 되지만,
solver pass 결과는 사용자가 볼 수 있어야 한다.
```

---

### 16.2 권장 replay 단계

```text
0. Original decoded map
1. 기존 belt/pipe 제거 표시
2. 기존 extractor 제거 표시
3. 기존 extension 제거 표시
4. asteroid field / mineable mask 표시
5. Pass1 outer placement 표시
6. Pass2 internal fill placement 표시
7. merge-aware routing 결과 표시
8. Pass3 route optimization **before/after** 표시  
   - before 스냅샷: **Pass3 시작 직전**(STEP 4 routing 완료 후·STEP 5 진입 직전 동일 레이아웃).  
   - after 스냅샷: **Pass3 종료 직후**(STEP 5 성공 커밋 시점).  
   - trace에는 §16.3 `layout_snapshot_before_pass3` / `layout_snapshot_after_pass3`(또는 동등 필드)로 고정한다.
9. reclaim placement loop 표시
10. post-reclaim Pass3 rerun 표시, 발생 시
11. recovery / degraded commit 표시, 필요한 경우만
12. final layout 표시
```

---

### 16.3 trace event schema 초안

`placements_removed`는 항상 존재하는 필드가 아니다. placement 제거는 recovery demolition, rollback, quarantine 해제 실패 때만 기록한다.

`transport_kind`의 `batch_mixed`는 **혼합 trunk 허용**을 뜻하지 않는다. 하나의 trace event가 shape belt와 fluid pipe 작업을 batch로 함께 기록했을 때만 `batch_mixed`를 사용한다. 개별 route/trunk event는 반드시 `shape_belt` 또는 `fluid_pipe` 중 하나여야 한다.

```yaml
trace_event:
  run_id: string
  phase: string
  step_index: int
  computation_cycle: int | null   # 누적 계산 cycle(§16.1 정본); UI는 매 10 cycle마다 갱신
  event_type: string
  recovery_trigger: string | null  # 분기 진입 이유 (commit_reason 아님)
  layout_snapshot_before_pass3: object | null   # STEP 5 직전 동일 스냅샷(replay overlay 정본)
  layout_snapshot_after_pass3: object | null    # STEP 5 직후
  layout_snapshot_phase: string | null          # 스냅샷이 대응하는 phase enum
  placements_added: list
  placements_removed: list | null
  placements_quarantined: list | null
  routes_added: list
  routes_removed: list
  protected_corridors:
    hard: list
    soft: list
  transport_kind: shape_belt | fluid_pipe | batch_mixed | none
  search:
    search_mode: lexicographic_dijkstra | weighted_astar | baseline_shortest | failed | null
    expanded_nodes: int | null
    search_time_ms: int | null
    fallback_reason: string | null
  metrics:
    extractor_count: int
    extension_count: int
    route_cell_count: int
    internal_transport_count: int
    optimization_baseline_internal_transport: int | null   # §15.4 counterfactual baseline
    pass3_internal_transport_saved: int | null
    reclaim_internal_transport_added: int | null
    net_internal_transport_saved_after_reclaim: int | null
    placement_candidate_blocked_count: int
    transport_connected: bool
    capacity_safe: bool
    trunk_load: dict
    recovery_attempts_total: int
    validation_recovery_attempts: int
    cascade_corrective_attempts: int
    recovery_internal_transport_delta: int | null
    baseline_internal_transport_at_reclaim_entry: int | null  # §12.5 net 비교 기준선
    external_margin_bbox_source: mineable | shell | null      # §3.5
  decision:
    committed: bool
    commit_reason: string          # §13.5: 성공 커밋 분류만
    rejected_reason: string | null
    rollback_reason: string | null # §13.5: 제거·거절 사유
    optimality_guarantee: bool | null
```

`committed=false`인 이벤트에서는 `commit_reason`을 비우고 `rejected_reason` / `rollback_reason`만 사용한다(§13.5).

---

## 17. 현재 진행 상태 요약

| 영역                                    |                                상태 | 판단                                       |
| ------------------------------------- | --------------------------------: | ---------------------------------------- |
| Shapez2 copy decode                   |                               구현됨 | 사용 가능                                    |
| asteroid reconstruction               |                               구현됨 | MVP 사용 가능                                |
| mineable field inference              |                               구현됨 | decode/reconstruction 단계에서만 사용해야 함       |
| beam placement                        |                             부분 구현 | MVP                                      |
| straight extension chain              |                               구현됨 | 임시 구조                                    |
| 3방향 extension topology                |                               미완성 | 다음 핵심 작업                                 |
| cheap exterior reachability           |                               구현됨 | placement filter로 유효. 실제 route로 취급하면 안 됨 |
| output A* routing                     |                               구현됨 | 연결성 MVP                                  |
| trunk seed 기반 merge-aware routing     |                           v4에서 정의 | 구현 필요                                    |
| capacity-aware routing                |                               미완성 | route commit constraint로 처리 필요           |
| committed-but-unrouted rollback       |                           v4에서 정의 | 구현 필요                                    |
| Pass3 internal transport minimization |                               설계됨 | 구현 필요                                    |
| reclaim placement loop                | v4에서 internal transport budget 추가 | 구현 필요                                    |
| post-reclaim Pass3 rerun              |             v4에서 bounded rerun 정의 | 구현 필요                                    |
| degraded recovery commit              |                          패치 방향 있음 | 표준화 필요                                   |
| recovery attempt limit                |                           v4에서 정의 | 구현 필요                                    |
| hard/soft protected corridor          |                        v3/v4에서 정의 | 구현 필요                                    |
| replay visualization                  |                          부분 기반 있음 | stage 확장 필요                              |
| final validation schema               |                               설계됨 | P0 작업                                    |

---

## 18. 현재 핵심 문제점과 수정 방향

### 18.1 문제 1 — 채굴기 하나 + 긴 pipe 패턴

현재 일부 결과에서 extractor 하나만 멀리 배치되고 긴 pipe/belt가 연결되는 비효율 패턴이 남는다.

원인 후보:

```text
- placement gain이 route cost보다 과대평가됨
- route length penalty가 약함
- internal transport opportunity loss가 scoring에 부족함
- isolated bundle reject 조건이 약함
```

해결 방향:

```text
- bundle_score에 expected_route_cost / opportunity_loss를 반영한다.
- 최소 extension 효율 또는 최소 gain/route ratio를 둔다.
- 긴 route가 필요한 단일 extractor는 reject 또는 낮은 priority로 둔다.
```

---

### 18.2 문제 2 — Transport 위 extractor 배치

```text
Pass2 일반 placement:
- final route가 아직 없으므로 route_cells_pass 제거 규칙을 적용하지 않는다.
- Pass1 extractor/extension/fixed_stub/hard_barrier만 blocked로 본다.

Reclaim placement / incremental placement:
- final_route_cells가 존재하므로 mineable_cur에서 제거한다.
- hard_protected_corridors도 mineable_cur에서 제거한다.
- **soft_protected_corridors**도 replacement 해제 전까지 mineable_cur에서 제거한다(§12.4, §14.3).
```

구현 규칙:

```python
# Pass2
mineable_pass2 = mineable_base - pass1_occupied - fixed_output_stubs - hard_barriers

# Reclaim loop
mineable_reclaim = (
    mineable_base
    - final_route_cells
    - hard_protected_corridors
    - soft_protected_corridors
    - all_committed_placements
)
```

---

### 18.3 문제 3 — 중앙 spine 과다

최단거리 routing은 내부 중앙을 관통하는 pipe/belt를 선호한다.

해결 방향:

```text
- RouteZone cost map 도입
- 내부 transport count를 priority 1순위로 설정
- congestion_penalty를 priority tuple에 포함
- 외곽/void/trunk를 선호하는 weighted 또는 lexicographic routing 사용
```

---

### 18.4 문제 4 — Pass 경계 불명확

현재 구현은 beam placement + routing MVP 형태라 Pass1/Pass2/Pass3의 책임이 명확하지 않다.

해결 방향:

```text
- SolverRunContext 도입
- Pass1Result / Pass2Result / RoutingResult / Pass3Result / ReclaimResult / RecoveryResult 정의
- pass별 masks / placements / routes / metrics 분리
```

---

### 18.5 문제 5 — Reclaim이 Pass3 최적화를 역행할 위험

해결 방향:

```text
- pass3_internal_transport_saved를 명시적으로 계산한다.
- reclaim_internal_transport_added를 후보별로 계산한다.
- net_internal_transport_saved_after_reclaim > 0 조건을 강제한다.
- spend ratio 초과 후보는 reject한다.
- 필요한 경우 post-reclaim Pass3 rerun을 1회만 허용한다.
```

---

## 19. 다음 개발 순서

### 19.1 내부 DTO 스키마 초안 (`SolverRunContext` · Pass 결과)

구현체는 필드를 추가할 수 있으나, 아래는 trace·replay와 매핑할 **최소 공통 구조**다.

```yaml
SolverRunContext:
  run_id: string
  asteroid_signature: string | null        # 재현용 입력 해시 등
  limits:
    max_reclaim_iterations: int
    max_post_reclaim_pass3_reruns: int      # 소행성 1 solve 전체(§4.2)
    max_total_recovery_attempts: int
    max_validation_recovery_attempts: int
    max_cascade_corrective_attempts: int
    default_reclaim_gain_ratio_threshold: float
  reconstruction:
    mineable_placement_cells: list[tuple[int, int]]   # 정본: 격자 (row, col) 정수 튜플; trace 직렬화는 [row,col] 등 합의 포맷
    extraction_shell_cells: list[tuple[int, int]]
    full_barrier_cells: list[tuple[int, int]]
  routing_state:
    trunk_seed_candidates: list[tuple[int, int]]   # reconstruction과 동일 (row, col) 정본
    existing_trunk_cells_by_kind: dict      # TransportKind -> cells
    fixed_output_stub_by_extractor: dict
    final_route_cells: list
    hard_protected_corridors: list
    soft_protected_corridors: list
  metrics_snapshot:
    internal_transport_count: int | null
    baseline_internal_transport_at_reclaim_entry: int | null
    optimization_baseline_internal_transport: int | null   # §15.4; 계산 시점 trace에 명시
  placement_commit_by_id: dict             # placement_id -> PlacementCommitState
  termination: SUCCESS | PARTIAL_SUCCESS | SOLVER_FAILURE | null

Pass1Result:
  placements: list                         # extractor/extension/stub 엔티티
  occupied_cells: list
  beam_trace: list[object] | null        # Pass1 replay용 선택 필드; 비어 있으면 UI에서 beam 단계 생략 가능
  # beam_trace 최소 원소 권장(각 행 = 한 후보 또는 beam 레벨 스냅샷):
  #   beam_level: int
  #   candidate_rank: int
  #   bundle_score: float
  #   placement_ids: list[string]
  #   selected: bool
  #   reject_reason: string | null

Pass2Result:
  provisional_placements: list             # PROVISIONAL_PLACED 후보
  blocked_cells_delta: list

RoutingResult:
  routes_by_extractor: dict
  trunk_load: dict
  routing_failures: list[object] | null   # 원소당 최소 필드(직렬화 시 키 고정):
  #   stub_cell: tuple[int, int]          # 해당 extractor의 fixed output stub (row, col)
  #   extractor_id: string | null
  #   recovery_trigger: string | null     # 연쇄 실패 시 상위 trigger
  #   attempt_count: int                  # 해당 stub·STEP에 대한 시도 횟수(또는 전역 partial)
  #   final_state: QUARANTINED_UNROUTED | ROLLED_BACK | failed | null
  #   last_error: string | null             # 용량·geometry·search_exhaust 등 요약

Pass3Result:
  routes_before: list | null               # 스냅샷 또는 route id
  routes_after: list | null
  internal_transport_saved: int | null

ReclaimResult:
  iterations_used: int
  commits: list
  rejects: list
  total_incremental_internal_transport_added: int

RecoveryResult:
  trigger: string | null
  context_chain: list[budget_recovery | terminal_overflow_recovery | merge_partial_failure
           | cascade_corrective_recovery | validation_recovery]   # trace·replay 정본: 한 recovery 세션당 1레코드, escalate 시 순서 append(길이≥1). 단일 컨텍스트면 길이 1.
  attempts_delta: int
```

---

### P0 — Solver Pass 구조 고정

```text
[ ] §19.1 SolverRunContext · Pass 결과 DTO 초안 정합
[ ] SolverRunContext 정의
[ ] Pass1Result / Pass2Result / RoutingResult / Pass3Result / ReclaimResult / RecoveryResult DTO 정의
[ ] trace_event schema 고정(RecoveryResult는 **context_chain** 정본; 단일 `context` 필드만 두지 않음)
[ ] Pass1Result.beam_trace 최소 필드(beam_level, candidate_rank, bundle_score, placement_ids, selected, reject_reason) 합의·직렬화 규칙
[ ] RoutingResult.routing_failures 원소 스키마(stub_cell, extractor_id, recovery_trigger, attempt_count, final_state, last_error) 합의
[ ] placement map / final route map / fixed stub map / hard corridor map / soft corridor map 분리
[ ] recovery attempt counter 추가
[ ] solver termination state 정의: SUCCESS / PARTIAL_SUCCESS / SOLVER_FAILURE
[ ] final validation gate 추가
```

---

### P1 — Extension Candidate Generator 교체

```text
[ ] 기존 straight chain generator 유지
[ ] output 방향 제외 3방향 extension 후보 생성
[ ] extension-to-extension 연결 허용
[ ] extension orientation = parent를 바라보는 방향으로 고정
[ ] 최대 3 extension 제한 유지
[ ] canonical signature로 중복 후보 제거
[ ] extractor당 extension 효율 점수화
```

---

### P2 — Merge-Aware Capacity-Aware Routing 구현

```text
[ ] TransportKind enum 추가
[ ] trunk seed 정의 및 후보 생성
[ ] goal set = existing trunk + exterior margin 구성
[ ] fixed output stub를 route start point로 고정
[ ] route commit 시 trunk_load 갱신
[ ] capacity overflow 시 split/additional trunk 시도
[ ] belt/pipe merge 분리
[ ] merge_partial_failure 감지
[ ] PROVISIONAL_PLACED → ROUTED_CONFIRMED / QUARANTINED_UNROUTED / ROLLED_BACK 상태 전이 구현
```

---

### P3 — Pass3 Weighted / Lexicographic Routing 구현

```text
[ ] RouteZone enum 추가
[ ] route_zone_map 생성
[ ] fixed_output_stub를 start point로 처리
[ ] hard/soft protected corridor 처리
[ ] lexicographic Dijkstra 우선 구현
[ ] A* 사용 시 admissible heuristic 제한 명시
[ ] expanded_nodes / search_time_ms budget 추가
[ ] fallback search mode 구현
[ ] baseline_route_length 계산
[ ] 단계별 route length ratio 적용
[ ] asteroid_internal_transport_saved 계산
```

---

### P4 — Reclaim Placement Loop 구현

```text
[ ] Pass3 이후 reclaimed_cells 계산
[ ] final_route_cells를 mineable 후보에서 제거
[ ] 신규 extractor + extension 후보 scan
[ ] reclaim candidate provisional commit 후 route_zone_map 재생성
[ ] gain / additional_route_cost 기준 적용(DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD, §12.2)
[ ] incremental routing 수행
[ ] reclaim_internal_transport_added 계산
[ ] internal transport spend budget 적용
[ ] capacity/connectivity 검증
[ ] 필요 시 post-reclaim Pass3 rerun 1회 수행
[ ] loop limit 적용
```

---

### P5 — Recovery Context 표준화

```text
[ ] budget_recovery context 정의
[ ] terminal_overflow_recovery context 정의
[ ] merge_partial_failure context 구현
[ ] validation_recovery context 구현
[ ] trigger별 복귀 경로 구현
[ ] MAX_TOTAL_RECOVERY_ATTEMPTS 적용
[ ] MAX_VALIDATION_RECOVERY_ATTEMPTS 적용
[ ] degraded_connected_commit 허용 조건 제한
[ ] commit_reason enum 고정
[ ] hard/soft protected corridor replacement 검증
```

---

### P6 — Replay UI 확장

```text
[ ] pass별 map snapshot 저장
[ ] before/after overlay 지원
[ ] rejected candidate debug layer 추가
[ ] hard/soft protected corridor layer 추가
[ ] quarantine / rollback placement layer 추가
[ ] play / pause / slider UI
[ ] final score breakdown 표시
```

---

## 20. 최종 성공 기준

### 20.1 배치 성공 기준

```text
[ ] extractor 수가 baseline 이상이다.
[ ] extension 활용률이 증가한다.
[ ] 평균 slots/extractor가 16에 가까워진다.
[ ] extractor/extension/transport overlap이 0건이다.
[ ] QUARANTINED_UNROUTED placement가 최종 결과에 남지 않는다.
```

---

### 20.2 연결 성공 기준

§15.2 **Connectivity validation**과 동일한 강도를 쓴다(성공 판정·검증 기준 불일치 방지).

```text
[ ] 모든 extractor output이 외부 route에 연결된다.
[ ] transport graph가 하나의 connected component로 이어져 있다(동일 TransportKind subgraph 관점은 §15.2 참고).
[ ] 모든 transport cell이 “외부 trunk·external margin 도달 가능” 영역에 속한다(§15.2 전역 검사와 동치).
[ ] external margin까지 도달하는 trunk가 존재한다.
[ ] fixed output stub가 유지된다.
```

구현·UI 요약 필드 `transport_is_connected`가 있더라도, **hard 성공**은 위 §15.2 항목을 모두 만족할 때만 인정한다.

### 20.3 capacity 성공 기준

```text
[ ] shape belt trunk load가 belt capacity를 초과하지 않는다.
[ ] fluid pipe trunk load가 pipe capacity를 초과하지 않는다.
[ ] overflow 발생 시 STEP 4에서 split/additional trunk로 해결된다.
[ ] final validation에서 capacity_safe == true다.
```

---

### 20.4 transport 최적화 성공 기준

```text
[ ] 내부 중앙 transport cell 수가 감소한다.
[ ] placement candidate 위 transport 점유가 감소한다.
[ ] 외곽/void/trunk 사용률이 증가한다.
[ ] route length 증가는 단계별 허용 범위 이내다.
[ ] Reclaim loop 이후에도 net_internal_transport_saved_after_reclaim > 0 이다.
[ ] Reclaim loop가 Pass3 절약분의 허용 budget 이상을 되먹지 않는다.
[ ] Pass3 이후 reclaim placement loop가 실행되었거나 불필요 사유가 기록된다.
```

---

### 20.5 replay/debug 성공 기준

```text
[ ] 모든 pass가 trace event를 남긴다.
[ ] 모든 commit/reject에 reason이 기록된다.
[ ] route 실패 시 failed_stub / blocked_by / explored_cells가 기록된다.
[ ] capacity 실패 시 trunk_id / load / capacity / overflow_amount가 기록된다.
[ ] recovery attempt count가 기록된다.
[ ] reclaim budget reject reason이 기록된다.
[ ] UI에서 pass별 결과를 재생할 수 있다.
[ ] solve 진행 중 **매 10 계산 cycle**마다 STEP 10 visualization을 갱신해 실시간 스트리밍한다(§16.1).
```

---

## 21. 최종 요약

현재까지의 Shapez2 asteroid mining solver는 다음 방향으로 정리된다.

```text
1. Shapez2 copy code를 decode한다.
2. 기존 blueprint에서 소행성 shell, 내부 mineable field, 기존 transport를 복원한다.
3. 기존 건물과 transport는 solver 관점에서 초기화한다.
4. extractor + 최대 3 extension bundle 후보를 생성한다.
5. Pass1에서 외곽부터 배치한다.
6. Pass2에서 남은 내부 mineable cell을 보강하되, route 확정 전 placement는 provisional 상태로 둔다.
7. STEP 4에서 trunk seed 기반 merge-aware, capacity-aware routing으로 모든 output을 외부에 연결한다.
8. routing 실패 placement는 quarantine 후 recovery 또는 rollback한다.
9. Pass3에서 내부 중앙 transport를 줄이고 외곽/void/trunk 쪽으로 밀어낸다.
10. Pass3가 확보한 공간은 reclaim placement loop에서 다시 활용한다.
11. Reclaim route는 Pass3 내부 transport 절약분의 budget 이내에서만 허용한다.
12. 필요하면 post-reclaim Pass3를 제한적으로 1회 재실행한다.
13. 복구 상황에서는 연결성 회복을 위해 degraded commit을 제한적으로 허용하되 attempt limit을 둔다.
14. 모든 과정을 trace와 visualization replay로 검증한다(진행 중에는 §16.1에 따라 10 cycle마다 UI 스트리밍 갱신).
```

본 문서의 파이프라인은 **구현 백지(§0)** 를 전제로 한다. 레포에 남아 있을 수 있는 단편 코드·스캐폴딩은 **정본이 아니다.**

구현 착수 시 권장 우선순위(동일 전제에서 순서는 프로젝트에 맞게 조정):

```text
1. extension 후보 생성기를 straight chain이 아닌 3방향 topology 목표에 맞춘다.
2. STEP 4를 trunk seed 기반 merge-aware, capacity-aware routing으로 구성한다.
3. Pass3 weighted / lexicographic routing으로 내부 transport를 최소화한다.
4. Pass3 이후 reclaim placement loop를 internal transport budget 기반으로 구현한다.
5. recovery attempt limit, trigger별 복귀 경로, committed-but-unrouted rollback을 구현한다.
```

최종 solver의 방향은 명확하다.

```text
채굴량을 늘리는 것만이 아니라,
채굴 후보 공간을 보존하면서,
모든 output을 외부로 안정적으로 연결하고,
Pass3가 확보한 공간을 budget 안에서 다시 placement로 회수하며,
Recovery와 Reclaim의 반복을 제한된 control flow 안에서 관리하고,
그 과정을 사람이 검토 가능한 형태로 재생하는 solver.
```
