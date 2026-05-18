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

- **화이트리스트** `LAB_SPRITE_KNOWN`: `tile_type` → 파일명 규칙으로 나온 이름이 여기에 있을 때만 `<img>`로 그린다. `tile_type`으로 파일명을 정할 수 없을 때만 `cell_kind` 소수 매핑(`fluid_miner` 등)으로 보조한다. `space_pipe` 같은 모호한 kind만으로는 스프라이트를 고르지 않는다.
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
