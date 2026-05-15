아래는 **위 13개 Sequence를 개발 관리용 체크리스트**로 바꾼 버전입니다.  
그대로 `documents/ai/checklist.md`나 `documents/plans/solver_v2_checklist.md`에 붙여도 됩니다.

---

# Solver v2 Development Checklist

## 0. 공통 금지 규칙

모든 Sequence에 공통 적용.

- [ ] v1 solver production logic을 수정하지 않는다.
  - // PR·리뷰 수동(자동 링크 없음). 브랜치에서 `asteroid_mining_layout`(v1 패키지명) diff 미포함 확인.
- [ ] v1 코드를 삭제하지 않는다.
  - // 저장소 정책 수동.
- [x] v2에서 v1 solver internals를 import하지 않는다. (확인) [`test_import_boundaries.py` L41–L47](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - // v2 소스 줄에 `django_apps.shapez_asteroid.services.asteroid_mining_layout.` 참조 금지 스캔.
- [x] NDJSON / replay_events / solver_summary / debug log를 algorithm input으로 사용하지 않는다. (확인) [`snapshots.py` L24–L31](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py)
  - // `read_ndjson_replay_events`는 `NotImplementedError` 스켈레톤; 알고리즘 경로에서 호출 금지는 import 경계 테스트로 보조.
- [x] replay / trace는 output-only로 유지한다. (확인) [`test_import_boundaries.py` L50–L59](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - // `placement`/`routing`/`validation`이 import 줄에 `replay` 포함 금지.
- [x] belt와 pipe를 같은 transport graph로 섞지 않는다. (확인)
  - [`domain/enums.py` L12–L16](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - [`placement/bundle_candidate.py` L30–L35](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/bundle_candidate.py)
  - // `TransportKind` + `infer_transport_kind`.
- [ ] canonical document가 기존 코드보다 우선한다.
  - // 문서·리뷰 게이트 수동.
- [x] 미구현 로직은 fake success를 반환하지 않고 `NotImplementedError` 또는 명시적 실패로 처리한다. (확인)
  - [`routing/trunk_seed.py` L14–L17](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py)
  - [`routing/merge_aware_router.py` L19–L22](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py)
  - [`solver.py` L48–L51](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py)
- [ ] 각 Sequence 종료 시 pytest / ruff / black 결과를 기록한다.
  - // Sequence 01 기록: 아래 **기록 (2026-05-14)** 절 참고.


**§0 규칙 ↔ 코드·테스트 근거 (2026-05-14 스냅샷)**  
아래는 PR 수동 항목을 제외하고, **저장소 안에서 추적 가능한 확인 코드**만 적는다. 링크는 Cursor에서 `mdc:`로 연다. **주의:** 한 줄에 `](mdc:...)` 링크를 여러 개 나열하면 에디터가 URI를 잘라 `Unable to resolve resource`(예: `trace_sema…`)가 날 수 있으니, **표에서는 `<br>`로 링크를 줄 바꿈**하거나 **목록에서는 들여쓴 줄에 링크 1개**씩 둔다.

| 규칙 요약 | 확인 코드 | 라인 | 코멘트 |
|-----------|-----------|------|--------|
| v2가 v1 `asteroid_mining_layout` 패키지를 참조하지 않음 | [test_import_boundaries.py](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) | L9–L47, L86–L109 | 소스 줄 스캔 + `solver.py` AST |
| placement/routing/validation이 replay 패키지 import 안 함 | 위 파일 `test_placement_routing_validation_do_not_import_replay` | L50–L59 | import 줄에 `\breplay\b` 탐지 |
| validation이 STEP4 라우트 생성 모듈명을 끌고 오지 않음 | 위 파일 `test_validation_does_not_import_merge_aware_router` | L62–L66 | `validation/` 트리 텍스트 검사 |
| v2 트리에 `django` / `django.*` import 없음 | 위 파일 `test_v2_tree_has_no_django_imports` | L69–L83 | AST 전수 |
| subprocess에서 domain enum import 시 Django 미적재 | 위 파일 `test_v2_domain_imports_without_django_in_subprocess` | L112–L133 | DB 사이드 이펙트 스모크 |
| NDJSON reader는 알고리즘 입력이 아님 | [snapshots.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py) `read_ndjson_replay_events` | L24–L31 | `NotImplementedError` 스켈레톤 |
| 미구현은 가짜 성공 대신 예외 | [trunk_seed.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py) `build_trunk_seed_candidates` | L14–L17 | 동일 패턴:<br>[merge_aware_router.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py) L19–L22<br>[solver.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py) L48–L51 |

---

# 1. Sequence 01 — v2 Namespace Skeleton

## 목표

v1과 독립된 `asteroid_mining_layout_v2` 패키지 골격 생성.

## 생성 파일

- [x] `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/__init__.py` (확인) [`L1–L12`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/__init__.py)
  - // v2 패키지 docstring·`__version__`·Django 비의존 선언.
- [x] `domain/__init__.py` (확인) [`L1–약128`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/__init__.py)
  - // coord·dto·enum·FSM 재export(placement_fsm은 placement로 위임).
- [x] `domain/coord.py` (확인) [`coord.py` 전체](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/coord.py)
  - // `Coord`·`BBox`·blueprint 셀 타입.
- [x] `domain/enums.py` (확인) [`L12–약128`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - // `TransportKind`·`PlacementCommitState`·`RouteZone` 등 CANON enum.
- [x] `domain/dto.py` (확인) [`L1–약345`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
  - // `SolverRunContext`·Pass 결과·`TraceEvent`(+ `__post_init__` trace 검증).
- [x] `domain/grid.py` (확인) [`grid.py` 전체](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/grid.py)
  - // 그리드 마스크 보조.
- [x] `decode/__init__.py` (확인) [`decode/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/__init__.py)
  - // `analyze_decoded_layout`·`decode_copy_payload` 공개.
- [x] `decode/copy_decode_adapter.py` (확인) [`L1–약40`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/copy_decode_adapter.py)
  - // `shapez_core` 디코드 위임, v1 미참조.
- [x] `decode/existing_layout_analysis.py` (확인) [`L84–L138` 등](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py)
  - // STEP 0.5 `analyze_decoded_layout`.
- [x] `reconstruction/__init__.py` (확인) [`reconstruction/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/__init__.py)
  - // `reconstruct_asteroid_mining_field` export.
- [x] `reconstruction/asteroid_reconstruction.py` (확인) [`L97–L188`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py)
  - // STEP 1 본체.
- [x] `placement/__init__.py` (확인) [`placement/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/__init__.py)
  - // Pass1/Pass2 심볼 export.
- [x] `placement/bundle_candidate.py` (확인) [`L30–L111` 대역](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/bundle_candidate.py)
  - // 후보·`infer_transport_kind`.
- [x] `placement/placement_fsm.py` (확인) [`L21–약121`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - // §9.6 FSM·provisional merge.
- [x] `placement/pass1_outer.py` (확인) [`L228–약325`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py)
  - // `run_pass1_outer_placement`.
- [x] `placement/pass2_internal.py` / `placement/pass2_bundle_optimizer.py` (확인) [`pass2_internal.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py) · [`pass2_bundle_optimizer.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_bundle_optimizer.py)
  - // `run_pass2_internal_fill` + CP-SAT/optional greedy 번들 패킹.
- [x] `routing/__init__.py` (확인) [`routing/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/__init__.py)
  - // STEP4 패키지 docstring.
- [x] `routing/trunk_seed.py` (확인) [`L14–L17`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py)
  - // 스켈레톤 `NotImplementedError`(본구현은 Phase 4).
- [x] `routing/connectivity.py` (확인) [`전체`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/connectivity.py)
  - // 읽기 전용 flood fill·validation 허용.
- [x] `routing/merge_aware_router.py` (확인) [`L19–L22`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py)
  - // 스켈레톤 `NotImplementedError`.
- [x] `validation/__init__.py` (확인) [`validation/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/__init__.py)
  - // STEP9 패키지 설명(merge-aware import 금지 문구).
- [x] `validation/final_validation.py` (확인) [`L20–L57`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py)
  - // `validate_final_layout_stub` + `connectivity`만 사용.
- [x] `replay/__init__.py` (확인) [`replay/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/__init__.py)
- [x] `replay/trace_event.py` (확인) [`L13–L21`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/trace_event.py)
  - // 출력용 `TraceEvent` dataclass.
- [x] `replay/snapshots.py` (확인) [`L15–L31`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py)
  - // `read_ndjson_replay_events` NIE 스켈레톤.
- [x] `solver.py` (확인) [`L25–L51`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py)
  - // copy-preview sidecar + `solve_mining_layout_v2_stub` NIE.


## 테스트 파일

- [x] `tests/unit/shapez_asteroid_v2/test_import_boundaries.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - // v1 문자열·replay import·Django AST·solver AST·subprocess enum 스모크.
- [x] `tests/unit/shapez_asteroid_v2/test_domain_enums.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_domain_enums.py)
  - // `TransportKind` 문자열 안정성.
- [x] `tests/unit/shapez_asteroid_v2/test_placement_fsm.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_placement_fsm.py)
  - // §9.6 전이·`apply_pass*_provisional_commits`.
- [x] `tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py)
  - // `domain.dto.TraceEvent`·`trace_semantics` (§16.3·§13.5).
- [x] `tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py)
  - // 빈 BP → `RAW_ASTEROID_FIELD`·입력 비변형.
- [x] `tests/unit/shapez_asteroid_v2/test_reconstruction_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_reconstruction_contract.py)
  - // 빈 reconstruction·`None` context.
- [x] `tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py)
  - // Pass1/2 commit이 `PROVISIONAL_PLACED`만.
- [x] `tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py)
  - // trunk seed NIE.
- [x] `tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py)
  - // merge-aware router NIE.
- [x] `tests/unit/shapez_asteroid_v2/test_final_validation_contract.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_final_validation_contract.py)
  - // quarantine·빈 transport 스텁 동작.
