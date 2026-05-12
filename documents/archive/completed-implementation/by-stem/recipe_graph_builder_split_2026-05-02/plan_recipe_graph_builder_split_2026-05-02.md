# Plan: recipe_graph_builder split (2026-05-02)

관련 리서치: [documents/research_recipe_graph_builder_split_2026-05-02.md](./research_recipe_graph_builder_split_2026-05-02.md)

원본 요청 요약: graph builder의 node/edge 조립 책임을 더 작은 helper로 분리하되, 현재 graph 결과 계약은 유지한다.

## 구현 접근

1. `build()` 앞단에서 usage 분석(`used_output_keys`, `reused_counts`)을 helper로 분리한다.
2. source shape node 생성 로직을 helper로 추출한다.
3. operation node 생성과 input edge 생성 로직을 helper로 추출한다.
4. output shape node 생성과 output edge 생성 로직을 helper로 추출한다.
5. preview scene 직렬화는 독립 helper로 유지하되, builder 본문에서는 호출만 하도록 정리한다.

## 호환성 기준

- `RecipeGraphBuilder.build()` 공개 시그니처는 유지한다.
- target/source/intermediate role 판정은 바뀌면 안 된다.
- `Target` / `Target xN` label 규칙은 유지한다.
- `Output B (unused)` 같은 unused output 표시는 유지한다.
- `quantity`, `reused_count`, `preview_scene` payload는 그대로 유지한다.

## 검증

- `python -m pytest tests/unit/shapez_solver/test_solver_service.py`
- `python -m pytest tests/unit/shapez_solver/test_factory_throughput_service.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m mypy django_apps/shapez_solver/services/recipe_graph_builder.py`
- `python -m ruff check django_apps/shapez_solver/services/recipe_graph_builder.py`
