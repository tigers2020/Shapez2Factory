# Algorithm 문서

알고리즘·optimization 레이어 계약 메모를 모아 둔다. **구현 정본**은 코드·[`documents/index/document_inventory.md`](../index/document_inventory.md)의 `CANON`·[`documents/ai/START_HERE.md`](../ai/START_HERE.md)를 우선한다. 이 디렉터리 문서는 주로 `RESEARCH`에 가깝다.

## 구현 베이스라인 (문서 기준일: 2026-05-18)

- **코드 기준으로 완료로 본다:** Decode → Reconstruction(청사진 디코드·정리·재구성·Lab 맥락의 지도/리플레이 입력까지).
- **아래 시리즈 체크리스트**는 동일 날짜에 **전부 미착수(`[ ]`)로 재설정**했다. optimization·POST GA·replay persistence 등은 **향후 작업**으로만 본다.
- **테스트:** 이 폴더 정리에서는 pytest 경로·통과 수·fixture 목록을 **갱신하지 않는다**. 본문에 남은 명령줄은 역사적 보관일 수 있다.

## 읽기 순서

1. [`asteroid_lab_00_overview.md`](asteroid_lab_00_overview.md) — 개요·좌표·금지 사항  
2. [`asteroid_lab_01_optimization_input.md`](asteroid_lab_01_optimization_input.md) ~ [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) — Phase 계약  
3. [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) — 구현 순서(체크리스트)  
4. [`asteroid_lab_11_future_execution_plan_post_sequence.md`](asteroid_lab_11_future_execution_plan_post_sequence.md) ~ [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md) — 이후 로드맵·런타임 배선·페이로드

## 파일 목록

| 파일 | 상태 | 설명 |
|------|------|------|
| `asteroid_lab_00_overview.md` | `RESEARCH` | Optimization layer 개요·원칙 |
| `asteroid_lab_01_optimization_input.md` | `RESEARCH` | `OptimizationInput`·좌표 계약 |
| `asteroid_lab_02_pattern_library.md` | `RESEARCH` | 번들 패턴 라이브러리 |
| `asteroid_lab_03_candidate_generator.md` | `RESEARCH` | 후보 생성 |
| `asteroid_lab_04_route_probe.md` | `RESEARCH` | 경로 탐침 |
| `asteroid_lab_05_genome_fitness.md` | `RESEARCH` | 게놈·적합도 |
| `asteroid_lab_06_evolutionary_search.md` | `RESEARCH` | 진화 탐색 v0 |
| `asteroid_lab_07_incremental_commit.md` | `RESEARCH` | 증분 커밋 |
| `asteroid_lab_08_validation.md` | `RESEARCH` | 검증 게이트 |
| `asteroid_lab_09_replay_debug.md` | `RESEARCH` | 리플레이·디버그 |
| `asteroid_lab_10_development_sequence.md` | `RESEARCH` | 시퀀스별 체크리스트 |
| `asteroid_lab_11_future_execution_plan_post_sequence.md` | `RESEARCH` | 시퀀스 이후 실행 계획 |
| `asteroid_lab_12_runtime_replay_wiring.md` | `RESEARCH` | 런타임 리플레이 배선 |
| `asteroid_lab_13_replay_payload_scalability.md` | `RESEARCH` | 페이로드·지연 로드 로드맵 |

## 초안 (`drafts/`)

| 파일 | 상태 | 설명 |
|------|------|------|
| [`drafts/Asteroid Mining Page Rebuild.txt`](drafts/Asteroid%20Mining%20Page%20Rebuild.txt) | `DRAFT` | 페이지 리빌드 설계 초안 |
| [`drafts/Asteroid Lab 개발 계획.txt`](drafts/Asteroid%20Lab%20개발%20계획.txt) | `DRAFT` | Start-to-end 개발 계획 초안 |

> **참고:** 예전에 `브랜치 · Asteroid Mining Page Rebuild.txt` 이름으로 **UI 디버그 메모**(modal JSX 등)가 있었다면 동일 성격의 메모는 `drafts/`에 두거나 별도 이슈로 옮긴다.

## 경로·패키지 주의

- **2026-05-15:** `django_apps.shapez_asteroid` 앱·채굴 레이아웃 솔버·세션 스펙(`mining_solver_cursor_sessions/`)은 저장소에서 제거되었다. 과거 mining 스펙은 **git 기록**을 본다.
- 시리즈 본문에 남은 `shapez_asteroid`·삭제된 `tests/unit/shapez_asteroid/` 등 인용은 **역사적**이며, 현재 Lab 표면은 **`django_apps/asteroid_lab/`** 등과 1:1로 맞지 않을 수 있다. 교차 확인: [`documents/refactor_audit/00_global_summary.md`](../refactor_audit/00_global_summary.md).

새 알고리즘 정본이 필요하면 `documents/ai/` 플랜·`documents/index/document_inventory.md` 갱신 후 별도 문서로 추가한다.
