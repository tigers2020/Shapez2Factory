# 매뉴얼: Testing · 검증

## pytest (기본: 변경 범위만)

- **기본:** 이번에 손댄 코드·모듈과 직접 연결된 테스트만 실행한다. 예: 바꾼 파일 옆 `tests/unit/...`의 해당 모듈, 또는 `pytest path/to/test_file.py` / `pytest tests/unit/some_package/`.
- **전체 스위트** (`python -m pytest`, 루트에서 전부): 머지·릴리스·CI 대응·회귀가 넓게 의심될 때 등 **꼭 필요할 때만** 돌린다. 평소 에이전트/로컬 반복에는 전체를 기본으로 두지 않는다.
- 구간·마커는 아래 **구간 실행** 표를 따른다.

```bash
# 예: 작업 디렉터리 한정
python -m pytest tests/unit/asteroid_lab/test_example.py

# 전체 (필요 시만)
python -m pytest
```

## 계약 지향 테스트 (Contract-Oriented)

**핵심**: 공개 **행위**, **계약**, **불변식**, **회귀**를 검증한다. 모든 줄·작은 구현 단계마다 테스트를 늘리지 않는다.

### 테스트가 필요한 경우 (작성·갱신)

다음을 바꾸면 보통 **집중 테스트**를 추가하거나 기존 테스트를 확장한다.

1. **공개 행위**: API 응답 형태, 함수 출력 계약, CLI, UI에 보이는 동작, 저장 데이터 형태, 직렬화·역직렬화 형식.
2. **도메인 계약**: DTO 필드, enum 값, 상태 전이, 소유·수명 규칙, 검증, 허용·금지 상태.
3. **데이터 변환**: 좌표 변환, 정규화, 파싱, 인코딩·디코딩, import/export 경계, 스키마 마이그레이션, DB 매핑.
4. **제어 흐름 분기**: 성공/실패, 수락/거절, 커밋/롤백, 재시도·건너뛰기·폴백, 오류 분류, 가드·게이트·권한.
5. **영속·외부 경계**: DB 변경, 파일 출력, 캐시 키, 네트워크 요청/응답, POST/GET 페이로드, 백그라운드 잡 페이로드, 아티팩트·로그·리플레이·디버그 출력 계약.
6. **버그 수정**: 실제 버그면 수정 전에 실패하는 **회귀 테스트**를 두는 것을 원칙으로 한다(불가능하거나 비용이 비현실적이면 완료 보고에 이유를 적는다).
7. **최근 취약 구역**: 최근 깨졌거나 엣지가 많거나 추론이 어려운 코드를 건드리면, 해당 **불변식**을 짚는 테스트를 최소 하나 둔다.

### 테스트가 기본적으로 불필요한 변경 (선택)

다음은 **새 테스트를 기본 추가하지 않고**, 관련 **기존 테스트·검증 명령**을 돌리는 쪽으로 충분할 수 있다.

- 포맷만, 주석만, 로그 문구만, CSS 색·간격 등 순수 시각 조정만.
- 비행위 변경인 비공개 심볼 리네임.
- 이미 테스트로 덮인 내부 리팩터·dead code 삭제(동작 동일).
- 픽스처 정리 등 **프로덕션 동작 변화 없음**.

### 의미 있는 변경 시 최소 셋

가능하면 **짧은 조합**으로 끝낸다: (1) happy path (2) 중요한 실패 경로 (3) 불변식 또는 엣지 하나. 같은 계약을 여러 테스트가 중복 증명하지 않게 한다.

### 층위 선택

- 순수 로직 → **단위**
- 오케스트레이션 → **서비스/유스케이스 수준**
- 경계 넘나듦 → **통합**
- 하위에서 계약을 증명할 수 없을 때만 **E2E**

느린 통합이 단위로 같은 불변식을 증명할 수 있으면 통합을 늘리지 않는다.

### 회귀 규칙

