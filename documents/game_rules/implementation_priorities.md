# 구현 우선순위 (프로젝트 관점)

사용자 제공 리뷰 문서의 권장 순서를 그대로 정리한다.

1. **Shape canonical model 확정** — 문자열·분면 순서·정규화 한곳에 고정 ([shape_encoding.md](shape_encoding.md), [solver_domain_model.md](solver_domain_model.md))
2. **연산을 순수 함수로 분리** — cut / rotate / stack / paint / swap / pin / crystal 등 ([solver_operation_interface.md](solver_operation_interface.md))
3. **Stacker / Cutter / Swapper / Crystal / Pin 규칙 테스트** — 위키·스니펫만 믿지 말고 게임 가능 시 교차 검증
4. **수량을 노드뿐 아니라 엣지·연산 플랜에 반영** ([solver_quantity_flow.md](solver_quantity_flow.md)) — 레시피 그래프 DTO·`recipe_graph_*` 서비스와의 정합 과제(별도 작업).
5. **재귀 단일 분해보다 BFS/Dijkstra/A* 등 탐색 레이어** ([solver_search_strategy.md](solver_search_strategy.md)) — 인벤토리/매크로 검색 등 기존 솔버 모듈 확장(별도 작업).

## 한 줄 요약

지금 단계에서는 “도형 렌더링/그래프 UI”보다 먼저 **도형 대수(shape algebra)** 를 안정화하는 것이 이득이다.
