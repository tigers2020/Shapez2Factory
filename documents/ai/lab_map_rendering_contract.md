# Lab map: 렌더링·방향 계약 (구현 메모)

CANON 아님. [`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`](../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) 구현과 동기화한다.

## Canonical 방향

- 정수 `0–3`: **0 = East, 1 = South, 2 = West, 3 = North**
- quarter-turn은 **clockwise** (화면에서 `rotate(90deg)`와 동일한 부호 감각).
- 서버/도메인 `cell.rotation` 값은 **표시·저장 모두 변경하지 않는다.** 스프라이트만 보정한다.

## Domain rotation contract (요약)

- **R = 0 → East**, R는 **시계방향** quarter-turn 증가.
- 스프라이트 보정은 **표시 전용**: `LAB_SPRITE_REGISTRY`의 `offsetQ` / `rotationCombine`와 `<img>`의 CSS `rotate`만 사용한다.
- 도메인 `R`에 `+1` 등 임의 변형을 넣지 않는다. 전역 부호 반전은 **전체 샘플이 체계적으로 반대**로 관측될 때만 display-only로 검토하고, 레지스트리와 **동시에** 적용하지 않는다.

## 검증 절차 (회전 이슈)

- `#lab-root`에 `data-lab-debug-rotation="1"`로 R/S 오버레이.
- 소수 셀에 대해 `tile_type` / 스프라이트 파일 / 서버 `R` / 기대 방향 / 현재 `S` 표를 적은 뒤, **레지스트리 한 축**만 조정한다.

## 스프라이트

- **파일명**을 키로 하는 `LAB_SPRITE_REGISTRY`: 항목별로 `offsetQ`, `rotationCombine` (`add` | `sub`), `nativeFacing`(현재 전부 East)를 명시한다. `tile_type`으로 파일명을 정할 수 없을 때만 `cell_kind` 소수 매핑(`fluid_miner` 등)으로 보조한다. `space_pipe` 같은 모호한 kind만으로는 스프라이트를 고르지 않는다.
- 화면 quarter-turn은 `combineSpriteRotation(normalizeQuarterTurns(serverRotation), spec)` 결과에만 의존한다.
- 스프라이트는 **`background-image`가 아니라 `<img class="lab-cell-sprite">`** 로만 그린다. 회전은 **`img`에만** `transform`을 적용한다.
- 베이스 URL은 `#lab-root`의 `data-lab-sprite-base`(Django `{% static 'web/assets/sprites/' %}`)에서 읽는다.

## 번들 브리지

- `bundle_links` 문자열의 `e` / `s` / `w` / `n`은 `LINK_KEY_TO_DIR` → `DIR_TO_BRIDGE_SUFFIX`를 거쳐 `lab-bundle-bridge-*` 클래스로만 붙인다 (CSS 기하는 [`assets/css/input.css`](../../assets/css/input.css)의 `#lab-replay-grid --lab-cell-gap`과 정합).

## 뷰포트

- `#lab-replay-grid-viewport`는 **16:9** 고정 비율(`aspect-video` 등)로 두고, 내부는 `overflow: hidden`, `touch-action: none` 등으로 브라우저 제스처·선택과 겹침을 줄인다.
- `#lab-replay-grid-stage`의 `transform`은 **`translate(tx, ty)`만** 사용한다 (`transform-origin: 0 0`). 줌은 stage `scale()`이 아니라 **그리드 셀 한 변(px)** = `labZoomedCellEdgePx(replayFitBasePx, zoom)`(리플레이) / `labZoomedCellEdgePx(demoBaseCellPxAtZoom1, zoom)`(데모)로 `grid-template-columns` / `rows`에 반영한다(디바이스 픽셀 스냅으로 흐림 완화).
- `translate(tx, ty)`는 **device pixel**에 맞게 스냅한다 (`snapToDevicePixel`).

## 디버그

- `#lab-root`에 `data-lab-debug-rotation="1"`이 있거나 JS 상수 `LAB_DEBUG_ROTATION`이 true이면 `#lab-replay-grid`에 `lab-debug-rotation` 클래스가 붙고, 스프라이트가 있는 셀에 `data-r` / `data-sprite-q`가 채워질 때 R/S 오버레이가 보인다.

## SVG 자산

- `space_pipe_*` Lab 스프라이트도 **East-facing·R=0 = 디코드 연결**에 맞추고, 표시는 `LAB_SPRITE_REGISTRY`에서 광물과 같이 `add`·`offsetQ: 0`으로 둔다(한 파일만 어긋날 때는 그 항목만 예외 조정).
- 신규 Lab용 layout 스프라이트는 **East-facing** 기준으로 작성한다.
- `viewBox="0 0 100 100"` 권장; 기존 96 좌표계는 스케일 래핑으로 맞출 수 있다.
