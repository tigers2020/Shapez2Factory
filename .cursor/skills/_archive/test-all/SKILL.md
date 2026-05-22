---
name: test-all
description: >-
  Runs pytest (optional, parallel via pytest-xdist), ruff, mypy, and Black;
  on failures, diagnoses and applies minimal code fixes then re-runs until
  pass or a documented stop. Use for /test-all, @test-all, or when the user
  wants lint, types, format, and tests with autonomous repair.
disable-model-invocation: true
---

# /test-all (테스트 · 린트 · 타입 · 포맷)

shapez2Solver 품질 검증을 한 흐름으로 돌리고, **실패 시 코드를 스스로 고쳐** 다시 돌린다. 전체 게이트 순서의 정본은 [AGENTS.md](../../../AGENTS.md)와 [@shapez2-harness](../shapez2-harness/SKILL.md) **렉스 순서**다.

## 명령

- **pytest(전체·병렬 권장)**: `python -m pytest -n auto --dist loadscope` — 워커가 수집된 테스트를 나눠 병렬 실행한다. `pytest-xdist`는 `pip install -e ".[dev]"`에 포함([`pyproject.toml`](../../../pyproject.toml)). Django DB 경로에서는 **`--dist loadscope`를 유지**한다([`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md)). **`-q` / `--quiet` / `--tb=no` 금지** (동 매뉴얼 § pytest 출력 규칙).
- **Makefile**: 루트 [`Makefile`](../../../Makefile)의 `make test-all`은 위와 동일하게 pytest에 `-n auto --dist loadscope`를 쓴다.
- `ruff check .` — 린트
- `mypy .` — 타입 체크
- `black .` (로컬) / `black --check .` (CI 포맷만 검사)

## 에이전트 실행 순서

1. **프로젝트 루트**에서 [AGENTS.md](../../../AGENTS.md) 순서 권장: **`python -m pytest -n auto --dist loadscope`** → `ruff check .` → `mypy .` → `black .` (또는 사용자가 **정적만**이면 pytest 생략). 단일 `python -m pytest`(워커 없음)는 기본으로 쓰지 않는다.
2. **Black**
   - 로컬에서 포맷까지 맞추려면: `black .`
   - CI처럼 **변경 없이 검사만**이면: `black --check .`

### pytest를 “청크”로 나눠 돌릴 때 (선택)

출력·메모리를 나누고 싶다면 **마커 기준 세 구간**으로 나눌 수 있다(`tests/conftest.py`·[`pytest.ini`](../../../pytest.ini)). 구간마다 내부 병렬은 동일하게 `-n auto --dist loadscope`를 붙인다.

- `python -m pytest -n auto --dist loadscope -m "unit and not slow"`
- `python -m pytest -n auto --dist loadscope -m "integration and not slow"`
- `python -m pytest -n auto --dist loadscope -m slow`

**주의**: Django+`--reuse-db` 환경에서는 **서로 다른 루트 pytest 프로세스를 동시에** 여러 개 띄우면 테스트 DB 충돌이 날 수 있다. 위 세 줄은 **순차 실행**(앞이 끝난 뒤 다음)을 기본으로 하고, **프로세스 간 병렬**이 아니라 **각 명령 안의 xdist 워커 병렬**로 속도를 낸다. 동시에 여러 pytest를 돌려야 하면 로컬 DB 분리·CI 매트릭스 등 별도 안전장치가 있을 때만 한다.

## 실패 시 자체 수정 (필수 동작)

테스트·린트·타입·포맷 중 **어느 단계든 실패하면**:

1. 출력(트레이스백, `ruff`/`mypy` 메시지)으로 원인을 특정한다.
2. [.cursor/rules/root.mdc](../../rules/root.mdc)에 맞게 **최소 수정**만 한다: 요청 범위·플랜 승인 게이트·솔버/도메인 **명시 요청 없는 동작 변경**은 하지 않는다. 고칠 수 있는 것은 예: 오타·import·타입 어노테이션·포맷·테스트 기대값과 구현의 명백한 불일치(회귀) 등.
3. 실패했던 명령(또는 전체 체인)을 **다시 실행**한다.
4. 통과할 때까지 2–3를 반복한다. **청크 순서**를 쓰는 경우 실패한 **해당 청크만** 다시 돌려도 된다. 같은 실패가 반복되거나 설계·스펙 판단이 필요하면 **수정 중단**, 관측 내용과 다음에 사람이 할 일을 보고한다.

## 완료 보고

- 각 명령의 최종 통과/실패(또는 미실행·이유).
- 자체 수정을 했다면: **어떤 파일을 왜** 고쳤는지 한 줄씩 요약.
- `black .`으로 파일이 바뀌었으면 **반드시** 별도로 명시한다.
- `black --check .`만 썼으면 “포맷 변경 없음” 또는 실패 라인을 요약한다.

## 참고

- 로컬에서 pytest만 줄이려면 [AGENTS.md](../../../AGENTS.md) **pytest 구간**, [`pytest.ini`](../../../pytest.ini), [`tests/conftest.py`](../../../tests/conftest.py), [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md)(`slow`·`make test-fast` 등).
