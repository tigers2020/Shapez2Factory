# 매뉴얼: Testing · 검증

TDD·계약·게이트 **상세 정본**. 라우팅·작업 분류 요약은 [`AGENTS.md`](../../../AGENTS.md) **Development Mode: Contract-first TDD**.

## pytest (기본: 변경 범위만)

- **기본:** 이번에 손댄 코드·모듈과 직접 연결된 테스트만 실행한다. 예: 바꾼 파일 옆 `tests/unit/...`의 해당 모듈, 또는 `pytest path/to/test_file.py` / `pytest tests/unit/some_package/`.
- **전체 스위트** (`python -m pytest`, 루트에서 전부): PR·병합·CI·광역 회귀 등 **꼭 필요할 때만** ([Quality gate sequence](#quality-gate-sequence) PR full gate 참고).
- 구간·마커는 아래 **구간 실행** 표를 따른다.

```bash
# 예: 작업 디렉터리 한정
python -m pytest tests/unit/asteroid_lab/test_example.py

# 전체 (PR / 병합 / CI)
python -m pytest
```

---

## Development Mode: Contract-first TDD

**기본 흐름**: 공개 행위·도메인 계약·불변식·회귀·데이터 변환 경계를 **테스트로 먼저 고정** → **최소 구현** → 게이트 통과. “구현 먼저 → 나중에 테스트”를 기본으로 두지 않는다.

**과격한 line coverage TDD는 아니다.** 모든 줄·내부 헬퍼마다 테스트를 늘리지 않는다. 깨진 뒤 **다시 발견하기 비싼 계약**만 테스트한다.

작업 시작 시 [`AGENTS.md`](../../../AGENTS.md) 분류(복수 가능): `계약 변경` · `구현 변경` · `리팩터링` · `문서 변경` · `회귀 수정`.

---

## When to write or update tests

다음을 바꾸면 보통 **집중 테스트**를 추가하거나 기존 테스트를 **먼저** 갱신한다.

1. **공개 행위**: API 응답 형태, 함수 출력 계약, CLI, UI에 보이는 동작, 저장 데이터 형태, 직렬화·역직렬화 형식.
2. **도메인 계약**: DTO 필드, **enum / StrEnum / 상수**, 상태 전이, 소유·수명 규칙, 검증, 허용·금지 상태.
3. **데이터 변환**: 좌표 변환(`raw` ↔ Server X/Y), 정규화, 파싱, 인코딩·디코딩, import/export 경계, 스키마 마이그레이션, DB 매핑.
4. **제어 흐름 분기**: 성공/실패, 수락/거절, 커밋/롤백, 재시도·건너뛰기·폴백, 오류 분류, 가드·게이트·권한.
5. **영속·외부 경계**: DB, 파일 출력, POST/GET 페이로드, 백그라운드 잡, **replay payload**, **validation 결과**, 아티팩트·로그·metrics·NDJSON 계약.
6. **버그 수정**: 재현 **회귀 테스트**를 수정 전에 추가(불가능·비현실적이면 Caveman **Tests/Risks**에 이유).
7. **최근 취약 구역**: narrow corridor, route starvation, replay, coordinate boundary, UI replay sync 등 — 해당 **불변식** 테스트 최소 하나.

**외부 계약 변경 시 우선 대상** (테스트·enum 동시 갱신):

- DTO · enum · serialization
- coordinate conversion · `route_domain` · candidate pool
- replay payload · validation `issue_code` / `failure_reason` / `event_type`

---

## When not to add new tests

다음은 **새 테스트를 기본 추가하지 않고**, 관련 **기존 테스트·검증 명령**으로 충분할 수 있다.

- 포맷만, 주석만, 로그 문구만, CSS 색·간격 등 순수 시각 조정만.
- 비행위 변경인 비공개 심볼 리네임.
- **동작 계약이 동일한** 내부 리팩터·dead code 삭제(기존 테스트가 충분).
- 픽스처 정리 등 **프로덕션 동작 변화 없음**.

단, **동작 계약이 바뀌면** 테스트 갱신은 필수다.

---

## Required red-green-refactor workflow

1. 작업 분류 후, **가장 좁은 계약 테스트 하나**를 추가하거나 기존 테스트를 실패 상태로 갱신한다(red).
2. **해당 테스트 경로만** `pytest`로 green을 만든다.
3. 범위를 넓히기 전에 같은 사이클을 반복한다.
4. **큰 통합 테스트를 한 번에** 먼저 쓰지 않는다. 통합·E2E는 단위로 같은 불변식을 증명할 수 없을 때만.

---

## Domain invariants that must be test-protected

### Asteroid Lab (solver / optimization)

시맨틱 정본은 `documents/Algorithm/asteroid_lab_*.md` · [ADR-003](../../adr/ADR-003-final-validation-assertion-gate.md). glob 작업 시 [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc).

| Invariant | Canon | Representative tests / planned names |
|-----------|-------|----------------------------------------|
| Replay / NDJSON / artifact / metrics **output-only** — solver·algorithm **입력 금지** | [`asteroid_lab_09_replay_debug.md`](../../Algorithm/asteroid_lab_09_replay_debug.md) | `test_manual_snapshot_replay_not_used_as_algorithm_input_doc`; `test_lab_page_context_*`; `asteroid_lab_10` 체크리스트 |
| Candidate: **placement commit 금지**; 생성 → local geometry → immediate route probe → reachable만 normal pool | [`asteroid_lab_03_candidate_generator.md`](../../Algorithm/asteroid_lab_03_candidate_generator.md) | generator 인근 unit; Phase 체크리스트 |
| Incremental commit: **commit-time latest `route_domain` re-probe**; candidate phase reachable ≠ 최종 증명 | [`asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md) | `test_incremental_commit_reprobes_latest_route_domain` (문서 명시) |
| Validation: **read-only assert**; route·placement·topology **repair 금지** | [`asteroid_lab_08_validation.md`](../../Algorithm/asteroid_lab_08_validation.md), ADR-003 | validation read-only 체크리스트·pytest |
| Lab replay ↔ Optimization replay **dual-track**; frame index·event order·autoplay **암묵 동기화 금지** | `asteroid_lab_09` dual-track 절 | `test_lab_js_replay_wiring_smoke`; `test_lab_page_context_*` |
| `OptimizationInput` 이후 알고리즘 좌표는 **Server X/Y dense only**; raw 변환은 decode/import·final UI/export 경계만 | [`asteroid_lab_01_optimization_input.md`](../../Algorithm/asteroid_lab_01_optimization_input.md), [`asteroid_lab_00_overview.md`](../../Algorithm/asteroid_lab_00_overview.md) | `test_optimization_input.py`, `test_seed_route_domain_*` |
| `failure_reason` · `event_type` · `issue_code` 등 **enum/const** — 자유 문자열 금지 | Phase DTO 문서 | `test_invalid_event_type_rejected`; replay contract tests |
| 동일 seed **deterministic** (+ tie-break) | evolution 문서 | 필요 영역에 명시적 테스트 |
| **Regression fixture** — 버그 재발 시점에 추가 | 본 매뉴얼 | `tests/fixtures/asteroid_lab/`; corridor·starvation·replay·coord·UI sync 우선 |

표에 있는 **미구현** invariant 테스트는 이후 **구현 PR** 범위다. 본 문서는 요구사항·보호 대상만 고정한다.

### shapez_solver · Graph

- demand summary · source quantity · target output · materialized nodes · visual labels · operation nodes **구분** ([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) Solver/Graph).
- 연산 출력 → 연산 **직접 접합 금지**; 중간 도형 노드 경유.

---

## Test selection strategy

### 의미 있는 변경 시 최소 셋

(1) happy path (2) 중요한 실패 경로 (3) 불변식 또는 엣지 하나. 같은 계약을 여러 테스트가 중복 증명하지 않게 한다.

### 층위 선택

- 순수 로직 → **단위**
- 오케스트레이션 → **서비스/유스케이스**
- 경계 넘나듦 → **통합**
- 하위에서 계약을 증명할 수 없을 때만 **E2E**

느린 통합이 단위로 같은 불변식을 증명할 수 있으면 통합을 늘리지 않는다.

### 회귀·fixture

버그 수정마다: **무엇이 잘못됐는지**, **어느 불변식이 깨졌는지**, **어떤 테스트가 재발을 막는지**. 계약 커버가 비어 있던 버그는 **계약 소유자(도메인·직렬화·경계)** 근처에 테스트를 둔다.

**Regression fixture**는 재발 순간에 추가한다. 우선순위: narrow corridor, route starvation, replay payload, coordinate boundary, UI replay sync.

### 기존 테스트 재사용

추가 전에 동일 계약을 검증하는 테스트가 있는지 찾는다. 있으면 **확장**, 없을 때만 새 케이스. 구현 디테일에 묶인 이름은 피한다.

### 테스트 이름

**행위·불변식** 기준.

- 좋음: `test_rejects_invalid_payload_without_crashing`, `test_commit_failure_does_not_mutate_confirmed_state`
- 나쁨: `test_helper_line_42`, `test_new_code_path`

---

## Quality gate sequence

### 반복 (로컬 red-green)

에이전트·구현 중 **기본**. narrow `pytest` **먼저**, green 후 필요 시 좁은 lint.

```bash
python -m pytest <narrow path>
# green 후
python -m ruff check <paths>   # 또는 .
python -m mypy <paths>         # 선택
python -m black <paths>        # 로컬 포맷 수정 허용
```

### PR / 병합 / CI (full gate)

마감·머지·CI에서는 **전체** 검증. 순서:

```bash
python -m ruff check .
python -m black --check .
python -m mypy .
python -m pytest
```

- 로컬에서 포맷을 고칠 때는 `black .` 허용.
- PR·Caveman **Tests** 절에는 `black --check .` 결과를 기록한다.

[`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) · [`protocols/README.md`](../../../protocols/README.md) · 하네스 스킬은 위 **이중 모드**와 동일하게 맞춘다.

---

## Agent behavior rules

- 작업 시작 전 변경 범위를 **계약 / 구현 / 리팩터 / 문서 / 회귀**로 분류한다([`AGENTS.md`](../../../AGENTS.md)).
- **계약 변경** → 테스트·관련 문서 먼저.
- **회귀 수정** → 재현 테스트 먼저.
- **구현 변경** → 가장 좁은 단위 테스트부터.
- **UI 변경** → DOM·serialization·JS behavior 또는 fixture 회귀 먼저.
- **문서만** → pytest 필수 아님; 문서가 **코드 계약**을 바꾸면 Caveman **Contracts/Tests**에 테스트 계획을 적는다.
- 마감은 Caveman 6절만([`shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc)); **Contracts**에 불변식·테스트 추가/생략 이유, **Tests**에 실행 명령·결과.
- 동일 seed deterministic 영역은 **tie-break**까지 테스트로 고정한다.

---

## Forbidden shortcuts

에이전트·PR에서 **금지**:

- 실패를 **테스트 삭제·완화**만으로 green — 삭제/완화 시 이유와 **대체 invariant**를 문서화.
- replay · artifact · metrics · NDJSON을 **solver / algorithm 입력**으로 읽는 변경.
- `route_domain`을 여러 곳에서 직접 patch — **`RouteDomainSnapshotBuilder` 단일 소유** 유지.
- validation 단계에 **repair** (route 생성, placement·topology 수정).
- candidate enumeration·rim 스캔 순서를 **`Gene.commit_order` / commit 순서**로 사용.
- candidate phase reachable을 **최종 commit 증명**으로 사용(commit-time re-probe 필수).
- `OptimizationInput` 이후 알고리즘 계층에서 **raw ↔ server 좌표 재변환**.
- `failure_reason` · `event_type` · `issue_code` 등 **자유 문자열** 추가 — **enum/const + 테스트** 동시 갱신.
- Lab replay frame index와 Optimization replay frame index **암묵 동기화**.
- “큰 테스트 한 방”으로 TDD 시작.

---

## PR / commit checklist

[`documents/ai/checklist.md`](../checklist.md)와 함께 본다.

- [ ] 작업 분류(계약·구현·리팩터·문서·회귀)를 Caveman **Summary** 또는 **Contracts**에 명시.
- [ ] 계약·불변식·회귀 변경 시 테스트 추가·갱신(또는 생략 이유).
- [ ] Forbidden shortcuts 해당 없음 확인.
- [ ] 반복: narrow `pytest` green.
- [ ] PR/병합: [full gate](#pr--병합--ci-full-gate) 또는 생략 이유(**Tests/Risks**).
- [ ] Asteroid Lab이면 [`asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc) 표 준수.

**마감 전 (구현 PR)** — 다음 중 하나라도 해당하면 집중 테스트 확인(예외는 **Tests**에 이유):

- 공개 행위 · 직렬화 · 분기·게이트 · 외부 경계 · 버그 수정 · 취약 경로.

---

## 구간 실행

| 방식 | 예 |
|------|-----|
| 마커 | `-m unit`, `-m integration`, `-m shapez_solver`, `-m shapez_core`, `-m web`, `-m api`, `-m asteroid_lab` |
| 조합 | `-m "unit and shapez_core"` |
| 경로 | `python -m pytest tests/unit/shapez_solver/` · `python -m pytest tests/unit/asteroid_lab/` |
| 단일 파일·이름 필터 | `python -m pytest tests/unit/shapez_solver/test_bar.py` · `python -m pytest -k "substring"` |

프로덕션 모듈만 수정한 경우에는, 해당 동작을 검증하는 **기존** 테스트 모듈·디렉터리 경로를 인자로 주는 것이 기본이다.

마커 정의: `pytest.ini`. 경로 기반 자동 마커: `tests/conftest.py`.

## Recipe Graph 에디터 (Vitest)

와이어·입력 arity·carrier 정렬은 Python과 공유 픽스처로 검증한다.

```bash
npm --prefix frontend/recipe_graph_editor test
```

픽스처: `tests/fixtures/recipe_connection_rule_scenarios.json` · Python: `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`

## 린트 · 타입 · 포맷

로컬 수정:

```bash
ruff check .
mypy .
black .
```

PR·CI 검증은 [Quality gate sequence](#quality-gate-sequence) PR full gate를 따른다.

## 로케일(`ko`)

템플릿·지정 Python 경로의 gettext msgid를 반영하려면 루트에서 `python scripts/build_locale_ko.py`를 실행한다. PR/CI에서는 `python scripts/build_locale_ko.py --strict`로 `django_apps/web/views/public_pages.py`에 등장하는 리터럴 `_("...")`가 `scripts/build_locale_ko.py`의 `KO`에 모두 있는지 검증한다(`tests/unit/test_build_locale_ko_strict.py`).

## 완료 보고

에이전트·PR 설명은 [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/shapez2-core.mdc`](../../../.cursor/rules/shapez2-core.mdc) **Caveman 6절만** 쓴다. **6절 없이 완료 보고 금지.**

| Caveman 절 | 포함할 내용 |
|------------|-------------|
| **Summary** | 변경 요약·작업 분류 |
| **Files** | 변경 파일·이유 |
| **Contracts** | 계약·불변식; 테스트 추가/생략 이유 |
| **Tests** | narrow/full `pytest` · `ruff` · `mypy` · `black`/`black --check` — pass/fail/skipped |
| **Risks** | 미실행 명령·남은 위험 |
| **Next** | 이후 진행; 「완료」는 여기만 |

예외: Plan mode 본문 · 사용자 상세 설명 요청 · `documents/` 파일 본문. 상세: [`cursor_usage.md`](cursor_usage.md) §17.
