---
status: ACTIVE
owner: solver-architecture
last_reviewed: 2026-05-13
supersedes: []
superseded_by:
related_epics:
  - asteroid_mining_layout DTO modeling
---

# asteroid_mining_layout DTO 인벤토리 (2026-05-13)

## 목적

`asteroid_mining_layout`의 DTO 정비는 동작 변경 없이 경계 타입을 먼저 올리는 작업이다. 이 문서는 [`03_data_schema_dto.md`](../../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) E절과 현재 코드의 `dict[str, Any]` 기반 필드를 대조해, 구현 착수 전에 승인할 수 있는 0단계 인벤토리만 정리한다.

## 상위 호출 경로 인벤토리

| 우선순위 | 경로 | 현재 느슨한 타입 | 주요 필드/역할 | 1차 정비 후보 |
|---:|---|---|---|---|
| 1 | [`existing_layout/existing_layout_analysis.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/existing_layout/existing_layout_analysis.py) | `dict[Coord, dict[str, Any]]`, `dict[str, Any]` | `source_kind`, `transport`, `transport_by_kind`, `equipment`, `issues`, `solver_hints` | `ExistingLayoutAnalysisWire` + 하위 TypedDict |
| 2 | [`validation/final_validation.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/validation/final_validation.py) | `list[dict[str, Any]]`, `dict[Coord, dict[str, Any]]` | `cells_dict_from_mining_map`, `mineable_bbox`, connectivity 검사 입력 | 공유 `MiningMapCell` / `MiningMapCells` |
| 3 | [`step4/step4_route_failure_detail.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_route_failure_detail.py) | `dict[str, Any]` | `ROUTING_FAILURE_DETAIL_KEYS`, `routing_failure_detail`, flat top-level mirror | `Step4RoutingFailureDetailWire` |
| 4 | [`step4/step4_routing_models.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/step4/step4_routing_models.py) | `Mapping[str, Any]`, `dict[str, Any]` | `search_stats`, `evidence`, `failures`, `p2c_metrics`, live `cells` | `Step4SearchStatsWire`, `Step4FailureEvidenceWire` |
| 5 | [`dto/timeline_types.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/dto/timeline_types.py) | `summary: dict[str, Any]`, `mining_map: list[dict[str, Any]]` | `solver_timeline` 프레임 와이어 | `SolverTimelineSummaryWire`, `MiningMapRowWire` |
| 6 | [`solver/solver_replay_events.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py) | `events: list[dict[str, Any]]`, payload helper 반환 `dict[str, Any]` | replay `kind`, `event_type`, corridor payload, transaction payload | 이벤트별 payload TypedDict |
| 7 | [`solver/solver_replay_frames.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_frames.py) | `list[dict[str, Any]]` | `ui_frames`, `event_indices`, cycle bounds, overlay slices | `ReplayUiFrameWire` |
| 8 | [`placement/pass12_route_probe.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py) | `Pass2RouteProbePack.cells`, `existing_layout_analysis`, `stats_sink` | Pass2 probe stats, goal trace, component probe diagnostics | `Pass2RouteProbeStatsWire`, `Pass2GoalTraceWire` |
| 9 | [`placement/pass12_bundle_commit.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_bundle_commit.py) | replay payload `dict[str, Any]`, `replay_events` | `pass12_bundle_commit` payload: placement/stub/extension/new transport | `Pass12CommitReplayPayloadWire` |
| 10 | [`existing_layout/pass12_existing_layout_hints.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/existing_layout/pass12_existing_layout_hints.py) | `existing_layout_analysis: dict[str, Any]`, `solver_hints: dict[str, Any]` | Pass12 block extras, hint coord union, meta | `ExistingLayoutSolverHintsWire` |

## `03_data_schema_dto.md` E절 vs 코드 필드 대조

