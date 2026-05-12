# 매크로 다층 타일 미리보기 활성화 (2026-05-06)

## 목표

매크로 레시피 그래프에서 다층 도형의 `preview_scene.cells`가 `layer_index > 0`을 포함할 때, 클라이언트 타일 스프라이트 합성(`ShapePartSpriteTileLayers`)이 폴백으로 떨어지지 않도록 `canComposeTileScene` 조건을 완화한다.

## 범위

- 포함: `frontend/recipe_graph_editor/src/ShapeSprite/compose.ts`의 `canComposeTileScene`, 해당 단위 테스트.
- 제외: Stage track UI, 솔버 인벤토리·배치 제한.

## 구현 요약

- `(layer_index, quadrant_index)` 조합 중복만 금지.
- `quadrant_index`는 0–3, `layer_index`는 0–3(패턴당 최대 4레이어와 정합).
- 셀 개수 상한 16.

## 검증

- `cd frontend/recipe_graph_editor && npm run test && npm run build`

## 승인

요청자 구현 지시로 진행(본 문서는 게이트 기록용).
