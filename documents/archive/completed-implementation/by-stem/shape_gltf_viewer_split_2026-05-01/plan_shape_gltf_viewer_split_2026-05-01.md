# Plan: shape_gltf_viewer split (2026-05-01)

관련 리서치: [documents/research_shape_gltf_viewer_split_2026-05-01.md](./research_shape_gltf_viewer_split_2026-05-01.md)

원본 요청 요약: [django_apps/web/static/web/js/shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) 를 책임 단위 ES 모듈로 나누되, 공개 API `mountShapeGltfViewer` / `disposeShapeGltfViewer` 와 자동 마운트 동작은 기존 진입점에 남겨 호환성을 유지한다.

## 범위

- 신규 폴더 [django_apps/web/static/web/js/shape_gltf/](../../../../../django_apps/web/static/web/js/shape_gltf/) 를 만든다.
- `shape_gltf_viewer.js` 에서 상수, 로더, 재질, transform, transitions, renderer, render_scene, ui_modes 를 순차 추출한다.
- 기존 진입점은 import, `viewerStates` WeakMap, `mountShapeGltfViewer`, `disposeShapeGltfViewer`, auto-mount 루프만 남기는 얇은 facade로 정리한다.

## 구현 접근

1. `constants.js`, `model_loader.js`, `materials.js` 를 먼저 추출해 데이터/로딩/재질 책임을 분리한다.
2. `transform.js`, `transitions.js` 를 추출해 위치 계산과 애니메이션 보간을 entry에서 분리한다.
3. `renderer.js`, `render_scene.js`, `ui_modes.js` 를 추출해 scene 구성과 UI 이벤트 wiring을 정리한다.
4. 마지막에 [django_apps/web/static/web/js/shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) 를 facade 형태로 축소한다.

## 호환성 기준

- `import "./shape_gltf_viewer.js"` 와 `import { mountShapeGltfViewer, disposeShapeGltfViewer } from "./shape_gltf_viewer.js"` 는 그대로 동작해야 한다.
- `data-shape-gltf-viewer` + `data-shape-gltf-auto-mount` 자동 마운트는 기존과 같은 시점에 실행되어야 한다.
- 렌더 결과, 모드 전환(`original`, `layer`, `quadrant`), dispose 동작은 시각 스펙 변경 없이 유지한다.

## 검증

- `pytest` 로 스모크를 확인한다. 최소 [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) 의 정적 자산 참조가 계속 통과해야 한다.
- 가능하면 데모 페이지에서 뷰어 mount, 모드 전환, dispose 경로를 수동 확인한다.
- JS 변경 중심이라도 저장소 규칙상 최종 보고에는 미실행 검증과 남은 위험을 명시한다.

## 비범위

- `vendor/three` 편집은 하지 않는다.
- 뷰 모드 추가, 상수 튜닝, 시각 리디자인은 하지 않는다.