버그 수정마다 답할 것: **무엇이 잘못됐는지**, **어느 불변식이 깨졌는지**, **어떤 테스트가 재발을 막는지**. 계약 커버가 비어 있어서 난 버그면 테스트는 **증상에 가까운 표면만**이 아니라 **계약 소유자(도메인·직렬화·경계)** 근처에 둔다.

### 기존 테스트 재사용

추가 전에 동일 계약을 이미 검증하는 테스트가 있는지 찾는다. 있으면 **확장**하고, 없을 때만 새 파일·새 케이스를 둔다. 구현 디테일(리팩터로 바뀌어도 행위는 같은 것)에 묶인 테스트는 피한다.

### 테스트 이름

**행위·불변식** 기준으로 짓는다.

- 좋음: `test_rejects_invalid_payload_without_crashing`, `test_commit_failure_does_not_mutate_confirmed_state`, `test_serializer_roundtrip_preserves_required_fields`
- 나쁨: `test_helper_line_42`, `test_new_code_path`, `test_private_variable_value`

### 마감 전 체크리스트

다음 중 하나라도 해당하면 집중 테스트를 추가·갱신했는지 확인한다(예외면 보고에 이유).

- 공개 행위를 바꿨는가?
- 데이터 형태·직렬화를 바꿨는가?
- 분기·게이트 결정을 바꿨는가?
- 영속·외부 경계를 바꿨는가?
- 버그를 고쳤는가?
- 취약·최근 깨진 경로를 건드렸는가?

**원칙**: 모든 줄을 테스트하지 않는다. 깨진 뒤 **다시 발견하기 비싼 계약**만 테스트한다.

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

```bash
ruff check .
mypy .
black .
```

CI에서는 `black --check .`로 포맷만 검사하는 경우가 있다.

## 로케일(`ko`)

템플릿·지정 Python 경로의 gettext msgid를 반영하려면 루트에서 `python scripts/build_locale_ko.py`를 실행한다. PR/CI에서는 `python scripts/build_locale_ko.py --strict`로 `django_apps/web/views/public_pages.py`에 등장하는 리터럴 `_("...")`가 `scripts/build_locale_ko.py`의 `KO`에 모두 있는지 검증한다(`tests/unit/test_build_locale_ko_strict.py`).

## 하네스 순서 (게이트)

**pytest:** 위 **기본(변경 범위만)** 을 먼저 적용한다. 루트에서 전체 `python -m pytest` 는 **머지·릴리스·광역 회귀·사용자 요청 등 꼭 필요할 때만**.

그다음 `ruff` → `mypy` → `black` 순을 원칙으로 한다(프로젝트·CI 정책이 다르면 그에 따름).

에이전트가 짧은 주기로 **전체** 스위트를 반복 실행하면 CI·로컬 대기 비용이 커진다. **파일·패키지·마커**로 좁히고, 필요할 때만 전체로 확장한다(배경: [`cursor_usage.md`](cursor_usage.md) §12).

## 완료 보고

에이전트·PR 설명은 [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/caveman-output.mdc`](../../../.cursor/rules/caveman-output.mdc) **Caveman 6절만** 쓴다. **6절 없이 완료 보고 금지.**

| Caveman 절 | 포함할 내용 |
|------------|-------------|
| **Summary** | 변경 요약 |
| **Files** | 변경 파일·이유 |
| **Contracts** | 계약·불변식; 테스트 추가/생략 이유 |
| **Tests** | `pytest` 경로·`ruff`·`mypy`·`black` — pass/fail/skipped; 전체 pytest 생략 이유 |
| **Risks** | 미실행 명령·남은 위험 |
| **Next** | 이후 진행; 「완료」는 여기만 |

예외: Plan mode 본문 · 사용자 상세 설명 요청 · `documents/` 파일 본문. 상세: [`cursor_usage.md`](cursor_usage.md) §17.
