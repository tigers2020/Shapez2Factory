# Lab map: 렌더링·방향 계약 (구현 메모)

CANON 아님. [`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`](../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) 구현과 동기화한다.

## Canonical 방향

- 정수 `0–3`: **0 = East, 1 = South, 2 = West, 3 = North**
- quarter-turn은 **clockwise** (화면에서 `rotate(90deg)`와 동일한 부호 감각).
- 서버/도메인 `cell.rotation` 값은 **표시·저장 모두 변경하지 않는다.** Lab 스프라이트는 East 기준 에셋에 **도메인 R만** CSS `rotate`로 반영한다.

## Domain rotation contract (요약)

- **R = 0 → East**, R는 **시계방향** quarter-turn 증가.
- **파일별 회전 보정(offset 레지스트리)은 사용하지 않는다.** `<img>`에 `normalizeQuarterTurns(cell.rotation)` → `rotate(90deg × R)`만 적용한다.
- 도메인 `R`에 `+1` 등 임의 변형을 넣지 않는다.

## 검증 절차 (회전 이슈)

- `#lab-root`에 `data-lab-debug-rotation="1"`로 R 오버레이.
- 소수 셀에 대해 `tile_type` / 스프라이트 파일 / 서버 `R` / 기대 방향을 적어 **도메인 R과 화면 방향**이 일치하는지 확인한다.

## 스프라이트

### 스프라이트 키 정책

| 필드 | 책임 | 예시 |
|------|------|------|
| `cell_kind` / `kind` | 도메인 의미 (`space_belt`, `space_pipe`, 등) | **Identifier와 통일 금지** |
| `tile_type` | **Canonical 스프라이트 키** = blueprint `T` = `ShapezGameIdentifier.value` | `SpaceBelt_Forward`, `SpacePipe_LeftTurn` |
| `sprite_identifier` | `tile_type`의 **alias** (wire JSON에 동시 출력) | 항상 `tile_type`과 동일 값 |
| `transport_kind` / `transport` | 도메인 채널 (`shape_belt`, `fluid_pipe`) | 스프라이트 lookup에 **직접 사용하지 않는다** |
| `rotation` | quarter-turn (0–3) | 별도 변환 없이 CSS `rotate(90deg × R)` |

**transport(belt/pipe) 스프라이트는 `tile_type`(= `sprite_identifier`) 필수다.** `cell_kind = space_belt`만으로는 variant(`Forward` / `LeftTurn` / `TripleSplitter` 등)를 구분할 수 없으므로 스프라이트를 선택하지 않는다. materializer `pick_tile_type`이 정본 T 값을 생성한다.

### JS 스프라이트 resolution 순서

1. `cell.sprite_identifier || cell.tile_type` → `labIdentifierSpriteRelpaths[t]` (DB 경로).
2. 없으면 prefix fallback: `SpaceBelt_*` → `SpaceBelt/<T>.svg`, `SpacePipe_*` → `SpacePipe/<T>.svg`.
3. 없으면 `cell_kind` → `LAB_SPRITE_CELL_KIND_TO_IDENTIFIER` (miner/extension 전용).
4. 최후 fallback: `inferTransportSpriteIdentifier(cell)` — `Forward` variant만 반환 (turn·splitter는 `tile_type` 없으면 스프라이트 포기).

### Wire JSON 계약

`unified_serialization.replay_map_view_to_json_dict`가 `full_cells` / `overlay_cells` / `cell_delta` 각 셀에 아래 두 필드를 **항상** 함께 출력한다:

```json
{ "tile_type": "SpaceBelt_Forward", "sprite_identifier": "SpaceBelt_Forward" }
```

`sprite_identifier`는 추가 처리 없이 `tile_type`과 동일한 값이다. 소비자(JS / 서드파티)는 둘 중 어느 쪽을 읽어도 무방하다.

### LAB_SPRITE_KNOWN (구 이름, 현재 없음)

이전 문서에서 언급된 `LAB_SPRITE_KNOWN` 화이트리스트 및 `labSpriteFilenameForCell`은 현재 JS 구현에 존재하지 않는다. 위 resolution 순서와 `labIdentifierSpriteRelpaths` (DB 경로 맵)이 정본이다.

- Django Admin 유전자 샘플 미니맵은 `django_apps/asteroid_lab/admin_lab_sprites.py`의 `lab_sprite_resolve(tile_type, cell_kind, rotation)`으로 **T·kind→파일**, **R→표시 quarter**를 묶는다(파일 선택에 R 오프셋은 두지 않음).

## Admin 미니맵 vs Lab 리플레이 (격자)

