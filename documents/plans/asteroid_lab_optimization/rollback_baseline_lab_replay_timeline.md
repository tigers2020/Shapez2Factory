# Rollback Baseline — Lab Replay Timeline Refactor Agent Boundary


> **Plans snapshot:** Not mirrored in `documents/Algorithm/`. For live contracts see [`documents/Algorithm/`](../../Algorithm/). **PR-F (2026-05):** dense server coords removed from product code.

## 목적

이 문서는 **통합 Lab 리플레이 리팩터** 작업 시 에이전트·인간 모두가 따를 **경계(정본)** 를 고정한다.

별도 Optimization 리플레이 **프론트/런타임 트랙**이 들어가기 전 상태로 의도적으로 롤백한 뒤, 최적화 단계 리플레이는 **기존 Lab 리플레이 타임라인에 프레임을 덧붙이는 방식**으로만 재구축한다.

**Sequence 3B-R (unified RTTP append):** [`docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md`](../../docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md)

## 기준선(Baseline)

권위 있는 기준 커밋(롤백 직전 한 커밋의 부모):

```text
10b3b966081496c3d67394d87780dc17e801c512^
```

이 기준선에 맞춘 **현재 로컬 checkout**이 구현 정본이다. 원격의 최신 `HEAD`나 이후 커밋의 파일 내용은 정본이 아니다.

## 에이전트 경계(필수)

에이전트는 **오직 현재 로컬 checkout**만을 기준으로 작업한다.

금지:

```text
- GitHub 원격 HEAD를 열어 구현 세부를 참고하는 행위
- 최적화 리플레이 코드를 찾기 위해 더 새 커밋을 검색하는 행위
- 10b3b966081496c3d67394d87780dc17e801c512 이후 커밋에서 파일·함수를 복사하는 행위
- 이전 separate Optimization 리플레이 구현을 기억·추론으로 재생성하는 행위
```

이 checkout에 존재하지 않는 파일·함수·클래스·테스트·문서는 **더 이후 커밋을 보고 재현하지 않는다.**

## 금지: 분리형 Optimization 리플레이 심볼

아래는 제거된 **듀얼 트랙** 구현으로의 회귀 신호다. 런타임·프론트 리플레이 경로에 나타나면 중단하고 제거한다(역사적 문서 전용으로 명시적으로 남기는 경우만 예외 검토).

```text
optimization_replay_frames
optimization_replay_payload_for_project
optimization-replay-json
optimizationReplayTrack
optimizationReplayFrameIndex
renderOptimizationReplayHud
replaceOptimizationReplayPayload
optimization_replay_attach
dual-track optimization replay
no implicit sync policy
```

### 예외(시각 전용): 통합 타임라인 위 optimization 오버레이

다음은 **듀얼 트랙이 아니라**, 단일 `lab_replay_frames_json`·단일 `currentFrameIndex` 안에서 Lab 베이스 그리드 위에만 쌓는 **출력 전용 시각 레이어**로 허용한다.

```text
projectOptimizationReplayFrameToLabOverlay   # 단일 타임라인 프레임 → 오버레이 지시
lab-optimization-overlay-layer               # #lab-replay-grid 위 DOM 레이어
```

금지는 그대로다: 별도 optimization 리플레이 JSON 스크립트, `optimizationReplayFrameIndex` 같은 **둘째 인덱스**, 두 타임라인 동기화, `optimization_replay_attach`로 별 페이로드 노출.

## 목표 아키텍처

리플레이는 **하나의 타임라인**만 존재한다.

```text
ReplayTrack / ReplayFrame
lab_replay_frames_json
currentFrameIndex
#lab-replay-grid
```

최적화 단계 이벤트는 기존 Lab 리플레이 프레임 시퀀스 **끝에 append** 한다.

다음은 허용하지 않는다: 두 번째 optimization 리플레이 페이로드, 두 번째 리플레이 인덱스, 두 타임라인 간 동기화 레이어.

## 필수 동작(수용 예시)

검사/재구성 리플레이가 67프레임이고, 최적화가 15개의 리플레이 이벤트를 내면:

```text
최종 lab_replay_frames_json 프레임 수 = 82
append된 frame_index = 67..81 (0부터 연속 유지)
```

append된 최적화 프레임은 **기존 Lab 스크러버·그리드 경로**로만 선택·렌더링된다.

## 구현 규칙

**이전 separate Optimization 리플레이 구현을 구제(salvage)하지 않는다.**

