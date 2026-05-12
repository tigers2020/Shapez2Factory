# 게임 규칙 문서 인덱스

shapez / shapez 2 계열의 **도형 대수·솔버 관점** 규칙을 주제별로 나눈 참고 문서다. 구현 전제는 각 파일의 **근거·신뢰도**와 **미확인 시 주의** 문단을 함께 본다.

| 파일 | 요약 |
| --- | --- |
| [sources_and_trust.md](sources_and_trust.md) | 근거 출처와 신뢰도 |
| [core_abstraction.md](core_abstraction.md) | 도형을 물리가 아닌 토큰 구조로 보는 핵심 추상화 |
| [shape_encoding.md](shape_encoding.md) | 레이어·분면·코드 문자열 규칙 (**프로젝트 정본: SW→NW→NE→SE**, 공식 viewer 문자열과 다를 수 있음) |
| [operation_cutter.md](operation_cutter.md) | Cutter / Quad Cutter |
| [operation_rotater.md](operation_rotater.md) | 회전(분면 치환) |
| [operation_stacker.md](operation_stacker.md) | Stacker·같은 층 병합 vs 층 증가 |
| [operation_painter.md](operation_painter.md) | Painter(형태 유지·색만 변경) |
| [operation_color_mixer.md](operation_color_mixer.md) | 색 액체 혼합(솔버에서는 자원 의존으로 분리 권장) |
| [shapez2_spatial_model.md](shapez2_spatial_model.md) | 3D 공장 vs 도형 자체는 2D 층 구조 |
| [shapez2_cutter_outputs.md](shapez2_cutter_outputs.md) | Shapez 2 Cutter 출력 순서(east/west) |
| [shapez2_stacker_inputs.md](shapez2_stacker_inputs.md) | Stacker bottom/top 입력 역할 |
| [shapez2_swapper.md](shapez2_swapper.md) | Simulated Swapper(서쪽 반쪽 교환) |
| [shapez2_pin_support.md](shapez2_pin_support.md) | Pin·부유 도형·지지 검증 |
| [shapez2_crystal.md](shapez2_crystal.md) | Crystal Generator 요약·구현 링크 |
| [crystal_mechanics.md](crystal_mechanics.md) | Crystal 생성·클러스터·shatter·연산별 메모(정본) |
| [solver_domain_model.md](solver_domain_model.md) | `shapez_core` 실제 타입(`ShapePart`, `ShapeLayer`, `Shape`) |
| [solver_operation_interface.md](solver_operation_interface.md) | 연산 인터페이스·필수 연산 목록 |
| [solver_graph_dag.md](solver_graph_dag.md) | 중간 도형 재사용·DAG |
| [solver_quantity_flow.md](solver_quantity_flow.md) | 수량이 노드만이 아니라 엣지·플랜에도 필요 |
| [solver_search_strategy.md](solver_search_strategy.md) | 최단 경로·BFS/Dijkstra/A* |
| [implementation_priorities.md](implementation_priorities.md) | 프로젝트 기준 구현 우선순위 |

상위 도메인 리서치: [research_shapez2_game_systems_2026-05-01.md](../research/research_shapez2_game_systems_2026-05-01.md)
