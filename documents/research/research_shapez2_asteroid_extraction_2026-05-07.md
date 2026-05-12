# 소행성 추출 파이프라인 — 리서치 메모 (2026-05-07)

## 목적

Island 블루프린트 복사 디코드에서 **채굴 가능 영역 재구성 → 배치 → 라우팅**까지 가는 솔버 입력을 정의한다. 본 문서는 구현 가정과 출처·불확실성을 고정한다.

## 디코드 격자 규칙 (레포 정본)

- `BP.Entries` 및 중첩 객체(예: `Building.Entries`)에 포함된 항목 중 `X`가 정수이고 **`X != 0`** 인 항목만 맵·솔버에 사용한다 ([architecture.mdc](../../.cursor/rules/architecture.mdc)).
- **동서 이웃**: 좌표 `(-1,y)`와 `(1,y)`는 `x=0` 열이 없으므로 **한 칸 붙어 있다**. 경로·빔·출구/확장 줄은 `shapez_grid.step_cardinal` / `neighbors4` 규칙을 따른다. **소행성 레이아웃 솔버**(`services/asteroid_mining_layout`, 외곽 스캔·번들 배치·void 병합 라우팅)도 동일 규칙을 사용한다(단순 데카르트 이웃 금지).
- `T`는 문자열 레이아웃/내부 변형 이름이다. [style_classifier.py](../../django_apps/shapez_asteroid/services/style_classifier.py)로 일부를 `PlotStyle`에 매핑한다.

## 암석 마스크 (MVP 근사)

### 소스 오브 트루스 결정 (2026-05-07)

**승안: 결정 게이트 옵션 2 (MVP barrier / 채굴 주변 패치 근사).** 상세 및 후속 검토 조건은 [plan_asteroid_extraction_solver_occupancy_gate_2026-05-07.md](../plans/plan_asteroid_extraction_solver_occupancy_gate_2026-05-07.md) 참조. 구현 정본 함수는 [`asteroid_reconstruction.py`](../../django_apps/shapez_asteroid/services/asteroid_reconstruction.py).

복사 코드에 “순수 암석만” 좌표가 별도 레이어로 없을 수 있다. MVP에서는 다음을 채택한다.

1. **전역 격자 스캔**: 디코드 트리를 재귀 순회하며 `X != 0` 인 모든 항목의 `(x, y)`를 수집한다.
2. **장벽 집합 `full_barrier`**: 위 좌표 전부(내부 변형·벨트·건물 외곽 등 포함). 패치 내부 알고리즘의 닫힌 루프 판별에 사용한다.
3. **벨트·파이프 셀**: `PlotStyle.belt` / `pipe`로 분류된 좌표. **새 추출기 코어는 놓을 수 없음** (겹침 금지).
4. **배치 가능(`mineable_placement_cells`, 솔버 정본)**: 추출류 셀로 이룬 **쉘**(기존 `is_extraction_style`와 동일)에 대해 `compute_patch_interior_cells(shell)` 과 쉘의 합집합에서 **`belt` / `pipe` 좌표를 제외**. (옛 문구의 `compute_patch_interior_cells(full_barrier)` ∪ 추출류 표현은 패치 형태 차이 가능성이 있어, 구현 단일 정본으로 위 집합을 사용한다.)
5. **라우팅 hard block**: `blueprint_occupied_cells` / `full_barrier`는 라우팅 벽이 아니다. rebuild 라우팅은 새로 배치한 추출기 코어·익스텐션 footprint와 명시적 `transport_hard_block_cells`만 hard block으로 쓰며, 이미 라우팅한 transport는 soft trunk로 재사용한다(역방향 edge만 금지).

6. **한계**: 레이아웃별 **다칸 footprint**는 아직 미반영(모든 엔트리 **1×1**). 리서치 확장 시 `T`+`R` 기반 footprint 표를 본 문서에 추가한다.

## Pipe routing preferences (2026-05-07)

- **Extractor/extension**: 파이프 스텝은 `blocked_static`(배치 클러스터 footprint + `transport_hard_block_cells`)에 의해 해당 셀을 밟지 않는다.
- **Mineable**: 채굴 가능 격자 위를 **완전 금지하지 않고**, A* 스텝 가산 비용 + 그리디 `_route_aware_score`에서 mineable 위 경로 셀 수만큼 패널티해 광맥 밖 선호를 만든다.

### 도형 채굴기 `R` (2026-05-07 구현, 잠정)