| 문서 계약 | 코드 위치 | 현재 코드 필드 | 차이/판단 |
|---|---|---|---|
| `ExistingLayoutAnalysis.source_kind` | `analyze_existing_layout_from_mining_map` 반환 | `source_kind` | 이름 일치. `SourceKind` Literal은 이미 있음. |
| `ExistingLayoutAnalysis.island_bbox` | 같은 반환 | `island_bbox` | 이름 일치. 값은 JSON object 또는 `None`. |
| `ExistingLayoutAnalysis.transport` | 같은 반환, `_analyze_one_transport_kind` | `transport` | 문서의 `ExistingTransportAnalysis`에 대응. mixed일 때 `by_kind`가 내부에 추가됨. |
| `ExistingLayoutAnalysis.transport_by_kind` | 같은 반환 | `transport_by_kind` | 문서 E절에는 명시적 최상위 필드로 강하게 고정돼 있지 않음. mixed transport 보조 필드로 코드가 더 구체적임. |
| `ExistingLayoutAnalysis.equipment` | 같은 반환 | `equipment.miner_count`, `extension_count`, `miners_without_adjacent_transport`, `miners_attached_to_orphan_transport`, `equipment_attachment` | 문서 방향과 일치. `equipment_attachment`는 현재 빈 리스트 기본값. |
| `ExistingLayoutAnalysis.issues` | 같은 반환 | `issues[].code`, `severity`, `coords`, `component_ids`, `message` | 문서 방향과 일치. `IssueCode` Literal은 이미 있음. |
| `ExistingLayoutAnalysis.solver_hints` | 같은 반환 | `trunk_seed_cell_union`, `cleanup_candidate_cell_union` | 문서 E.9와 일치하는 핵심 힌트. Pass12/P4 소비 경로가 이미 존재. |
| `DecodedExistingLayoutContext.analysis` | STEP0 decode 문서 계약 | 별도 wrapper 없음 | 현재 구현은 분석 dict를 직접 전달. 다음 단계에서 dataclass 또는 wrapper DTO 여부 결정 필요. |
| `ExistingTransportComponent.cells` | `_analyze_one_transport_kind` | `components[].cells` | 좌표는 `list[list[int]]`로 직렬화됨. 문서의 `frozenset[Coord]` 내부 표현과 와이어 표현 분리 필요. |
| `ExistingLayoutSolverHints` 확장 필드 | `pass12_existing_layout_hints.py` 소비 | `pass12_fixed_output_stub_cells` 등 선택 키 소비 | 분석 반환의 기본 `solver_hints`에는 없음. 별도 overlay/hint 확장으로 취급해야 함. |

## 승인 전 결정점

1. 공유 셀 행 타입은 `dto/mining_map_cell.py`에 둔다. 이유: `final_validation`, `existing_layout`, `step4`, `pass3`, `timeline`이 모두 와이어 또는 준와이어 `mining_map` 행을 공유한다.
2. 1차 `TypedDict`는 `total=False`로 시작한다. 필수 키를 좁히는 작업은 읽기 전용 소비자 적용 후 별도 단계에서 한다.
3. `ExistingLayoutAnalysis`는 먼저 와이어 `TypedDict`를 정의하고, dataclass 직렬화 helper는 2차 단계에서 추가한다. 현재 호출부가 JSON-friendly dict를 직접 소비하므로 한 번에 dataclass로 바꾸면 파급이 크다.
4. STEP4 실패 상세는 `ROUTING_FAILURE_DETAIL_KEYS` 순서를 변경하지 않는다. 타입은 반환 시그니처와 내부 `cast`로만 도입한다.
5. replay/timeline payload는 이벤트 `kind` 2~3개씩 쪼개 적용한다. `solver_replay` root 버전 또는 NDJSON 필드 추가/삭제가 필요하면 별도 플랜으로 분리한다.

## 제안 작업 순서

| 단계 | 범위 | 산출물 | 검증 |
|---:|---|---|---|
| 1 | 공유 셀 행 타입 | `dto/mining_map_cell.py`, 읽기 소비자 타입 힌트 | `pytest tests/unit/shapez_asteroid/` 중 final validation/existing layout |
| 2 | Existing layout wire | `ExistingLayoutAnalysisWire`와 하위 타입, `as_dict` 경계 | existing layout 관련 unit + mypy 대상 모듈 |
| 3 | STEP4 failure detail | `Step4RoutingFailureDetailWire`, 빌더 반환 타입 | step4 route failure unit + 키 순서 스냅샷 |
| 4 | replay/timeline | `ReplayEventWire`, `ReplayUiFrameWire`, timeline summary/mining map row | replay frame unit + NDJSON/golden diff 있으면 바이트 diff |
| 5 | Pass12 probe stats | `Pass2RouteProbeStatsWire`, `Pass2GoalTraceWire` | Pass2 probe/provisional step4 tests |
| 6 | export 정리 | `dto/__init__.py` export, `P4BundleEval` 공개 이름 결정 | ruff, mypy |

## 범위 밖

- 전 패키지 `dict[str, Any]` 일괄 제거.
- replay/trace 필드 삭제, rename, 키 순서 변경.
- solver 동작, phase order, skip reason, summary key 변경.