통합 리플레이 확장은 **롤백 기준선 위에서만** 설계·구현한다.

허용:

```text
최적화 알고리즘이 내부 디버그/이벤트 객체를 emit하는 것
그 객체를 즉시 Lab ReplayFrame 호환 프레임으로 적응시키는 것
```

금지:

```text
최적화 리플레이를 별도 UI/런타임 트랙으로 저장·노출하는 것
```

## 사전 점검(Preflight)

### Bash

```bash
git rev-parse HEAD
git merge-base --is-ancestor 10b3b966081496c3d67394d87780dc17e801c512^ HEAD
git status --short
git grep -n "optimization_replay\|optimization-replay-json\|optimizationReplayTrack\|optimizationReplayFrameIndex" || true
```

`git merge-base --is-ancestor` 가 0이 아니면(실패): 현재 `HEAD`가 기준선을 조상으로 포함하지 않는다.

`git grep` 종료 코드 `1`은 매칭 없음으로 **정상**이다. `2` 이상은 오류로 본다.

### PowerShell

```powershell
git rev-parse HEAD
git merge-base --is-ancestor 10b3b966081496c3d67394d87780dc17e801c512^ HEAD
if ($LASTEXITCODE -ne 0) { throw "HEAD is not based on rollback baseline" }

git status --short

git grep -n "optimization_replay\|optimization-replay-json\|optimizationReplayTrack\|optimizationReplayFrameIndex"
if ($LASTEXITCODE -gt 1) { throw "git grep failed" }
```

`git grep` 종료 코드 `1`(매칭 없음)은 허용. `0`은 매칭 있음(별도 정책에 따라 중단·조사).

## 수용 테스트(검증 관점)

```text
- Run Solver JSON 응답에 lab_replay_frames_json 타임라인이 하나만 노출된다.
- 최적화 단계 프레임이 동일 리스트에 append된다.
- frame_index는 0부터 final_count - 1까지 연속이다.
- 렌더된 프로젝트 HTML에 `optimization-replay-json` / `optimizationReplayTrack` / `optimizationReplayFrameIndex` 문자열이 없다.
- (예외) `#lab-optimization-overlay-layer` 및 `data-lab-optimization-overlay-enabled` 는 **단일 타임라인 시각 레이어**로 허용된다.
- 기존 Lab 스크러버로 append된 최적화 프레임을 선택할 수 있다.
- 리플레이는 출력 전용이며 솔버 입력으로 쓰이지 않는다.
```

## 검증 명령

```bash
python -m pytest
python -m ruff check .
python -m mypy .
python -m black --check .
```

단일 디렉터리로 빠르게 볼 때(예시):

```bash
python -m pytest tests/unit/asteroid_lab/
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py
```

## 다음 진행 순서(권장)

1. 이 문서를 저장·승인 계열에 포함한다.
2. working tree를 정리(stash·커밋·폐기 정책 합의)한다.
3. 기준선에서 새 브랜치를 만든다:

```bash
git checkout -b refactor/unified-lab-replay-from-baseline 10b3b966081496c3d67394d87780dc17e801c512^
```

4. 에이전트 세션 프롬프트 첫머리에 다음을 둔다:

```text
Read and obey documents/plans/asteroid_lab_optimization/rollback_baseline_lab_replay_timeline.md before editing code.
```

## 관련 플랜 문서(구 서술 정렬)

아래 파일이 **아직 없거나** 과거 초안에 **Lab / Optimization dual-track·독립 `optimizationReplayFrameIndex`** 를 불변으로 두었다면, 구현·문서 정본은 **본 rollback 문서 + `asteroid_lab_00_overview.md` §1b·1c** 를 따른다. Phase 9·10 플랜 본문 상단에 *Unified Lab Replay Timeline* superseded 메모를 두었다.

```text
documents/plans/asteroid_lab_optimization/asteroid_lab_09_replay_debug.md
documents/plans/asteroid_lab_optimization/asteroid_lab_10_development_sequence.md
(작성 예정) asteroid_lab_12_runtime_replay_wiring.md
(작성 예정) asteroid_lab_13_replay_payload_scalability.md
```

## Git의 역할에 대한 메모

```text
1. Git은 작업 기준을 고정하는 장치일 뿐이다.
2. 에이전트의 기억·검색·최신 패턴 재생성은 이 문서·프롬프트·grep 게이트로 막는다.
```