- 격자: **+X 동, +Y 남** (블루프린트 디코드와 동일).
- 솔버가 **새로 놓는** 코어에 대해 `R % 4`는 벨트가 붙는 **출구 쪽 이웃 한 칸**을 고른다: R=0 동, 1 남, 2 서, 3 북 (`shape_miner_rotation.py`).
- **확장**은 출구의 **반대 방향**으로만 일직선(최대 `EXTENSION_MAX_PER_CLUSTER` 및 빔 `BEAM_ENUM_MAX_EXTENSION_DEPTH` 캡).
- 인게임 `R`과 1:1 대응은 **자산 검증 전 잠정**이며, 검증 후 오프셋 순서·시작각만 조정하면 된다.

## 처리량 상수 (가정 표, 출처)

| 항목 | 값 | 비고 |
|------|-----|------|
| 도형 슬롯당 생산 | 45 items/min | 위키 “Miners” 등 커뮤니티 자료와 정합 목표 |
| 코어 슬롯 수 (shape) | 4 | MVP: 확장 없이 코어 1셀 = 4슬롯 |
| 확장당 슬롯 | +4, 최대 3확장 | 설계 문서; 빔 열거 깊이는 `BEAM_ENUM_MAX_EXTENSION_DEPTH`로 캡 |
| 벨트 레인 처리량 | 480 items/min × 12 | 장기 capacity-aware 라우팅용 |
| 파이프 | 28200 × 12 / min | 동상 |

코드 상수는 [extraction/constants.py](../../django_apps/shapez_asteroid/extraction/constants.py)에만 둔다.

## 클러스터 정규화 (동치)

- 클러스터는 **코어 1셀 + 출구 반대 일직선 확장**(최대 3확장, 빔 열거 깊이 캡). 코어에 **`rotation`(`R`)** 이 붙어 벨트 출구 격자가 정해진다.
- **`normalized_cluster_signature`**: 코어를 원점으로 둔 상대 좌표의 회전 정규화(`canonicalize_cluster`) — `R`은 시그니처에 아직 미포함.
- 정규화가 거칠면 서로 다른 배치를 동치로 합쳐 최적을 놓칠 수 있으므로, footprint 도입 시 동치 클래스를 본 절에 갱신한다.

## 라우팅 격자 (expanded bbox)

- 무한 평면 금지. 암석·장벽의 tight bbox에 **margin**을 더한 직사각형 안에서만 A* 탐색한다 (상수 `ROUTING_BBOX_MARGIN`).
- MVP 비용: 유클리드 격자 맨해튼; **용량 포화는 무시**하되 DTO `RouteEdge`에 `used_capacity` / `max_capacity` 필드를 예약한다. 기존 routed transport는 경로 장애물이 아니라 재사용 가능한 trunk 후보이다.

## 유체 추출기(펌프) — 파이프 입구·외부 연결 (검증)

MVP 규칙(게임 근거 세부는 추후 `R`/footprint 표로 정밀화):

1. 분류 `PlotStyle.extractor`(예: `PumpDefaultInternalVariant`)인 각 셀에 대해, **입구 격자**는 `R % 4`에 따른 한 칸 오프셋(시드 `fluid_miner.json`으로 R=1→남쪽, R=3→북쪽 등 4방 순환 보정).
2. 그 칸은 블루프린트에 존재해야 하며 **`pipe` 스타일**(이름에 `pipe` 포함 등)이어야 한다. 벨트는 유체 입구로 치지 않는다.
3. 입구 파이프에서 **파이프 셀만** 4방으로 BFS했을 때, 이웃 중 **`full_barrier`에 없는 좌표**(복사본 발자국 밖의 공석)에 닿으면 “외부 연결”로 본다.

구현: `extraction/extractor_pipe_rules.py`, 솔브 결과 `extractor_pipe_layout` / `metrics.extractor_pipe_ok`.

## UI partial

- 폴링에는 **현재 best** 요약만(수치 + 소형 `placements` / 오버레이 점 목록). Beam 프론티어 전체는 전송하지 않는다.

## Shapez2-MIP-Miner 참조 (2026-05-08)

- 외부 구현은 Gurobi MIP로 miner/extender/belt/flow 변수를 동시에 두고 extraction throughput을 최적화한다: <https://github.com/jiahao-0204/Shapez2-MIP-Miner>.
- 본 프로젝트는 Gurobi 의존성을 도입하지 않는다. 대신 beam 후보를 A* 라우팅으로 검증한 뒤 **covered cells → saturated slots → route length → cluster count** 순서의 route-aware score로 실제 사용 subset을 고른다.
- pipe는 belt의 directed edge 제약을 그대로 쓰지 않고, 기존 pipe network 또는 exterior로 합류 가능한 하나의 4-connected network인지 검증한다.

## 참고 링크 (외부)

- shapez2.wiki.gg — Miners / 확장 슬롯 설명
- 스팀 커뮤니티 가이드 — 레인·처리량 설명
- 커뮤니티 블루프린트 관행 — 4/8/12/16 슬롯 정렬 (`full_lane_bonus` 휴리스틱 옵션 근거)
