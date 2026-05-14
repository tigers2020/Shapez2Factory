# v2 copy-preview 행동 산출물 (behavior artifact)

## 목적

copy-preview 요청 한 건에 대해 **decode → STEP 0.5 → STEP 1 → 프리뷰 타임라인 → Pass1 replay_events**까지의 관측 가능한 상태를 **단일 JSON 파일**로 남긴다. 개발·오프라인 분석용이며 **솔버 입력이 아니다**.

## 정본과의 관계

- 권위: `documents/Algorithm/mining_solver_cursor_sessions/README.md` 및 `04_step0_decode`, `05_step1_reconstruction`, `06_step2_pass1_placement`, `14_step10_replay_ui` 등.
- **Replay NDJSON**(`trace_event` 등) · **Debug NDJSON**(`debug_log_event` 등) · **Solver DTO** · **본 산출물**은 역할이 다르다. 상호 대체·입력으로의 사용을 하지 않는다.
- v1 `var/asteroid_mining_layout_debug` NDJSON과는 **별도 계약**이다.

## 계약 요약

| 항목 | 값 |
|------|-----|
| 환경 변수 | `SHAPEZ_COPY_DEBUG_DIR` (비어 있으면 무동작). **상대 경로는 프로젝트 루트(`BASE_DIR`) 기준**으로 풀린다. |
| `schema_version` | `v2.copy_preview_behavior_artifact.1` |
| `artifact_kind` | `copy_preview_behavior` |
| `algorithm_input` | 항상 `false` |
| `http_response_included` | 항상 `false` |
| 기본 포함 `mining_map` 행 | 없음 (`preview_frames`는 `id` + `summary`만) |
| Pass1 | **단일** `run_pass1_outer_placement` 실행에서 나온 `pass1_replay_events` 전체 |
| 원문 copy 문자열 | 기본 저장하지 않음 (`input_digest_prefix`만) |

## 구현 경계

**허용**: `copy_preview` 뷰, `build_copy_preview_v2_sidecars`, 프리뷰 타임라인 조립, `v2_behavior_artifact_dump` 모듈.

**금지**: `domain/*`, `reconstruction/asteroid_reconstruction.py` 코어, `pass1_outer.py`, routing/validation이 collector·dumper를 import; 솔버가 산출물 파일을 읽어 분기.

## STEP 1 diagnosis

- `ReconstructionDTO` 생성 **이후**, `mineable_placement_cells`가 비었을 때만 `diagnose_reconstruction_mineable_empty(decoded, reconstruction=recon)` 호출해 산출물에 기록.
- 진단 결과로 Pass1 스킵·mineable 보정·DTO 변경을 하지 않는다. 예외 시 `step_1_diagnosis_error`에 문자열을 남기고 나머지 산출물은 계속 쓴다.

## 검증

구현 후: `tests/unit/shapez_asteroid_v2/test_behavior_artifact_dump.py`, `test_import_boundaries.py` 확장, 기존 v2 단위 테스트 및 `ruff` / `mypy` (플랜 본문 검증 절 참고).
