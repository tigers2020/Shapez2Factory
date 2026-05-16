# Lab map: 렌더링·방향 계약 (구현 메모)

CANON 아님. [`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`](../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) 구현과 동기화한다.

## Canonical 방향

- 정수 `0–3`: **0 = East, 1 = South, 2 = West, 3 = North**
- quarter-turn은 **clockwise** (화면에서 `rotate(90deg)`와 동일한 부호 감각).
- 서버/도메인 `cell.rotation` 값은 **표시·저장 모두 변경하지 않는다.** 스프라이트만 보정한다.

## 스프라이트

- **파일명**을 키로 하는 `LAB_SPRITE_REGISTRY`: 각 항목은 `offsetQ`, `rotationCombine` (`add` | `sub`)만 사용한다.
- 화면 quarter-turn은 `combineSpriteRotation(serverRotation, spec)` 결과에만 의존한다.
- 스프라이트는 **`background-image`가 아니라 `<img class="lab-cell-sprite">`** 로만 그린다. 회전은 **`img`에만** `transform`을 적용한다.
- 베이스 URL은 `#lab-root`의 `data-lab-sprite-base`(Django `{% static 'web/assets/sprites/' %}`)에서 읽는다.

## 번들 브리지

- `bundle_links` 문자열의 `e` / `s` / `w` / `n`은 `LINK_KEY_TO_DIR` → `DIR_TO_BRIDGE_SUFFIX`를 거쳐 `lab-bundle-bridge-*` 클래스로만 붙인다 (CSS 기하는 [`assets/css/input.css`](../../assets/css/input.css)의 `#lab-replay-grid --lab-cell-gap`과 정합).

## 뷰포트

- `#lab-replay-grid-stage`가 있을 때 `translate(tx, ty)`는 **device pixel**에 맞게 스냅할 수 있다 (`snapToDevicePixel`).

## SVG 자산

- 신규 Lab용 layout 스프라이트는 **East-facing** 기준으로 작성한다.
- `viewBox="0 0 100 100"` 권장; 기존 96 좌표계는 스케일 래핑으로 맞출 수 있다.
