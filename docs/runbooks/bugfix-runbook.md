# Bug Fix Runbook

이 runbook은 버그 수정 작업의 표준 절차다. `bug-fix` 스킬(`.cursor/skills/bug-fix/SKILL.md`)과 함께 사용한다.

## 전제 조건

- 버그를 재현할 수 있는 입력 또는 로그가 있어야 한다.
- 재현 불가 시 `BLOCKED: missing context`로 중단하고 추가 정보를 요청한다.

## 절차

### 1. 재현 확인

```bash
# 재현 테스트 또는 직접 실행
pytest tests/ -k "<관련 테스트 이름>" -v
```

재현 테스트가 없으면 먼저 작성한다 (`write-tests` 스킬 참조).

### 2. Root cause 분석

1. 스택 트레이스 / 로그에서 최초 오류 발생 위치를 찾는다.
2. 해당 레이어(domain / application / adapters / interfaces)를 확인한다.
3. 레이어 경계 위반이 있으면 `docs/architecture/README.md`와 대조한다.
4. 가설을 1~2개로 압축한다.

### 3. 수정

- smallest diff 원칙: 최소한의 변경으로 원인을 제거한다.
- domain 규칙 변경이면 도미닉에게, application이면 유리에게, adapter이면 아다에게 확인한다.
- 설계 결정이 바뀌면 `docs/adr/`에 ADR을 추가한다.

### 4. 검증

```bash
python -m pytest            # 전체 (-q / --quiet / --tb=no 금지)
ruff check .                # 린트
mypy django_apps config src # 타입 검사
black --check .             # 포맷
```

모든 단계 통과 후에만 완료 선언한다.

### 5. 완료 보고

```
Summary: (버그 원인 한 줄)
Files changed:
Commands run: python -m pytest / ruff check . / mypy django_apps config src / black --check .
Validation: (통과/실패 상세)
Risks / follow-up:
Docs updated:
```

## 자주 하는 실수

| 실수 | 올바른 행동 |
|---|---|
| 테스트 없이 수정 | 먼저 재현 테스트 작성 |
| domain에 I/O 추가 | adapter/port로 분리 |
| 검증 전 완료 선언 | 4단계 검증 후 선언 |
| 회귀 테스트 미추가 | 동일 유형 회귀 막는 테스트 1개 이상 추가 |

## 참조

- [bug-fix skill](../../.cursor/skills/bug-fix/SKILL.md)
- [Architecture](../architecture/README.md)
- [AGENTS.md](../../AGENTS.md)
