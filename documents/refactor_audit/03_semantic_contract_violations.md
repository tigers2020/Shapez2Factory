# Semantic Contract Violations

## 기준

- canonical refs: `01_project_overview.md`, `03_data_schema_dto.md`, `13_step9_validation.md`, `14_step10_replay_ui.md`

## 위반/드리프트 목록

| File | Finding | Suspected root cause | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/services/replay_pipeline_service.py` | `algorithm_label="inspection_only"`인데 `SolverRun`/`ReplayTrack`를 생성하며 solver pipeline처럼 보이게 함 | inspection replay scaffold를 solver 도메인에 억지로 수용 | `01_project_overview.md` §2, `02_pipeline_control_flow.md` | `P1` | High | `rewrite` |
| `django_apps/asteroid_lab/models.py` | `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot`가 live flow에 연결되지 않음 | future solver schema를 조기 영속화 | `03_data_schema_dto.md`, `02_pipeline_control_flow.md` | `P1` | High | `deprecate` |
| `django_apps/web/views/public_pages.py` | `"force=True"`가 에러 문자열에 들어가면 재시도하는 규칙 | typed failure contract 부재 | `02_pipeline_control_flow.md` | `P1` | High | `rewrite` |
| `django_apps/asteroid_lab/services/input_service.py` | `persist_decoded_snapshot(...)`가 "project의 최신 map_input"을 수정 | target row를 명시하지 않는 mutation contract | `03_data_schema_dto.md` §E | `P1` | Medium | `rewrite` |
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer가 `frame_payload.full_map`이 없으면 `cell_overlay_json.cells`를 full_map으로 승격 | output schema authority가 분산 | `14_step10_replay_ui.md` §16.3 | `P1` | High | `isolate` |
| `django_apps/asteroid_lab/services/dto.py` | DTO 한 파일에 replay, decode, inspection, topology, orchestration 의미가 혼재 | 경계보다 편의성 우선 설계 | `03_data_schema_dto.md` | `P1` | High | `split` |

## canonical 대비 부재 항목

아래는 "잘못 구현"보다 "현재 live tree에 정의되지 않음"에 가깝다.

| Missing contract | Live status | Canonical refs | Severity | Action |
|---|---|---|---|---|
| `PlacementCommitState` FSM | 없음 | `03_data_schema_dto.md` §B | `P1` | `migrate` |
| `RecoveryTrigger / CommitReason / RollbackReason` 분리 | 없음 | `03_data_schema_dto.md` §B, `11_step8_recovery.md` | `P1` | `migrate` |
| assertion-only final validation | 전용 모듈 없음 | `13_step9_validation.md` | `P1` | `migrate` |
| cycle-based streaming trace | 5-frame snapshot replay만 존재 | `14_step10_replay_ui.md` §16.1 | `P1` | `migrate` |
| protected corridor lifecycle | 전용 타입/모듈 없음 | `12_protected_corridor.md` | `P1` | `migrate` |

## 메모

현재 live `asteroid_lab`는 canonical solver의 "초기 decode/inspection/replay 관찰 실험실"로 읽으면 의미가 맞지만, `SolverRun`과 관련 모델 명명 때문에 full solver로 오인되기 쉽다. 이 semantic drift를 먼저 제거하지 않으면 후속 리팩터가 계속 잘못된 contract 위에서 진행된다.
