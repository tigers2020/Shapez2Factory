# 저장소 맵

> 생성: 2026-05-15. 목적은 `documents/`를 미래 AI 코딩 에이전트와 유지보수자가 신뢰할 수 있는 소스 오브 트루스로 쓰기 위한 1차 지도화다.

## 코드 모듈 트리 요약

| 경로 | 역할 | 감사 메모 |
|---|---|---|
| `config/` | Django 설정과 runtime flag | production code 변경 없음. |
| `django_apps/shapez_core/` | shape parsing/rendering/domain core | asteroid solver v2의 decode/preview가 일부 core decode 서비스를 사용한다. |
| `django_apps/shapez_solver/` | recipe graph, macro recipe, pattern catalog | mining layout v2와 별도 solver 도메인. |
| `django_apps/shapez_asteroid/` | asteroid optimizer 앱, copy-preview API, asteroid map/model/service | 현재 mining layout v2 구현의 주 작업 영역. |
| `django_apps/web/` | 일반 웹 UI, static assets, support/gallery/auth | 생성 sprite와 static asset은 문서 정본이 아니다. |
| `assets/`, `frontend/` | Tailwind/프론트 소스 | 이번 감사에서는 변경 대상 아님. |
| `scripts/` | 디버그/렌더/locale 보조 스크립트 | debug NDJSON reader는 증거 분석용. |
| `tests/` | unit/integration tests | v2 계약 테스트는 `tests/unit/shapez_asteroid_v2/`. |
| `var/` | 실행 로그, debug output, checklist snapshot | generated/debug artifact. 정본 spec로 사용 금지. |

## solver 관련 모듈 경로

| 경로 | 현재 판단 |
|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/` | current/v2 skeleton 및 부분 구현. canonical session specs와 교차검증 대상. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/` | STEP 0.5 ExistingLayoutAnalysis. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/` | STEP 1 reconstruction. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/` | STEP 2 Pass1, STEP 3 Pass2, PlacementCommitState helper. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/` | STEP 4 routing skeleton/utility. `route_all` and trunk seed are not implemented. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/` | STEP 9 final validation skeleton. |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/` | STEP 10 replay/trace schema and offline adapter stubs. |
| `django_apps/shapez_asteroid/services/asteroid_reconstruction.py`, `asteroid_patch_interior.py` | pre-v2 support/legacy-adjacent services. Use with caution. |
| `django_apps/shapez_asteroid/services/behavior_artifact_collector.py`, `v2_behavior_artifact_dump.py` | behavior artifact output stack, not solver algorithm input. |

## 테스트 경로

| 경로 | 역할 |
|---|---|
| `tests/unit/shapez_asteroid_v2/` | v2 import boundaries, DTO/enums, reconstruction, Pass1/Pass2, routing skeleton, replay output-only contracts. |
| `tests/unit/shapez_asteroid_v2/test_import_boundaries.py` | v2가 v1/replay/output stack에 잘못 의존하지 않는지 검증. |
| `tests/unit/shapez_asteroid_v2/test_existing_layout_analysis_contract.py` | STEP 0.5 read-only and kind-separated transport contract. |
| `tests/unit/shapez_asteroid_v2/test_reconstruction_contract.py` | STEP 1 mineable reconstruction contract. |
| `tests/unit/shapez_asteroid_v2/test_pass1_pass2_provisional_contract.py` | Pass1/Pass2 provisional-only contract. |
| `tests/unit/shapez_asteroid_v2/test_step4_routing_contract.py` | STEP4 DTO/skeleton contract. |
| `tests/unit/shapez_asteroid_v2/test_final_validation_contract.py` | final validation skeleton behavior. |
| `tests/fixtures/pass12_telemetry_trace_pack/*.ndjson` | fixture/generated evidence, not canonical spec. |

## 문서 디렉터리 맵

| 경로 | 권위 상태 | 메모 |
|---|---|---|
| `documents/Algorithm/mining_solver_cursor_sessions/` | canonical_spec | 사용자 지정 01-14 canonical authority. |
| `documents/Algorithm/checklist.md` | checklist | v2 구현 진척/검증 표. 정본은 아님. |
| `documents/ai/` | canonical/active mixed | AI entrypoint, manuals, current plan, checklist가 섞여 있음. |
| `documents/index/` | canonical_spec | document lifecycle/inventory routing layer. |
| `documents/adr/` | canonical_spec | 이유/결정 기록. Algorithm spec을 대체하지 않음. |
| `documents/plans/`, `documents/ai/plans/` | implementation_plan | 승인/진행 범위. 완료분 archive 검토 필요. |
| `documents/reports/`, `documents/research/`, `documents/notes/`, `documents/debug/` | audit_report | 관측/분석. 정본 충돌 시 정본 우선. |
| `documents/archive/` | historical_reference | current implementation 판단에 사용 금지. |
| `documents/refactory/` | obsolete_or_conflicting | v1-era redirect 성격. archive 상태 유지 권장. |
| `documents/samples/` | generated_output/reference | copy/decode sample. algorithm input 금지. |

## 생성/디버그 산출물 디렉터리

- `var/asteroid_mining_layout_debug/`: NDJSON/JSON debug evidence.
- `var/shapez_copy_debug/`: copy-preview decode/debug output.
- root `v2_behavior_artifact_*.json`: generated behavior artifacts. 문서 정본 아님.
- `tests/fixtures/pass12_telemetry_trace_pack/*.ndjson`: fixture evidence only.
- `documents/samples/*.json`: sample evidence only.
- `.graph_preview_cache*`, `.pytest_cache`, `.ruff_cache*`, `.mypy_cache*`: tool cache.

## 초기 위험 메모

1. `documents/README.md`와 `documents/Algorithm/mining_solver_cursor_sessions/README.md`가 현재 터미널 출력에서 mojibake처럼 보였다. 실제 파일 인코딩/렌더링을 별도 확인해야 한다.
2. canonical directory 안의 `14_step4_routing_dto_refactor_inventory.md`, `15_step4_telemetry_field_semantics.md`는 사용자 지정 01-14 범위 밖이다. 정본 승격 여부가 불명확하다.
3. v2 implementation은 STEP 0.5, STEP 1, STEP 2, STEP 3 일부가 구현되어 있고 STEP 4/9/10은 skeleton 또는 output-only adapter가 많다.
4. archive 문서에는 v1 경로와 `latest.ndjson` 분석이 많다. 현재 판단에 재사용하면 v1/v2 drift가 재발할 수 있다.
