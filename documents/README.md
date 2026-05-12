# `documents/` 인덱스

프로젝트 Markdown 본문 언어는 [AGENTS.md](../AGENTS.md) 기준 **한국어**(코드·경로·식별자는 그대로).

## 디렉터리

| 경로 | 용도 |
|------|------|
| [`ai/`](ai/) | 에이전트용 현재 계획·체크리스트·작업 유형별 매뉴얼 |
| [`index/`](index/) | 문서 상태 enum·inventory·정본/활성/보관 읽기 우선순위 |
| [`adr/`](adr/) | 승인된 아키텍처 결정 기록. 정본 spec의 "왜"를 보강 |
| [`plans/`](plans/) | 승인 게이트 대상 **활성 실행 플랜** (주제별 `plan_*.md`; 구현 완료·참고용 쌍은 [`archive/completed-implementation/`](archive/completed-implementation/README.md)) |
| [`research/`](research/) | 플랜 선행 **조사·근거** (`research_*.md`; 1:1 쌍은 위와 동일 규칙) |
| [`notes/`](notes/) | 진행 메모·요약(장기 보관 가치가 낮은 초안) |
| [`meta/`](meta/) | 크레딧·잡 메모 등 메타 |
| [`attribution/`](attribution/) | 외부 자산·표기 |
| [`game_rules/`](game_rules/) | shapez 2 규칙·도메인 모델·솔버 추상화 정본 |
| [`Algorithm/`](Algorithm/) | asteroid mining layout 중심의 알고리즘 설계·공간 권위·리플레이/검증 스펙 |
| [`refactory/`](refactory/) | 솔버 **문서 정본 대비 drift·Epic(A–D)·Phase 0–4** 기준선·감사 매트릭스 ([refactory/README.md](refactory/README.md)) |
| [`samples/`](samples/) | shapez 2 블루프린트/디코드 예제와 분석 샘플 |
| [`ui/`](ui/) | 독립 HTML 기반 UI 레퍼런스·목업 |
| [`archive/`](archive/) | 완료·폐기된 플랜·리서치 **보관** (아래 참고) |

## 아카이브

