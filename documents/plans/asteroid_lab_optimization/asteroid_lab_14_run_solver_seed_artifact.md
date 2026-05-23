# Asteroid Lab — Sequence 14: Run Solver Seed Artifact 경계


> **Plans snapshot:** Not mirrored in `documents/Algorithm/`. For live contracts see [`documents/Algorithm/`](../../Algorithm/). **PR-F (2026-05):** dense server coords removed from product code.

> **상태:** ACTIVE (사람 승인 후 구현). Lab 단일 `ReplayTrack`·append 정본은 `rollback_baseline_lab_replay_timeline.md`와 `asteroid_lab_00_overview.md` §1b를 따른다.

## 1. 역할 (Architecture Reviewer 합의)

엔드포인트(`create-project` vs `run-solver`)는 이미 분리되어 있으나, **Run Solver 내부**가 inspection 준비와 동급의 파이프라인을 한 번 더 탄다.

```text
copy string decode (decode_copy_string) → Run Solver에서는 하지 않음 (현행).
decoded_json → snapshot → cleanup → reconstruction → optimization input 준비 → Run Solver에서 매번 재실행 (문제).
```

**“같은 코드를 도는가?”**에 대한 정확한 답은 위와 같다. 버튼을 둘로 둘 **의미는 있으나**, UI 계약 “저장된 baseline 위에 append”를 완전히 만족하려면 Run Solver 내부를 바꿔야 한다.

## 2. 핵심 문제: 두 정본의 혼합

현재 `run_lab_solver_optimization_for_map_input`는 대략 다음을 동시에 쓴다.

```text
baseline full_map
  ← ReplayTrack 마지막 ReplayFrame에서 추출

optimization 입력 (cleanup / reconstruction / OptimizationInput / route seed)
  ← AsteroidMapInput.decoded_json에서 snapshot을 다시 만들고 재계산
```

이 둘이 항상 동일한 결과를 낸다는 보장이 약하다. 좌표·flatten·reconstruction 경계 이슈가 있으면 **Run Solver에서 재발**한다.

## 3. 목표 장기 구조

```text
Save/Open Project (유일한 baseline·seed 생성 구간)
  → copy_code 저장
  → decoded_json 저장
  → cleanup / reconstruction 실행 (inspection 경로)
  → canonical inspection ReplayTrack 생성
  → OptimizationSeedArtifact 저장 (optimizer 전용 정본)

Run Solver
  → map_input_id·canonical inspection ReplayTrack 검증
  → OptimizationSeedArtifact 로드
  → optimizer만 실행
  → 동일 ReplayTrack 뒤에 optimization_* 프레임 append
```

**금지 (Run Solver):**

```text
AsteroidMapInput.decoded_json에서 cleanup / reconstruction을 다시 돌려 optimization 입력을 만들 것.
```

## 4. 구현 옵션 비교

### 옵션 A — Optimization seed 저장 (권장)

**역할:** `ReplayFrame`이 아니라 **optimizer 입력 전용** persisted artifact.

저장 시점 예: `build_initial_replay_for_map_input` 성공 직후(또는 동일 트랜잭션 정책으로 명시).

저장 위치 후보:

```text
(1) AsteroidMapInput.optimization_seed_json  — 단순, 마이그레이션 1컬럼
(2) AsteroidOptimizationSeed (별도 모델) — map_input_id, replay_track_id, 버전, JSON 필드 분리
```

필드 예시(이름은 구현 시 조정):

```text
map_input_id
replay_track_id (canonical inspection; seed가 어떤 트랙과 함께 유효한지)
schema_version
cleanup_snapshot_json (또는 직렬화된 CleanupResult)
reconstruction_summary_json (선택)
optimization_input_json
route_domain_seed_json (선택; 빌더가 seed에서만 복원 가능하면)
created_at
```

**장점:** create-project vs run-solver 계약 분리, run-solver에서 좌표/flatten 재진입 제거, append 디버깅 단순화.

**단점:** seed 스키마·버전 관리, 마이그레이션·무효화 정책(코드 변경 시 재생성 트리거) 필요.

### 옵션 B — ReplayTrack 특정 프레임을 canonical source

예: 특정 `frame_key`의 `full_map`을 optimization 입력 소스로 사용.

**단점:** Replay를 알고리즘 입력으로 재소비하는 형태가 되어 `asteroid_lab_00_overview.md` §1 “Replay-driven algorithm 금지” 철학과 충돌 소지가 크다. **비추천.**

### 옵션 C — 재계산 유지 + strict equivalence 테스트

Save/Open 시점 산출과 Run Solver 재계산이 바이트/구조적으로 같아야만 통과.

**단점:** 근본 계약이 “baseline 위 append”로 명확해지지 않고, 동일 클래스 버그가 반복된다. **임시 방편.**

## 5. 권장: 옵션 A

이름 예: `OptimizationSeedArtifact` / `AsteroidOptimizationSeed` (구현에서 하나로 통일).

```text
ReplayFrame = output-only (기존 원칙 유지)
OptimizationSeedArtifact = canonical optimizer input (신규 정본)
```

## 6. 플랜에 넣을 핵심 문구 (계약, EN)

```text
Save/Open Project is the only endpoint allowed to decode, cleanup, and reconstruct a map input.

Run Solver must not regenerate cleanup or reconstruction from AsteroidMapInput.decoded_json.
Run Solver consumes a persisted OptimizationSeedArtifact produced by the canonical inspection build.

ReplayFrame remains output-only.
OptimizationSeedArtifact is the canonical optimizer input.
```

한 줄 요약:

```text
Save/Open creates the canonical baseline and optimization seed.
Run Solver only optimizes against that seed and appends frames.
```

## 7. 구현 순서 (승인 후)

```text
1. 본 문서·스키마 초안 리뷰 승인
2. 모델 또는 JSON 컬럼 + schema_version 결정
3. Save/Open 경로에서 inspection 성공 후 OptimizationSeedArtifact 생성·저장
4. Run Solver에서 snapshot→cleanup→reconstruction 경로 제거; seed만 로드
5. integration test:
   - Save/Open 후 seed 존재
   - Run Solver는 seed 읽기만 (decoded_json 기반 재구성 호출 없음을 단언 가능한 수준으로)
   - 동일 replay_track에 프레임 수 증가
6. 정적 경계(가능하면): web `asteroid_lab_optimization_run`이 cleanup/reconstruction 빌더에 직접 의존하지 않도록 — seed 로더·역직렬화 모듈로 이동
```

## 8. 기존 코드 앵커 (참고용)

- Save/Open·inspection: `django_apps/web/views/public_pages.py` — `asteroid_miner_layout_create_project`, `build_initial_replay_for_map_input`
- Run Solver: `django_apps/web/views/public_pages.py` — `asteroid_miner_layout_run_solver`; `django_apps/web/services/asteroid_lab_optimization_run.py` — `run_lab_solver_optimization_for_map_input`
- 스냅샷 로드: `django_apps/asteroid_lab/services/cell_snapshot_service.py` — `build_decoded_blueprint_snapshot_from_input`

## 9. 승인 게이트

- 본 문서의 seed 필드 범위(최소: `optimization_input_json`만으로 충분한지, route seed까지 필요한지) 확정
- 마이그레이션·기존 프로젝트 무 seed 시 Run Solver 동작(400 + “inspection만 다시 저장” 안내 vs 자동 백필) 결정

---

**다음 액션:** 사람 승인 후 위 순서 2번부터 구현. 구현 전에는 `asteroid_lab_optimization_run.py`의 재계산 경로를 바꾸지 않는다.