- [x] `tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py` (확인) [`전체`](mdc:tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py)
  - // NDJSON reader NIE·replay `TraceEvent` 생성.


## 완료 조건

- [x] v2 package import 성공 (확인) [`pytest` `tests/unit/shapez_asteroid_v2`](mdc:tests/unit/shapez_asteroid_v2) — 2026-05-14 스냅샷 76 passed
  - // 전체 v2 단위 테스트 수집·실행.
- [x] v2 modules가 v1 solver internals를 import하지 않음 (확인) [`test_import_boundaries.py` L41–L47](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
- [x] placement/routing/validation이 replay NDJSON reader를 import하지 않음 (확인) [`L50–L59`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
- [x] validation이 route creation function을 직접 import하지 않음 (확인)
  - [`test_import_boundaries.py` L62–L66](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - [`validation/final_validation.py` L15–L17](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py) (`connectivity`만)
- [x] solver.py가 v1 solver internals를 import하지 않음 (확인) [`test_import_boundaries.py` `test_solver_py_does_not_import_v1_layout_package`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
- [x] v2 package import 시 Django DB access 없음 (확인)
  - [`test_import_boundaries.py` L69–L83](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) (Django AST 금지)
  - [`test_import_boundaries.py` L112–L133](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) (subprocess 스모크)
- [x] 비어 있는 구현은 fake success 대신 NotImplementedError 사용 (확인)
  - [`routing/trunk_seed.py` L14–L17](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py)
  - [`routing/merge_aware_router.py` L19–L22](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py)
  - [`replay/snapshots.py` L24–L31](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py)


## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m pytest tests/unit/shapez_asteroid_v2/test_domain_enums.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

**기록 (2026-05-14, Sequence 01 마감):** `python -m pytest tests/unit/shapez_asteroid_v2` 35 passed, `ruff check …/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2` 통과, `black --check` 동일 경로 통과.  
**갱신 (2026-05-14, Sequence 02 trace·enum 보강 후):** 동일 경로 `pytest` **76 passed**.

---

# 2. Sequence 02 — Domain DTO / Enum / FSM

## 목표

v2의 semantic enum, DTO, PlacementCommitState FSM 고정.

## 구현 대상

- [x] `domain/coord.py` (확인) [`coord.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/coord.py)
- [x] `domain/enums.py` — `ROUTE_ZONE_PASS3_BASE_COST`·`TRANSPORT_KIND_ROUTE_ZONE_MULTIPLIER` (§11.1–11.2; STEP 4 Dijkstra와 분리) (확인) [`enums.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `domain/dto.py` (확인) [`dto.py` L37–약340](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `domain/grid.py` (확인) [`grid.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/grid.py)
- [x] `placement/placement_fsm.py` (확인) [`placement_fsm.py` L21–약121](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - // `_ALLOWED` 전이표·provisional merge.


## Enum 체크리스트

- [x] `TransportKind.SHAPE_BELT = "shape_belt"` (확인) [`enums.py` L15–L16](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - // `test_domain_enums.py` 문자열 고정.
- [x] `TransportKind.FLUID_PIPE = "fluid_pipe"` (확인) [`enums.py` L16](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - // belt/pipe 분리.

- [x] `PlacementCommitState.PROVISIONAL_PLACED` (확인) [`enums.py` L22–L23](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `PlacementCommitState.ROUTED_CONFIRMED` (확인) [`enums.py` L23](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `PlacementCommitState.QUARANTINED_UNROUTED` (확인) [`enums.py` L24](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `PlacementCommitState.ROLLED_BACK` (확인) [`enums.py` L25](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)

- [x] `RouteZone.OUTSIDE` (확인) [`enums.py` L31](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RouteZone.BOUNDARY_VOID` (확인) [`enums.py` L32](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RouteZone.INTERNAL_VOID` (확인) [`enums.py` L33](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - // CANON §11.1 zone; STEP4 Dijkstra 비용과 혼용 금지는 Sequence 02 완료조건·docstring에서 반복 명시.
- [x] `RouteZone.FILLABLE_INTERIOR` (확인) [`enums.py` L34](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RouteZone.PLACEMENT_CANDIDATE` (확인) [`enums.py` L35](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RouteZone.PLACEMENT_OCCUPIED` (확인) [`enums.py` L36](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RouteZone.BLOCKED` (확인) [`enums.py` L37](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)

- [x] `SolverTerminationTier.SUCCESS` (확인) [`enums.py` L43](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `SolverTerminationTier.PARTIAL_SUCCESS` (확인) [`enums.py` L44](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `SolverTerminationTier.SOLVER_FAILURE` (확인) [`enums.py` L45](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)


## Recovery / Commit Semantic 체크리스트

- [x] `RecoveryTrigger.STEP4_ROUTING_FAILURE` (확인) [`enums.py` L55](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RecoveryTrigger.STEP4_CAPACITY_FAILURE` (확인) [`enums.py` L56](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RecoveryTrigger.PASS3_CONNECTIVITY_BREAK` (확인) [`enums.py` L57](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RecoveryTrigger.POST_RECLAIM_PASS3_CONNECTIVITY_BREAK` (확인) [`enums.py` L58](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RecoveryTrigger.RECLAIM_INCREMENTAL_FAILURE` (확인) [`enums.py` L59](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `RecoveryTrigger.FINAL_VALIDATION_FAILURE` (확인) [`enums.py` L60](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)

- [x] `CommitReason.NORMAL_GAIN` (확인) [`enums.py` L66](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `CommitReason.DEGRADED_CONNECTED_RECOVERY` (확인) [`enums.py` L67](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)

- [x] `rejected_by_no_replacement_route`는 `CommitReason`으로 분류되지 않음 (확인)
  - [`domain/trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) (`_FORBIDDEN_COMMIT_STRINGS`)
  - // `RejectedReason` 정의: [`domain/enums.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
- [x] `post_reclaim_pass3_connectivity_break`는 `CommitReason`으로 분류되지 않음 (확인) [`trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py)
- [x] `recovery_trigger` 값은 `commit_reason`으로 사용 불가 (확인) [`trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py)


## DTO 체크리스트

- [x] `Coord` (확인) [`coord.py` L16–L24](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/coord.py)
- [x] `BBox` (확인) [`coord.py` L27–L34](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/coord.py)
- [x] `GridMask` (immutable cell set wrapper) (확인) [`dto.py` L37–L46](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `PlacementId` (확인) [`dto.py` L34](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `ExtractorPlacement` (확인) [`dto.py` L228–L232](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `ExtensionPlacement` (확인) [`dto.py` L235–L240](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `OutputStub` (확인) [`dto.py` L219–L225](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `PlacementBundle` (확인) [`dto.py` L243–L247](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `RoutePath` (확인) [`dto.py` L250–L255](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `RoutingFailure` (확인) [`dto.py` L258–L267](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `TrunkLoadSummary` (확인) [`dto.py` L270–L275](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `SolverRunContext` (확인) [`dto.py` L204–L215](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `Pass1Result` (확인) [`dto.py` L278–L285](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `Pass2Result` (확인) [`dto.py` L288–L295](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `Step4RoutingResult` (확인) [`dto.py` L298–L304](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `FinalValidationReport` (확인) [`dto.py` L307–L313](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
- [x] `TraceEvent` (확인) [`domain/dto.py` — `TraceEvent`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
  - // `__post_init__`에서 `trace_semantics.validate_trace_decision_semantics`·`validate_route_level_trace_transport` 호출.


## FSM 체크리스트

- [x] `PROVISIONAL_PLACED` → `ROUTED_CONFIRMED` 허용 (확인)
  - [`placement/placement_fsm.py` `_ALLOWED` L21–L37](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - [`test_placement_fsm.py`](mdc:tests/unit/shapez_asteroid_v2/test_placement_fsm.py)
- [x] `PROVISIONAL_PLACED` → `QUARANTINED_UNROUTED` 허용 (확인) 동일 `_ALLOWED`
- [x] `PROVISIONAL_PLACED` → `ROLLED_BACK` 허용 (확인) 동일 `_ALLOWED`
- [x] `QUARANTINED_UNROUTED` → `ROUTED_CONFIRMED` 허용 (확인) 동일 `_ALLOWED`
- [x] `QUARANTINED_UNROUTED` → `ROLLED_BACK` 허용 (확인) 동일 `_ALLOWED`
- [x] `ROLLED_BACK` 이후 transition 금지 (확인)
  - [`placement/placement_fsm.py` L63–L67](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - // `test_rolled_back_cannot_leave`
- [x] `ROUTED_CONFIRMED` 이후 placement-state transition 금지 (확인)
  - [`placement/placement_fsm.py` L63–L67](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - // `test_routed_confirmed_cannot_regress`


## 완료 조건

- [x] `committed=false` 이벤트에 `commit_reason` 사용 시 실패 (확인) [`trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) · [`test_trace_semantic_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py)
- [x] `committed=true` 이벤트에 유효 `commit_reason` 없으면 실패 (확인) [`trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) · [`test_trace_semantic_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py)
- [x] `RecoveryTrigger` 값이 `CommitReason`으로 들어오면 실패 (확인) [`trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) · [`test_trace_semantic_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py)
- [x] `route_level=true`인 `TraceEvent`에 `transport_kind=batch_mixed` 금지 (§16.3) (확인) [`trace_semantics.validate_route_level_trace_transport`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) · [`test_trace_semantic_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py)
- [x] `TransportKind` belt/pipe 완전 분리 (확인)
  - [`domain/enums.py` L12–L16](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - [`test_domain_enums.py`](mdc:tests/unit/shapez_asteroid_v2/test_domain_enums.py)
- [x] `RouteZone` cost table은 STEP4 Dijkstra cost와 혼합하지 않음 (확인)
  - [`domain/enums.py` `ROUTE_ZONE_PASS3_BASE_COST`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py) · [`domain/grid.py` 모듈 docstring](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/grid.py)
- [x] DTO는 가능한 immutable (확인)
  - [`domain/dto.py` dataclass frozen/slots](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)


## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_domain_enums.py
python -m pytest tests/unit/shapez_asteroid_v2/test_placement_fsm.py
python -m pytest tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 3. Sequence 03 — STEP 0 / 0.5 Decode + ExistingLayoutAnalysis

## 목표

copy decode adapter와 read-only ExistingLayoutAnalysis 구현.

## 구현 대상

```md
- [x] decode/copy_decode_adapter.py
- [x] decode/existing_layout_analysis.py
- [x] domain/dto.py 필요 DTO 추가
- [x] domain/enums.py 필요 enum 추가

```

**확인 (코드·라인·코멘트)**  
- [`decode/copy_decode_adapter.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/copy_decode_adapter.py) L1–L40: `shapez_core` 래퍼, v1 미참조.  
- [`decode/existing_layout_analysis.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py) L84–L138: `analyze_decoded_layout` 본문.  
- [`domain/dto.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py) L172–L193 등: `ExistingLayout*` / `DecodedExistingLayoutContext`.  
- [`domain/enums.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py) L86–L93: `SourceKind` 등 STEP 0.5 enum.

## Decode 체크리스트

```md
- [x] `SHAPEZ2-4-` prefix 처리
- [x] Base64 decode
- [x] gzip decompress
- [x] JSON parse
- [x] normalized decoded blueprint DTO 반환
- [x] decode adapter가 placement/routing/validation에 의존하지 않음

```

## ExistingLayoutAnalysis DTO 체크리스트

```md
- [x] SourceKind.raw_asteroid_field
- [x] SourceKind.existing_fluid_layout
- [x] SourceKind.existing_shape_layout
- [x] SourceKind.mixed_existing_layout
- [x] SourceKind.unknown

- [x] ExistingLayoutAnalysis
- [x] ExistingTransportAnalysis
- [x] TransportComponentSummary
- [x] ExistingEquipmentAnalysis
- [x] EquipmentTransportAttachment
- [x] ExistingLayoutIssue
- [x] ExistingLayoutSolverHints
- [x] DecodedExistingLayoutContext

```

## 분석 로직 체크리스트

```md
- [x] ExistingLayoutAnalysis는 read-only context
- [x] blueprint / placement를 mutate하지 않음
- [x] mineable_placement_cells를 생성하지 않음
- [x] reconstruction을 대체하지 않음
- [x] 같은 TransportKind끼리만 connected component 분석
- [x] belt와 pipe component를 섞지 않음
- [x] main_trunk_candidate만 trunk_seed_cell_union hint 생성 가능
- [x] orphan_component는 cleanup_candidate_cell_union으로 분류
- [x] single_cell_artifact는 cleanup candidate로 분류
- [x] existing pipe/belt를 자동 hard_protected 처리하지 않음
- [x] existing_layout_* field와 final_validation_* field 분리

```

## 테스트 체크리스트

```md
- [x] raw asteroid input은 existing layout으로 오분류되지 않음
- [x] existing fluid miner + SpacePipe layout source kind 분류
- [x] connected main component가 trunk seed hint 생성
- [x] orphan component는 trunk seed에서 제외
- [x] single cell artifact는 cleanup candidate
- [x] ExistingLayoutAnalysis가 mineable_placement_cells로 사용되지 않음
- [x] existing_layout_* report field와 final_validation_* field 분리
- [x] belt / pipe component analysis 분리

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 4. Sequence 04 — STEP 1 Asteroid Reconstruction

## 목표

decoded blueprint에서 asteroid shell / barrier / mineable placement cells 재구성.

## 구현 대상

```md
- [x] reconstruction/asteroid_reconstruction.py
- [x] domain/dto.py 필요 DTO 추가

```

**확인 (코드·라인·코멘트)**  
- [`reconstruction/asteroid_reconstruction.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py) L97–L188: `reconstruct_asteroid_mining_field` (STEP1).  
- [`domain/dto.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py) L58–L71: `ReconstructionDTO` 필드.

## ReconstructionResult 체크리스트

```md
- [x] full_barrier_cells
- [x] extraction_shell_cells
- [x] belt_cells
- [x] pipe_cells
- [x] extractor_cells
- [x] extension_cells
- [x] interior_patch_cells
- [x] mineable_placement_cells
- [x] asteroid bbox
- [x] external margin metadata
- [x] external_margin_bbox_source

```

## 알고리즘 체크리스트

```md
- [x] asteroid shell cells 수집
- [x] belt / pipe / extractor / extension / asteroid shell 분리
- [x] existing buildings와 hard obstacles로 full_barrier_cells 구성
- [x] outside flood fill 실행
- [x] Chebyshev 8-neighbor closing 적용
- [x] interior mineable patch는 reconstruction에서만 추론
- [x] ExistingLayoutAnalysis는 hint로만 사용
- [x] orphan pipe/belt component를 asteroid shell로 취급하지 않음
- [x] existing island layout을 raw asteroid field로 취급하지 않음

```

## 테스트 체크리스트

```md
- [x] belt_cells와 pipe_cells 분리
- [x] existing layout context가 mineable_placement_cells를 대체하지 않음
- [x] orphan transport cells가 extraction_shell_cells로 들어가지 않음
- [x] interior patch inference가 reconstruction에서만 발생
- [x] 작은 perimeter gap leakage가 closing으로 방지됨
- [x] reconstruction result deterministic
- [x] external_margin_bbox_source deterministic
- [x] raw asteroid / existing layout source 비혼합

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_reconstruction_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 5. Sequence 05 — STEP 2 Pass1 Outer-First Placement

## 목표

외곽 우선 Pass1 배치.  
단, 최종 routing은 하지 않는다.

## 구현 대상

```md
- [x] placement/bundle_candidate.py
- [x] placement/pass1_outer.py
- [x] placement/placement_fsm.py 필요 보강
- [x] domain/dto.py 필요 DTO 추가

```

**확인 (코드·라인·코멘트)**  
- [`placement/bundle_candidate.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/bundle_candidate.py) L30–L35: `infer_transport_kind` belt/pipe 분기.  
- [`placement/pass1_outer.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py) L228–L325: `run_pass1_outer_placement`.  
- [`placement/placement_fsm.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py) L21–L121: §9.6 FSM + provisional merge.

## Pass1 체크리스트

```md
- [x] asteroid outer perimeter부터 inward scan
- [x] deterministic scan order 사용
- [x] output direction 후보 평가
- [x] extractor마다 exactly one output stub 생성
- [x] extension 후보는 output direction 제외 3방향
- [x] extension-to-extension chain / branching 지원
- [x] extractor당 max 3 extensions
- [x] extension orientation은 parent를 향함
- [x] cheap escape는 feasibility / score로만 사용
- [x] cheap escape path를 occupied transport로 기록하지 않음
- [x] final route cells 생성하지 않음
- [x] accepted bundle state는 PROVISIONAL_PLACED
- [x] placement_pass="pass1"
- [x] TransportKind 분리

```

## Candidate 필드 체크리스트

```md
- [x] placement_id 또는 candidate_id
- [x] extractor coord
- [x] output direction
- [x] output stub coord
- [x] extension coords
- [x] extension parent relation
- [x] extension orientation
- [x] transport kind
- [x] scan index
- [x] score
- [x] reject_reason

```

## 테스트 체크리스트

```md
- [x] output direction마다 output stub exactly one
- [x] extension candidates가 output direction 제외
- [x] max 3 extensions
- [x] extension orientation points to parent
- [x] extension-to-extension branching 지원
- [x] cheap escape path가 occupied_cells에 없음
- [x] cheap escape path가 final_route_cells에 없음
- [x] accepted bundle은 PROVISIONAL_PLACED
- [x] STEP4 전 ROUTED_CONFIRMED 없음
- [x] deterministic scan order
- [x] belt / pipe TransportKind 분리
- [x] Pass1이 final routing commit code를 import하지 않음

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_placement_fsm.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 6. Sequence 06 — STEP 3 Pass2 Internal Fill Placement

## 목표

Pass1 이후 남은 내부 mineable cells에 provisional placement.

## 구현 대상

```md
- [ ] placement/pass2_internal.py
- [ ] placement/bundle_candidate.py 필요 보강
- [ ] domain/dto.py 필요 DTO 추가

```

## Pass2 체크리스트

```md
- [ ] Pass1 이후 남은 mineable cells 사용
- [ ] Pass1 extractor cells blocked
- [ ] Pass1 extension cells blocked
- [ ] Pass1 output stub cells blocked
- [ ] hard barrier cells blocked
- [ ] preserve 대상 existing structures blocked
- [ ] STEP4 final routes를 참조하지 않음
- [ ] Pass3 rerouted cells를 참조하지 않음
- [ ] cheap escape path를 occupied 처리하지 않음
- [ ] accepted bundle은 PROVISIONAL_PLACED
- [ ] isolated extractor with no plausible escape 거부 또는 낮은 우선순위
- [ ] placement_pass="pass2"
- [ ] TransportKind 분리
- [ ] ordinary Pass2에서 reclaim route-overlap rule 미적용
- [ ] Pass2 feasible ``Pass2BundleCandidate`` 풀을 먼저 수집한 뒤 전역적으로 겹침 없는 부분집합을 선택한다 (``pass2_internal`` + ``pass2_bundle_optimizer``).
- [ ] 번들 패킹은 ``extractor_cell``·``output_stub_cell``·extension 타일 셀 기준 set packing이며, OR-Tools CP-SAT는 **선택**이며 미설치 시 결정적 greedy fallback으로 동작한다.
- [ ] ``pass2_bundle_optimizer``는 STEP4 라우팅·``final_route_cells``·``ROUTED_CONFIRMED``·replay NDJSON 입력을 사용하지 않는다.

```

### Pass2 번들 패킹 옵티마이저 (CP-SAT / fallback)

- [x] `placement/pass2_bundle_optimizer.py` — CP-SAT(optional)·greedy fallback·``Pass2PackingInput``/``Pass2PackingResult`` (확인) [`pass2_bundle_optimizer.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_bundle_optimizer.py)
- [x] `run_pass2_internal_fill` — 풀 수집 후 ``optimize_pass2_bundle_packing`` 연결·beam ``pass2_optimizer_selected`` / ``pass2_optimizer_summary`` (확인) [`pass2_internal.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py)
- [x] 계약 테스트 (확인) [`test_pass2_bundle_optimizer_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_pass2_bundle_optimizer_contract.py)


## 테스트 체크리스트

```md
- [ ] Pass2는 Pass1 extractor 위에 배치하지 않음
- [ ] Pass2는 Pass1 extension 위에 배치하지 않음
- [ ] Pass2는 Pass1 output stub 위에 배치하지 않음
- [ ] hard barrier 위 배치 금지
- [ ] cheap escape path가 occupied_cells에 없음
- [ ] Pass2는 final_route_cells를 참조하지 않음
- [ ] accepted Pass2 bundle은 PROVISIONAL_PLACED
- [ ] STEP4 전 ROUTED_CONFIRMED 없음
- [ ] ordinary Pass2에서 route overlap logic 미적용
- [ ] Pass2 번들 패킹 옵티마이저가 ``merge_aware_router`` / ``trunk_seed`` / replay import를 끌지 않음
- [ ] deterministic candidate ordering
- [ ] isolated extractor no plausible escape 처리
- [ ] belt / pipe TransportKind 분리

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_placement_fsm.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 7. Sequence 07 — STEP4 Trunk Seed / Goal Set

## 목표

STEP4 routing 전에 trunk seed와 route goal set을 정본 기준으로 구성.

## 구현 대상

```md
- [ ] routing/trunk_seed.py
- [ ] routing/connectivity.py 필요 helper
- [ ] domain/dto.py 필요 DTO 추가

```

## Trunk Seed 체크리스트

```md
- [ ] TransportKind별 trunk_seed_candidates 생성
- [ ] exterior margin adjacent / outside candidate exit cells 포함
- [ ] output이 접근 가능한 boundary ring cells 포함
- [ ] ExistingLayoutAnalysis의 preserved existing trunk cells 반영
- [ ] existing trunk 반영 조건: same TransportKind
- [ ] existing trunk 반영 조건: component status == main_trunk_candidate
- [ ] existing trunk 반영 조건: policy allows trunk candidate
- [ ] orphan_component는 trunk seed 제외
- [ ] single_cell_artifact는 trunk seed 제외
- [ ] cheap escape path는 trunk seed 제외
- [ ] shape_belt와 fluid_pipe trunk seed 분리

```

## Goal Set 체크리스트

```md
- [ ] 첫 route 전: exterior margin cells ∪ trunk_seed_candidates
- [ ] route commit 후: existing trunk cells ∪ exterior margin cells
- [ ] 첫 route 실패 시 existing trunk 승격 없음
- [ ] goal source count metadata 기록

```

## 테스트 체크리스트

```md
- [ ] main existing component가 trunk seed candidate가 됨
- [ ] orphan component는 trunk seed 제외
- [ ] single cell artifact는 trunk seed 제외
- [ ] cheap escape path 제외
- [ ] first route goal set = exterior margin ∪ trunk_seed_candidates
- [ ] after commit goal set = existing trunk ∪ exterior margin
- [ ] first failed route does not promote existing trunk
- [ ] belt route cannot use pipe trunk seed
- [ ] pipe route cannot use belt trunk seed
- [ ] external margin deterministic
- [ ] source metadata records goal source counts

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 8. Sequence 08 — STEP4 Merge-Aware Router MVP

## 목표

고정 output stub에서 trunk/exterior까지 merge-aware route commit.

## 구현 대상

```md
- [ ] routing/merge_aware_router.py
- [ ] routing/connectivity.py
- [ ] domain/dto.py 필요 DTO 추가

```

## Routing 체크리스트

```md
- [ ] input은 PROVISIONAL_PLACED Pass1/Pass2 bundles
- [ ] routing priority deterministic
- [ ] route start = fixed output stub
- [ ] route start가 extractor core가 아님
- [ ] goal set은 Sequence 07 builder 사용
- [ ] geometry valid일 때만 commit
- [ ] output stub connected일 때만 commit
- [ ] target trunk 또는 exterior connected일 때만 commit
- [ ] TransportKind match일 때만 commit
- [ ] trunk_load aggregate update
- [ ] rated/max capacity comparison은 MVP에서 미적용
- [ ] 성공 시 ROUTED_CONFIRMED
- [ ] route cells가 final_route_cells / existing trunk에 편입
- [ ] 실패 시 QUARANTINED_UNROUTED 또는 ROLLED_BACK
- [ ] failure row에 stub_cell 기록
- [ ] failure row에 extractor_id 기록
- [ ] failure row에 attempt_count 기록
- [ ] failure row에 final_state 기록
- [ ] failure row에 last_error 기록
- [ ] stub already external reachable trunk이면 path=[stub] no-op commit 허용

```

## 금지 체크리스트

```md
- [ ] Pass3 route cost model 사용 안 함
- [ ] Reclaim incremental routing 사용 안 함
- [ ] Recovery branch 사용 안 함
- [ ] final validation repair 사용 안 함
- [ ] NDJSON/log read 없음
- [ ] mixed transport kind trunk 없음
- [ ] capacity overflow enforcement 없음

```

## 테스트 체크리스트

```md
- [ ] route starts at fixed output stub
- [ ] success route -> ROUTED_CONFIRMED
- [ ] failed route -> QUARANTINED_UNROUTED 또는 ROLLED_BACK
- [ ] first route can target exterior margin / trunk seed
- [ ] later route can merge into committed existing trunk
- [ ] no-op route commit works when stub already external reachable trunk
- [ ] trunk_load aggregate recorded
- [ ] max capacity not enforced
- [ ] belt route rejects pipe goal
- [ ] pipe route rejects belt goal
- [ ] routing failure row required fields 존재
- [ ] no ROUTED_CONFIRMED without route commit
- [ ] final_route_cells separated by TransportKind

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_placement_fsm.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 9. Sequence 09 — STEP9 Final Validation MVP

## 목표

최종 검증은 assertion gate로만 동작.  
route 생성/수정 금지.

## 구현 대상

```md
- [ ] validation/final_validation.py
- [ ] routing/connectivity.py read-only helper

```

## Geometry Validation 체크리스트

```md
- [ ] extractor / extension overlap 없음
- [ ] extractor / extension이 belt / pipe와 overlap 없음
- [ ] belt / pipe가 extractor / extension과 overlap 없음
- [ ] every extractor has output stub
- [ ] fixed output stub removed 여부 검사
- [ ] QUARANTINED_UNROUTED placement 잔존 금지

```

## Connectivity Validation 체크리스트

```md
- [ ] every extractor output stub reaches external trunk/margin by same TransportKind
- [ ] all transport cells belong to external reachable area
- [ ] no orphan belt component
- [ ] no orphan pipe component
- [ ] external margin reachable trunk exists

```

## Capacity / Optimization 체크리스트

```md
- [ ] MVP에서는 rated/max capacity enforcement 미적용
- [ ] route가 있으면 trunk_load aggregate 존재 여부 검사
- [ ] capacity 미적용 상태를 report에 명시
- [ ] optimization validation은 not_evaluated 또는 warning
- [ ] optimization warning만으로 SOLVER_FAILURE 처리하지 않음

```

## Mutation 금지 체크리스트

```md
- [ ] final validation은 layout을 mutate하지 않음
- [ ] final validation은 route를 생성하지 않음
- [ ] final validation은 STEP4를 호출하지 않음
- [ ] FinalValidationReport만 생성

```

## 테스트 체크리스트

```md
- [ ] overlap fails validation
- [ ] missing output stub fails validation
- [ ] QUARANTINED_UNROUTED fails validation
- [ ] all stubs connected passes
- [ ] orphan transport component fails validation
- [ ] capacity max overflow not enforced in MVP
- [ ] trunk_load missing policy tested
- [ ] validation does not mutate input layout
- [ ] validation module cannot import route creation functions
- [ ] optimization warning alone does not produce SOLVER_FAILURE
- [ ] existing_layout_* and final_validation_* fields not mixed

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_final_validation_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 10. Sequence 10 — Replay / Trace Output Layer

## 목표

trace/replay를 output-only로 고정.

## 구현 대상

```md
- [ ] replay/trace_event.py
- [ ] replay/snapshots.py

```

## Trace 체크리스트

```md
- [ ] trace_event는 output only
- [ ] computation_cycle 기록 가능
- [ ] UI streaming policy는 every 10 computation cycles로 문서화
- [ ] NDJSON writer는 replay/debug/report module 아래에만 위치
- [ ] algorithm은 prior trace file을 읽지 않음
- [ ] committed=false event는 commit_reason 없음
- [ ] committed=true event는 valid CommitReason 필요
- [ ] recovery_trigger와 commit_reason 분리
- [ ] transport_kind = shape_belt / fluid_pipe / batch_mixed / none
- [ ] batch_mixed는 batch trace event 전용
- [ ] route-level event는 batch_mixed 금지

```

## Snapshot 체크리스트

```md
- [ ] original_decoded_map
- [ ] existing_layout_analysis
- [ ] reconstruction
- [ ] pass1
- [ ] pass2
- [ ] step4_routing_result
- [ ] validation
- [ ] final_layout

```

## API 체크리스트

```md
- [ ] make_trace_event(...)
- [ ] validate_trace_event_semantics(...)
- [ ] make_phase_snapshot(...)
- [ ] serialize_snapshot(...)
- [ ] optional write_ndjson_trace_event(...)

```

## 테스트 체크리스트

```md
- [ ] trace event semantic validation
- [ ] committed=false with commit_reason rejected
- [ ] committed=true without commit_reason rejected
- [ ] RecoveryTrigger rejected as CommitReason
- [ ] batch_mixed does not appear in route-level event
- [ ] snapshots serializable
- [ ] routing/placement/validation do not import NDJSON reader
- [ ] replay module does not affect routing decision
- [ ] computation_cycle preserved
- [ ] snapshot phase stable

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py
python -m pytest tests/unit/shapez_asteroid_v2/test_trace_semantic_contract.py
python -m pytest tests/unit/shapez_asteroid_v2/test_import_boundaries.py
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 11. Sequence 11 — v2 Solver Orchestrator MVP

## 목표

STEP 0 → STEP 9 → STEP 10까지 v2 MVP pipeline 연결.

## 구현 대상

```md
- [ ] solver.py

```

## Pipeline 체크리스트

```md
- [ ] STEP 0 decode
- [ ] STEP 0.5 ExistingLayoutAnalysis
- [ ] STEP 1 Reconstruction
- [ ] STEP 2 Pass1 placement
- [ ] STEP 3 Pass2 placement
- [ ] STEP 4 Merge-aware routing
- [ ] STEP 9 Final validation
- [ ] STEP 10 Minimal replay snapshots

```

## MVP 제외 범위

```md
- [ ] STEP 5 Pass3 제외
- [ ] STEP 6 Reclaim 제외
- [ ] STEP 7 post-reclaim Pass3 rerun 제외
- [ ] STEP 8 Recovery branch 제외
- [ ] protected corridor replacement 제외
- [ ] rated/max capacity overflow enforcement 제외

```

## Termination 체크리스트

```md
- [ ] final validation pass + hard issue 없음 => SUCCESS
- [ ] 일부 placement rollback 후 valid layout => PARTIAL_SUCCESS
- [ ] connected transport 생성 불가 => SOLVER_FAILURE
- [ ] QUARANTINED_UNROUTED는 final validation 전 제거 또는 실패
- [ ] final validation에서 STEP4 자동 re-entry 없음
- [ ] optimization warning alone은 SOLVER_FAILURE 아님

```

## Solver API 체크리스트

```md
- [ ] solve_asteroid_layout_v2(input_copy_or_blueprint, options=None)
- [ ] typed SolverResult 반환
- [ ] orchestration은 thin layer
- [ ] phase outputs는 explicit DTO
- [ ] NotImplementedError를 success로 숨기지 않음

```

## 테스트 체크리스트

```md
- [ ] tiny fixture one extractor route to exterior => SUCCESS
- [ ] unreachable Pass2 placement rollback/quarantine 처리
- [ ] final에 QUARANTINED_UNROUTED 잔존 없음
- [ ] mixed belt/pipe fixture에서 routing 분리
- [ ] final validation failure does not call STEP4 repair
- [ ] replay snapshots emitted for each phase
- [ ] solver never imports v1 solver internals
- [ ] optimization warning alone does not cause SOLVER_FAILURE

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 12. Sequence 12 — Feature Flag / Integration Adapter

## 목표

v1 default 유지하면서 v2 opt-in 가능하게 연결.

## 설정 체크리스트

```md
- [ ] SHAPEZ_ASTEROID_SOLVER_VERSION = "v1" | "v2"
- [ ] default는 v1
- [ ] invalid setting은 clear error

```

## Integration 체크리스트

```md
- [ ] current application entrypoint 검색
- [ ] build_solver_timeline 관련 entrypoint 확인
- [ ] asteroid_mining_layout solver entry 확인
- [ ] optimize API 확인
- [ ] copy-preview API 확인
- [ ] 가장 얇은 boundary에 adapter 추가
- [ ] v1 path unchanged
- [ ] v2 path는 asteroid_mining_layout_v2.solver만 호출
- [ ] shared mutable global state 없음
- [ ] adapter level에서만 version choice log
- [ ] UI contract 불필요 변경 없음

```

## 테스트 체크리스트

```md
- [ ] setting v1 calls existing solver adapter
- [ ] setting v2 calls v2 solver
- [ ] invalid setting raises clear error
- [ ] v2 import does not import v1 internals
- [ ] v1 behavior unchanged by v2 package import
- [ ] default setting remains v1
- [ ] adapter logs version choice without algorithm leakage

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2
python -m pytest relevant existing shapez_asteroid adapter/API tests
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 13. Sequence 13 — v2 MVP Cross-Check Report

## 목표

코드-문서-테스트 교차 검증 보고서 작성.

## 보고서 경로

```md
- [ ] documents/reports/2026-05/solver_v2_mvp_cross_check.md

```

## Audit 체크리스트

### 13.1 v2 Isolation

```md
- [ ] no v1 solver internal imports
- [ ] no replay/NDJSON read path in algorithm modules
- [ ] v2 package imports without Django DB side effects

```

### 13.2 DTO / Enum

```md
- [ ] TransportKind separated
- [ ] PlacementCommitState FSM correct
- [ ] commit_reason namespace separated
- [ ] recovery_trigger is not commit_reason

```

### 13.3 Decode / ExistingLayoutAnalysis

```md
- [ ] read-only context
- [ ] does not define mineable cells
- [ ] existing_layout_* fields separate from final_validation_* fields

```

### 13.4 Reconstruction

```md
- [ ] mineable_placement_cells generated only in reconstruction
- [ ] orphan transport not used as asteroid shell
- [ ] flood fill / closing behavior tested

```

### 13.5 Pass1

```md
- [ ] output stub fixed
- [ ] cheap escape path not occupied
- [ ] PROVISIONAL_PLACED only
- [ ] extension topology supports three non-output directions

```

### 13.6 Pass2

```md
- [ ] blocks Pass1 extractor/extension/stub
- [ ] no final routes assumed
- [ ] PROVISIONAL_PLACED only
- [ ] cheap escape path not occupied

```

### 13.7 STEP4

```md
- [ ] fixed output stub is route start
- [ ] trunk seed and goal set separated
- [ ] route commit upgrades to ROUTED_CONFIRMED
- [ ] failure becomes QUARANTINED_UNROUTED or ROLLED_BACK
- [ ] trunk_load aggregate only
- [ ] belt/pipe separated

```

### 13.8 Final Validation

```md
- [ ] assertion only
- [ ] no new route creation
- [ ] no QUARANTINED_UNROUTED remains
- [ ] orphan transport rejected
- [ ] optimization warning alone does not fail hard

```

### 13.9 Replay

```md
- [ ] output only
- [ ] snapshots exist
- [ ] semantic trace guards active
- [ ] batch_mixed does not imply mixed trunk

```

### 13.10 MVP Non-Goals

```md
- [ ] no Pass3
- [ ] no Reclaim
- [ ] no Recovery
- [ ] no protected corridor replacement
- [ ] no rated capacity enforcement

```

## 보고서 섹션

```md
- [ ] Summary
- [ ] Canonical document alignment table
- [ ] Implemented scope
- [ ] Explicit non-goals
- [ ] Test results
- [ ] Known gaps
- [ ] Recommendation

```

## 검증 명령

```bash
python -m pytest tests/unit/shapez_asteroid_v2
python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2
python -m black --check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2

```

---

# 전체 진행판

> **체크 규칙:** `[x]` 항목의 **첫 줄**에 제목과 `(확인)`을 두고, `mdc:` 링크는 **들여쓴 줄에 하나씩**만 둔다(한 줄에 `mdc:`를 여러 개 두면 Cursor가 URI를 잘라 `Unable to resolve resource`가 날 수 있음). `//` 코멘트는 그 다음 들여쓴 줄에 적는다.

| Phase | 항목 | 상태 | 확인 코드 (경로·라인) | 코멘트 |
|-------|------|:----:|------------------------|--------|
| 0 | v1 freeze 기준 합의 | [ ] | — | 저장소 외 합의·릴리즈 노트(자동 링크 없음) |
| 0 | v2 namespace 생성 | [x] | [`asteroid_mining_layout_v2/__init__.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/__init__.py) L1–L11 | 패키지 docstring·`__version__` |
| 0 | import boundary test 생성 | [x] | [`test_import_boundaries.py`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) L9–L133 | `_REPO_ROOT`·v1 문자열·replay·Django AST·subprocess |
| 1 | DTO / enum / FSM 구현 | [x] | [`domain/dto.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py) L1–320대<br>[`domain/enums.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py) L12–<br>[`placement/placement_fsm.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py) L21–L121 | CANON DTO·enum·§9.6 FSM |
| 1 | semantic namespace guard 구현 | [ ] | [`test_import_boundaries.py`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) L20–L47 | **부분:** v1 패키지 문자열만 차단. 전용 semantic guard 모듈은 미도입 |
| 1 | trace semantic guard 구현 | [x] | [`domain/trace_semantics.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py) L25–L66<br>[`domain/dto.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py) TraceEvent.__post_init__ L330–L340 | NDJSON 없이 in-memory 검증 |
| 2 | STEP 0 decode adapter | [x] | [`decode/copy_decode_adapter.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/copy_decode_adapter.py) L27–L40 | `shapez_core` 위임 |
| 2 | STEP 0.5 ExistingLayoutAnalysis | [x] | [`decode/existing_layout_analysis.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py) L84–L138 | `analyze_decoded_layout` |
| 2 | STEP 1 reconstruction | [x] | [`reconstruction/asteroid_reconstruction.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py) L97–L188 | `reconstruct_asteroid_mining_field` |
| 3 | STEP 2 Pass1 | [x] | [`placement/pass1_outer.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py) L228–L325 | `run_pass1_outer_placement` |
| 3 | STEP 3 Pass2 | [x] | [`placement/pass2_internal.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py) L185–파일 끝 | `run_pass2_internal_fill` |
| 3 | provisional contract 검증 | [x] | [`test_pass1_pass2_provisional_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py) 전체 | `PROVISIONAL_PLACED`·`ROUTED_CONFIRMED` 금지 |
| 4 | STEP4 trunk seed / goal | [ ] | [`routing/trunk_seed.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py) L14–L17 | 스켈레톤 `NotImplementedError` |
| 4 | STEP4 merge-aware router MVP | [ ] | [`routing/merge_aware_router.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py) L19–L22 | 스켈레톤 `NotImplementedError` |
| 4 | routing failure state transition 검증 | [ ] | [`test_step4_routing_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py) 등 | 라우팅 본구현 후 보강 예정 |
| 5 | STEP9 final validation 구현 | [ ] | [`validation/final_validation.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py) L20–L57 | **부분:** `validate_final_layout_stub`만 존재 |
| 5 | STEP10 replay trace output | [ ] | [`replay/trace_event.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/trace_event.py) L13–L21<br>[`replay/snapshots.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py) L15–L31 | DTO·NDJSON reader 스켈레톤 수준 |
| 5 | output-only contract 검증 | [x] | [`test_replay_trace_is_output_only.py`](mdc:tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py)<br>[`test_import_boundaries.py`](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py) L50–L59 | NDJSON reader 미연결·replay import 금지 |
| 6 | v2 solver orchestrator | [ ] | [`solver.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py) L25–L51 | **부분:** `build_copy_preview_v2_sidecars`만; `solve_mining_layout_v2_stub`은 NIE |
| 6 | feature flag adapter | [ ] | — | 별도 어댑터 시퀀스에서 링크 예정 |
| 6 | v1 default 유지 | [ ] | — | 제품 플래그·URL 계약은 Django 앱 쪽 수동 확인 |
| 7 | v2 MVP cross-check report | [ ] | — | 문서 산출물(코드 링크 없음) |
| 7 | full v2 unit tests 통과 | [x] | `python -m pytest tests/unit/shapez_asteroid_v2` (2026-05-14) | 76 passed 스냅샷 |
| 7 | ruff 통과 | [x] | 동일 날짜 `ruff check …/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2` | CI/로컬 로그에 기록 |
| 7 | black --check 통과 | [x] | 동일 날짜 `black --check` 동일 경로 | CI/로컬 로그에 기록 |

# Solver v2 Progress Board

## Phase 0 — 준비
- [ ] v1 freeze 기준 합의
  - // 릴리즈·팀 합의 수동.
- [x] v2 namespace 생성 (확인) [`asteroid_mining_layout_v2/__init__.py` L1–L12](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/__init__.py)
  - // 패키지 docstring·`__version__`.
- [x] import boundary test 생성 (확인) [`test_import_boundaries.py` L9–L133](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - // v1·replay·Django·solver AST·subprocess.

## Phase 1 — Domain Foundation
- [x] DTO / enum / FSM 구현 (확인)
  - [`domain/dto.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
  - [`domain/enums.py` L12–](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py)
  - [`placement/placement_fsm.py` L21–L121](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/placement_fsm.py)
  - // Sequence 02 체크리스트와 동일 근거.
- [ ] semantic namespace guard 구현
  - // 전용 모듈 미도입; `test_import_boundaries`는 v1 패키지 문자열만 차단(상단 표 참고).
- [x] trace semantic guard 구현 (확인)
  - [`domain/trace_semantics.py` L25–L66](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/trace_semantics.py)
  - [`domain/dto.py` TraceEvent.__post_init__ L330–L340](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py)
  - // NDJSON 없이 in-memory 검증.

## Phase 2 — Input / Reconstruction
- [x] STEP 0 decode adapter 구현 (확인) [`copy_decode_adapter.py` L1–약40](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/copy_decode_adapter.py)
- [x] STEP 0.5 ExistingLayoutAnalysis 구현 (확인) [`existing_layout_analysis.py` L84–L138](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py)
- [x] STEP 1 reconstruction 구현 (확인) [`asteroid_reconstruction.py` L97–L188](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/asteroid_reconstruction.py)

## Phase 3 — Placement
- [x] STEP 2 Pass1 구현 (확인) [`pass1_outer.py` L228–약325](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py)
- [x] STEP 3 Pass2 구현 (확인) [`pass2_internal.py` L185–끝](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py)
- [x] provisional placement contract 검증 (확인) [`test_pass1_pass2_provisional_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py)

## Phase 4 — Routing
- [ ] STEP4 trunk seed / goal set 구현
  - // 현재 스켈레톤: [`routing/trunk_seed.py` L14–L17](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py)
  - // 계약 테스트: [`test_step4_trunk_seed_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_step4_trunk_seed_contract.py)
- [ ] STEP4 merge-aware router MVP 구현
  - // [`merge_aware_router.py` L19–L22](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py) NIE.
- [ ] routing failure state transition 검증
  - // 라우팅 본구현 후 [`test_step4_routing_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py) 확장 예정.

## Phase 5 — Validation / Replay
- [ ] STEP9 final validation 구현
  - // 스텁: [`validation/final_validation.py` L20–L57](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py)
  - // 테스트: [`test_final_validation_contract.py`](mdc:tests/unit/shapez_asteroid_v2/test_final_validation_contract.py)
- [ ] STEP10 replay trace output
  - // [`replay/trace_event.py`](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/trace_event.py)
  - // [`replay/snapshots.py` L24–L31](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py)
- [x] output-only contract 검증 (확인)
  - [`test_replay_trace_is_output_only.py`](mdc:tests/unit/shapez_asteroid_v2/test_replay_trace_is_output_only.py)
  - [`test_import_boundaries.py` L50–L59](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
  - // NDJSON reader 미구현·replay import 금지.

## Phase 6 — Integration
- [ ] v2 solver orchestrator 구현
  - // [`solver.py` L25–L51](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py) copy-preview만; `solve_mining_layout_v2_stub` NIE.
- [ ] feature flag adapter 구현
- [ ] v1 default 유지

## Phase 7 — Verification
- [ ] v2 MVP cross-check report 작성
- [x] full v2 unit tests 통과 (확인) `python -m pytest tests/unit/shapez_asteroid_v2` — 2026-05-14, **76 passed**
- [x] ruff 통과 (확인) `python -m ruff check django_apps/shapez_asteroid/services/asteroid_mining_layout_v2 tests/unit/shapez_asteroid_v2` — 2026-05-14
- [x] black --check 통과 (확인) `python -m black --check` 동일 경로 — 2026-05-14


**절대 Merge 금지 ↔ 자동 검증 (참고)**  
위 §0 표와 동일하게, 아래에서 금지 패턴을 부분적으로 커버한다. 전 항목 PR 수동 확인.

- [test_import_boundaries.py](mdc:tests/unit/shapez_asteroid_v2/test_import_boundaries.py)
- [final_validation.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py)
- [pass1_outer.py](mdc:django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py) (docstring 등)

---

# PR 승인 기준

각 PR마다 아래를 만족해야 merge 가능.

```md
- [ ] 이번 Sequence 범위만 수정했다.
- [ ] v1 production solver logic을 건드리지 않았다.
- [ ] canonical document와 충돌하지 않는다.
- [ ] 새 테스트 또는 기존 테스트 보강이 있다.
- [ ] pytest 통과 로그가 있다.
- [ ] ruff 통과 로그가 있다.
- [ ] black --check 통과 로그가 있다.
- [ ] NotImplementedError / TODO가 허용 범위 내에만 있다.
- [ ] 다음 Sequence에 넘길 known gap이 명시되어 있다.

```

---

# 절대 Merge 금지 조건

```md
- [ ] v2에서 v1 solver internals import 발생
- [ ] NDJSON / replay / solver_summary를 algorithm input으로 사용
- [ ] final validation이 route 생성 또는 STEP4 호출
- [ ] Pass1/Pass2가 ROUTED_CONFIRMED 생성
- [ ] cheap escape path를 occupied transport로 commit
- [ ] belt와 pipe graph 혼합
- [ ] orphan existing transport를 trunk seed로 승격
- [ ] QUARANTINED_UNROUTED가 final valid layout에 남음
- [ ] fake success 반환
- [ ] canonical document와 충돌하는 behavior를 테스트 없이 도입

```

---

# 다음 단계

바로 쓸 거면 **Sequence 01 프롬프트 + 위 체크리스트의 Sequence 01 부분**만 먼저 Cursor에 넣는 게 맞습니다.  
통짜로 넣으면 Agent가 범위를 넘어서 Pass3/Reclaim/Recovery까지 건드릴 가능성이 큽니다.