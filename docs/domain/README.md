# Domain Manual

**소유**: 도미닉 (`persona/dominic.md`)

에이전트·사람이 빠르게 읽는 **요약**이다. 계약 정본은 `documents/` (CANON)이며, 코드는 Phase 1에서 `django_apps/*/domain/`에 있다.

## 역할

- 도메인 용어, 불변식, 정책을 한곳에서 찾을 수 있게 한다.
- `docs/domain/` 요약과 `documents/` 정본이 충돌하면 **정본을 먼저 수정**하고 요약을 뒤따르게 한다.
- Phase 2+ 추출 시 `src/shapez2_factory/domain/`이 이 문서를 따른다.

## 도메인 용어

| 용어 | 설명 | 정본 |
|---|---|---|
| Shape / ShapePart | SW→NW→NE→SE 인코딩, 레이어·분면 | [`documents/game_rules/shape_encoding.md`](../../documents/game_rules/shape_encoding.md) |
| Recipe graph | 중간 도형 노드 경유 DAG; 연산 출력→연산 직접 접합 금지 | [`documents/game_rules/solver_graph_dag.md`](../../documents/game_rules/solver_graph_dag.md) |
| Factory demand | demand summary · source quantity · target output · materialized nodes 구분; 요약 일치 ≠ 연결 증명 | [`documents/game_rules/solver_quantity_flow.md`](../../documents/game_rules/solver_quantity_flow.md) |
| Operation node | Cutter·Rotater·Stacker·Painter 등; 메타는 `shapez_solver` | [`documents/game_rules/solver_operation_interface.md`](../../documents/game_rules/solver_operation_interface.md) |
| Asteroid Lab replay | Lab / Optimization **듀얼 트랙**; optimization은 output-only 관측 | [`documents/Algorithm/`](../../documents/Algorithm/) · [`asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc) |
| Blueprint grid | Server `X`/`Y`; **`x == 0` 불법**; dense X 슬롯 시각화 | [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../../documents/research/research_blueprint_grid_coordinates_2026-05-10.md) |
| Route domain | candidate probe·commit 시 단일 스냅샷 소유 | [`documents/Algorithm/`](../../documents/Algorithm/) · [testing.md § Domain invariants](../../documents/ai/manuals/testing.md#domain-invariants-that-must-be-test-protected) |

게임 시스템 개요: [`documents/research/research_shapez2_game_systems_2026-05-01.md`](../../documents/research/research_shapez2_game_systems_2026-05-01.md)

## 불변식 (요약)

상세·테스트 표: [testing.md § Domain invariants](../../documents/ai/manuals/testing.md#domain-invariants-that-must-be-test-protected), [@asteroid-lab-invariants.mdc](../../.cursor/rules/asteroid-lab-invariants.mdc).

- **INV-SG-1**: 연산 출력은 중간 Shape 노드를 거친다; operation→operation 직접 엣지 금지.
- **INV-SG-2**: demand summary 일치만으로 materialized graph 연결을 증명하지 않는다.
- **INV-AL-1**: Blueprint/server 좌표에서 `x == 0`은 불법; 디코드·API·솔버 입력에서 제외.
- **INV-AL-2**: Lab replay와 Optimization replay는 인덱스 동기화 없음; optimization은 관측·메타 보조 트랙.
- **INV-AL-3**: `route_domain`은 `RouteDomainSnapshotBuilder` 단일 소유; 다중 patch 금지.
- **INV-AL-4**: validation은 repair 없음; topology·경로를 고치지 않는다.
- **INV-AL-5**: `failure_reason`·`event_type`·`issue_code`는 enum/const; 자유 문자열 금지.
- **INV-AL-6**: replay·artifact·metrics를 solver/algorithm **입력**으로 쓰지 않는다.

## 코드 매핑 (Phase 1)

| 개념 | 현재 코드 |
|---|---|
| Shape algebra | `django_apps/shapez_core/domain/` |
| Solver domain helpers | `django_apps/shapez_solver/domain/` |
| Planner / recipe graph | `django_apps/shapez_solver/services/` |
| Asteroid optimization | `django_apps/asteroid_lab/optimization/` |
| Replay / snapshots | `django_apps/asteroid_lab/replay/` |

## 파일 구성 규칙

- 파일 하나는 하나의 개념(엔티티/값 객체/정책)만 다룬다.
- 파일명은 `<개념명>.md` 형식으로 한다.
- 새 파일 추가 시 이 README 목차를 갱신한다.

## 참조

- [Architecture](../architecture/README.md)
- [ADR](../adr/README.md)
- [documents/game_rules/](../../documents/game_rules/README.md)
