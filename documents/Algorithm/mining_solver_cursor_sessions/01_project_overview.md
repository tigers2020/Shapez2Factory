# 01 — 프로젝트 개요 (§0–§3)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 없음

> 목표, 근거, 게임/배치 규칙.

> **전제**: §0 — solver 구현은 **백지 상태**를 전제로 하며, 본 문서가 설계 정본이다.

---

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

v5.4 문서 정합: **STEP 10 실시간 UI streaming** — 솔버 계산 **매 10 cycle**마다 visualization 갱신(§16.1, `14_step10_replay_ui.md`), `computation_cycle` trace·cycle 정의 정본.

v5.5 문서 전제: **solver 구현 백지** — 본 문서군은 기존 코드 완성도를 전제로 하지 않으며, 구현은 설계 정본에 맞춘다(§0 본문).

v5.6 문서 정합: **extractor 배치 시 기존 belt/pipe 연계·공용**(§3.1·§3.5 merge), Pass1 목표 보강.

v5.7 문서 정합: **RouteZone 기본 cost**(`03_data_schema_dto.md` §11.1, `PLACEMENT_OCCUPIED` 등).

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