| 경로 | 설명 |
|------|------|
| [`archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | 레이아웃 이전 시점의 Django/정렬 플랜 초안 |
| [`archive/2026-05-completed/README.md`](archive/2026-05-completed/README.md) | **2026-05**에 완료 처리한 플랜·리서치 묶음 (Python 정리, Recipe Graph Editor 일괄) |
| [`archive/completed-implementation/README.md`](archive/completed-implementation/README.md) | **구현 완료**로 분류한 실행 플랜·리서치 1:1 쌍 (`by-stem/<stem>/`) |

## 플랜 ↔ 리서치 짝·누락 (파일명 기준)

활성 본문은 `documents/plans/`·`documents/research/`에 두고, 구현이 끝난 1:1 쌍은 [`archive/completed-implementation/by-stem/`](archive/completed-implementation/README.md) 아래에 **동일 스템 폴더**로 모은다. (과거 규칙) `plan_<stem>.md`와 `research_<stem>.md`의 `<stem>`이 같으면 한 쌍으로 본다. **현재 스캔 기준** (2026-05-12 정리):

| 구분 | 스템 (예시) | 비고 |
|------|-------------|------|
| `plans/`에만 남음 (동일 스템 리서치 없음) | `asteroid_extraction_solver_2026-05-07`, `asteroid_extraction_solver_occupancy_gate_2026-05-07`, `asteroid_map_cell_status_2026-05-07`, `asteroid_mining_layout_solver_inputs_2026-05-08`, `checklist_asteroid_mining_layout_multi_pass_2026-05-09`, `corridor_runtime_contract_2026-05-11`, `decoded_existing_layout_model`, `factory_throughput`, `pass12_recoverability_class_2026-05-11`, `pass3_f_topology_branch_mvp_2026-05-11`, `solve_progress_rendering_2026-05-01`, `solver_graph_horizontal_layout_2026-05-01` | 현재 활성·백로그·체크리스트 성격으로 유지. 완료 여부가 코드로 확정된 뒤 아카이브 이동 검토 |
| `research/`에만 남음 (동일 스템 플랜 없음) | `blueprint_grid_coordinates_2026-05-10`, `merge_repair_not_found_2026-05-09`, `pass2_bundle_transport_heuristic_2026-05-08`, `shapez2_asteroid_extraction_2026-05-07`, `shapez2_game_systems_2026-05-01`, `solver_graph_generation_2026-05-02`, `solver_init_baseline_map_2026-05-11` | 상위 주제·근거·도메인 정본으로 보관; 플랜과 1:1이 아님 |
| 독립 스펙·분류 문서 | `pattern_family_macro_taxonomy`, `plan_solver_optimization_topology_2026-05-11` | 접두사 규칙과 무관한 분류/최적화 스펙. 현재는 활성 참고 문서로 유지 |
| `Algorithm/` 활성 스펙 | `mining_solver_cursor_sessions/01..14`, `route_graph_authority`, `solver_state_mutation_audit`, `progress_status_2026-05-10` 등 | asteroid mining layout의 최신 설계·세션 브리프. 구현 완료 아카이브가 아니라 현재 작업 기준 문서 |
| 세션별 아카이브 (이전 방식) | `python_dead_code_cleanup_2026-05-04`, Recipe Graph Editor 계열 | [`archive/2026-05-completed/`](archive/2026-05-completed/README.md) 참고 |
| 구현 완료 플랜+리서치 쌍 | 위 세션 아카이브 외 다수 | [`archive/completed-implementation/by-stem/`](archive/completed-implementation/README.md) |

## 최신 업데이트 기준 (2026-05-12)

- `documents/index/document_inventory.md`가 현재 정본·활성·연구·보고·보관 문서를 구분하는 1차 라우팅 표다. 새 작업은 먼저 [`documents/index/document_lifecycle.md`](index/document_lifecycle.md)의 상태 enum을 따른다.
- `documents/ai/START_HERE.md`는 새 AI 세션·서브에이전트의 context 진입점이다.
- `documents/adr/`는 bounded recovery, protected corridor, final validation, replay cycle stream의 결정 이유를 기록한다.
- `documents/ai/README.md`, `manuals/cursor_usage.md`, `manuals/testing.md`가 최신 작업 허브·검증 지침을 반영한다.
- `documents/ai/plan_pass12_stub_route_recovery_decision.md`, `documents/ai/pass12_telemetry_policy_note_2026-05-11.md`, `documents/plans/plan_corridor_runtime_contract_2026-05-11.md`, `documents/plans/plan_pass3_f_topology_branch_mvp_2026-05-11.md`는 최근 pass12/pass3/route 계약 문서다.
- `documents/Algorithm/mining_solver_cursor_sessions/`에 **01~14** 단계 브리프(`01_project_overview.md` … `14_step10_replay_ui.md`)가 있다. 한 페이지 인덱스는 [`Algorithm/mining_solver_cursor_sessions/README.md`](Algorithm/mining_solver_cursor_sessions/README.md), 경로 표는 [`refactory/01_canonical_doc_paths.md`](refactory/01_canonical_doc_paths.md)를 본다. (IDE에서 해당 폴더가 비어 보이면 워크스페이스 제외·동기화를 확인한다.)
- `documents/research/research_blueprint_grid_coordinates_2026-05-10.md`는 블루프린트 격자 좌표 정본이며, `AGENTS.md`의 `X == 0` 불가 전제와 연결된다.

## 알려진 불일치·정리 메모

1. **`notes/recipe_graph_editor_progress_2026-05-04.md`**  
   과거 `notes/`에만 두었던 스냅샷은 Phase 표가 낙후되어 **정본을 아카이브**로 통합했고, 해당 파일은 리다이렉트만 남겼다.

2. **동일 주제 문서**  
   Recipe Graph Editor는 플랜이 `plans/`와 과거 `documents/` 루트에 나뉘어 있었음 → 완료 후 **`archive/2026-05-completed/recipe-graph-editor/`** 한곳으로 모았다.

3. **`plan_recipe_graph_editor_2026-05-04.md` 내부 표**  
   본문 하단 「구현 진행 현황」은 **부분 완료** 기준이고, 같은 날짜의 **진행 스냅샷**(`recipe_graph_editor_progress_*.md`)과 Phase 요약이 다를 수 있다. 최종 구현 여부는 코드·스냅샷을 우선한다.

4. **`archive/completed-implementation/` 일괄 보관 (2026-05-06)**  
   `plans/`·`research/`에 있던 대부분의 1:1 실행 플랜 쌍을 스템별 폴더로 옮겼다. 세부 규칙·예외 스템은 [`archive/completed-implementation/README.md`](archive/completed-implementation/README.md)를 본다.