- **Admin 유전자 미니맵**: `decoded_json`의 server bbox **tight** 격자만 그린다. 셀 래퍼에 `data-server-x` / `data-server-y` / `data-grid-row` / `data-grid-col` / `data-linear-index` / `data-sprite` / `data-rotation-deg` 계약 속성을 둔다(`django_apps/asteroid_lab/genetic_sample_mini_map.py`, 좌표 계산은 `django_apps/asteroid_lab/lab_screen_grid.py`의 `mini_map_grid_coord`와 동일).
- **Lab 리플레이**: 동일한 dense/raw **상대 이웃** 규칙(`visualCol` + raw `y`)에 더해 **대칭 패딩**이 있을 수 있어, Admin과 **절대** 셀 인덱스를 직접 비교하지 않는다.
- **리플레이 격자 bbox** (`computeReplayGridLayout`): 모든 프레임을 훑을 때 `map_view.full_cells`뿐 아니라 **`map_view.overlay_cells`**·**`map_view.cell_delta`** 좌표도 spatial target에 포함한다. optimization `validation.completed` 등에서 miner/belt가 overlay에만 있으면 bbox 밖으로 빠져 `resolveCellIndex`가 조용히 skip되지 않도록 한다 (`collectFrameSpatialTargets` ↔ `renderReplayFrame`의 overlay paint와 동일 좌표 집합).
- **회전 quarter**는 좌표 보정과 독립이다. 가로·세로가 “화면에서 어느 쪽이 오른쪽/아래인지” 같은 문장은 **테스트·`data-*`로 증명되는 범위**에서만 단정한다(선언만으로 고정하지 않음).
- 화면 quarter-turn은 `normalizeQuarterTurns(serverRotation)`만 사용한다.
- 스프라이트는 **`background-image`가 아니라 `<img class="lab-cell-sprite">`** 로만 그린다. 회전은 **`img`에만** `transform`을 적용한다. 벡터 SVG 확대 시 **`image-rendering: auto`** 를 둔다(`crisp-edges`는 `<img>` 벡터에서 흐림·픽셀화를 유발할 수 있음).
- 베이스 URL은 `#lab-root`의 `data-lab-sprite-base`(Django `{% static 'web/assets/sprites/' %}`)에서 읽는다.

## 번들 브리지

- `bundle_links` 문자열의 `e` / `s` / `w` / `n`은 `LINK_KEY_TO_DIR` → `DIR_TO_BRIDGE_SUFFIX`를 거쳐 `lab-bundle-bridge-*` 클래스로만 붙인다 (CSS 기하는 [`assets/css/input.css`](../../assets/css/input.css)의 `#lab-replay-grid --lab-cell-gap`과 정합).

## 뷰포트

- `#lab-replay-grid-viewport`는 **16:9** 고정 비율(`aspect-video` 등)로 두고, **레이아웃 크기·클리핑 창**으로만 쓴다. `overflow: hidden`, `contain: layout paint`, `touch-action: none` 등으로 브라우저 제스처·선택과 겹침을 줄인다. **viewport에 `transform`·줌에 따른 `width`/`height` 인라인 변경을 두지 않는다.**
- `#lab-replay-grid-stage`는 `position: absolute; left: 0; top: 0; transform-origin: 0 0`이며, **팬·줌의 유일한 CSS transform 소유자**다. JS에서 `transform: translate(tx, ty) scale(zoom)` 한 번에 적용한다. `translate`의 `tx`/`ty`는 **device pixel**에 맞게 스냅한다(`snapToDevicePixel`). `zoom` 값은 그대로 `scale`에 넣는다. stage에 불필요한 `will-change: transform`은 두지 않는다(합성 레이어가 언스케일 크기로 래스터된 뒤 `scale`로 확대되면 스프라이트가 흐릿해질 수 있음).
- `#lab-replay-grid`의 `grid-template-columns` / `rows`는 **줌과 무관한 월드 셀 한 변(px)** 만 사용한다(서버 리플레이: `replayFitBasePx`, 데모: `demoBaseCellPxAtZoom1`). 셀 크기에 `zoom`을 곱하지 않는다.
- `#lab-optimization-overlay-layer`는 stage **안**에서 `#lab-replay-grid`와 형제로 두고, stage와 동일 transform을 공유한다(오버레이가 viewport transform을 소유하지 않음).
- 포인터 히트 테스트·HUD는 뷰포트 패딩을 보정한 뒤 `(viewportLocal - translate) / zoom`으로 **월드 좌표**로 역변환해 셀 인덱스를 구한다.

## 디버그

- `#lab-root`에 `data-lab-debug-rotation="1"`이 있거나 JS 상수 `LAB_DEBUG_ROTATION`이 true이면 `#lab-replay-grid`에 `lab-debug-rotation` 클래스가 붙고, 스프라이트가 있는 셀에 `data-r`이 채워질 때 R 오버레이가 보인다.

## SVG 자산

- 신규 Lab용 layout 스프라이트는 **East-facing** 기준으로 작성한다.
- `viewBox="0 0 100 100"` 권장; 기존 96 좌표계는 스케일 래핑으로 맞출 수 있다.
