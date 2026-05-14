# 소행성 레이아웃 솔버 입력 매핑

## mining_map 항목 (copy-preview 최종 스텝)

- `x`, `y`: 게임 좌표 (`x == 0` 행은 UI에서 제외되어도 서버는 무시 가능).
- `role`: `occupied` | `inferred` | `belt` | `pipe`.
- `surface`: `shape` | `fluid` (추출·패치 표면 힌트).
- `layout_kind`: `PlotStyle` 문자열 또는 `asteroid_field` 등.

## 솔버 도출 집합

| 집합 | 정의 (1차) |
|------|------------|
| `asteroid_cells` | `role in ("occupied", "inferred")` 인 모든 좌표 |
| `mineable_cells` | 1차는 `asteroid_cells` 와 동일 (전역 암석 채굴 가능으로 간주) |
| `blocked_cells` | 초기 빈 집합; 배치 시 `occupied` 로 채움 |
| `surface_by_cell` | 각 좌표의 `surface` |

라우팅은 소행성 **내부 암석 셀 관통 금지**: 좌표가 `asteroid_cells` 에 속하면 벨트/파이프 통과 불가(출구 인접 void 제외는 void 좌표로 처리).

## 격자 스텝 (no-x0)

블루프린트에 **`x == 0` 열이 없음**에 따라, 레이아웃 솔버(`django_apps/shapez_asteroid/services/asteroid_mining_layout/`)의 **외곽 판별·추출 번들 출구/확장선·void 병합 BFS**는 단순 `(x+dx, y+dy)` 가 아니라 [`shapez_grid.step_cardinal`](../../django_apps/shapez_asteroid/extraction/shapez_grid.py) / [`neighbors4`](../../django_apps/shapez_asteroid/extraction/shapez_grid.py)를 쓴다. 그렇지 않으면 `(-1,y)`↔`(1,y)` 사이에 가짜 void가 생겨 내부 열에 추출기가 깔리는 오류가 난다.

## 2-pass repair solver 규칙

### Extension 트리

- 구조는 extractor-rooted directed tree이다. 기존 “extractor 반대 방향 3칸 직선” 모델은 폐기한다.
- extractor는 output 방향 한 방향으로만 출력하고, output 한 칸은 belt/pipe 출력 타일이어야 한다.
- extension은 extractor 기준 output 방향을 제외한 3방향에 붙을 수 있다.
- extension은 부모(extractor 또는 extension)를 바라보며, 부모 방향을 제외한 3방향에 자식 extension을 둘 수 있다.
- 같은 칸에는 extension을 중복 배치할 수 없다.
- 기준 좌표 `(0, 0)`, output `E`, 정확히 3 extension은 55개, 최대 3 extension(0~3)은 71개로 고정한다. 4방향 회전 전체는 각각 220개, 284개다.

### 열거 의사코드

1. 상태는 `{extension_offset: facing_vec}`로 둔다.
2. 부모 후보는 `extractor ∪ 이미 놓인 extension 전체`이다.
3. 부모가 extractor이면 `blocked_vec = output_vec`, 부모가 extension이면 `blocked_vec = state[parent]`이다.
4. `DIRS` 중 `dir_vec != blocked_vec`인 방향에 자식을 놓고, 자식 facing은 `-dir_vec`로 둔다.
5. extractor 칸과 이미 점유된 칸은 제외하고, 정렬된 상태 튜플로 canonical 중복 제거를 한다.

### 맵 검증 8조항

1. Extractor 위치는 `mineable_cells`에 속해야 한다.
2. Output 칸은 routeable void여야 한다.
3. 각 extension 위치는 `mineable_cells`에 속해야 한다.
4. Extension 칸은 기존 pipe/belt 타일과 겹치지 않아야 한다.
5. Extension끼리 칸이 겹치지 않아야 한다.
6. 각 extension의 facing 반대편 인접 칸에는 parent가 있어야 한다.
7. Parent의 blocked 방향에는 자식을 두지 않는다.
8. Extractor output 방향 칸에는 extension을 두지 않는다.

### Repair 비용과 트리거

| 셀 종류 | 비용 |
|---------|-----:|
| 기존 pipe/belt, locked trunk, exterior 연결 | 0 |
| 빈 routeable void | 1 |
| 암석 mineable 빈 칸 | INF |
| extension / fluid_extension | 50 |
| extractor | 300 |
| map 밖 / 비통과 / protected source | INF |

현재 규칙은 암석 내부 트랜스포트 관통 금지이므로 `mineable` 빈 암석 셀은 비용 2가 아니라 `INF`로 둔다. 추후 게임 규칙상 암석 표면 경유가 허용되는 경우에만 별도 플래그로 비용 2를 켠다.

Repair는 기존 void BFS merge가 `outlet -> route_tree` 연결에 실패할 때 시도한다. `start`는 실패한 outlet이고, `goals`는 anchor와 이미 병합된 route tree이다. 가중 최단경로 tie-breaker는 총 비용, extractor 파괴 수, extension 파괴 수, 경로 길이, 회전 수 순서다. 경로가 extension/extractor를 건드리면 parent 포인터로 자식 서브트리까지 제거하고, 경로 셀은 2차 배치가 침범하지 못하는 corridor로 예약한다.

### Timeline frame id

Repair 확장을 위해 `SOLVER_STEP_IDS`는 다음 계약을 포함한다.

- `solver_pass1_bundle_0`
- `solver_connectivity_check`
- `solver_repair_path`
- `solver_demolition`
- `solver_corridor_reserved`
- `solver_pass2_bundle_0`

### 1차/2차/3차 scan 계약

- **1차 scan**: 소행성 **외곽 boundary**를 따라 extractor + extension 번들을 배치하고, 각 extractor output을 **외부 방향 transport**와 연결한다. `solver_pass1_bundle_*` frame을 남긴다.
- **2차 scan**: pipe merge 전에 반드시 실행한다. **내부 void를 inferred mining field로 채우거나 변환하는 단계가 아니다** (그 개념은 decode·map reconstruction·timeline 쪽). 1차 후 남은 공간에서 **내부 extension 진입점(anchor)**에서 외부로 **직통 spine** pipe/belt를 만들고, **spine 양쪽**에 extractor/extension 번들을 추가 배치한다. `solver_pass2_bundle_*` frame을 남긴다.
- **3차 scan**: 중앙 belt/pipe를 통째로 제거하는 것이 아니라, **줄일 수 있는 belt/pipe만 줄이고** 고가치 mining-priority 공간 위 transport를 **외곽·저가치 셀 쪽 route로 재구성**한다. 내부 transport 비용을 높게 두고 **fixed stub는 예외**로 둔다. pass2 snapshot 대비 이득일 때만 candidate를 commit한다.
- 이후 merge 루프가 1차 outlet과 2차 outlet을 모두 대상으로 파이프/벨트 연결을 처리한다.
- Repair는 전체 outlet 연결 단계에서 일반 merge가 실패했을 때만 보조로 실행한다.

단계별 체크리스트·결과 YAML·합격 조건의 정본: [`checklist_asteroid_mining_layout_multi_pass_2026-05-09.md`](checklist_asteroid_mining_layout_multi_pass_2026-05-09.md).
