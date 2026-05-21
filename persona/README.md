# Persona Index

이 디렉터리는 팀 페르소나 카드를 보관한다. 각 카드는 역할, 담당 레이어, DO/DON'T, 검증 책임을 한 페이지로 정의한다.

## 역할 요약

| 페르소나 | 카드 | 주 담당 레이어 | 핵심 역할 |
|---|---|---|---|
| 시몬 | [simon.md](simon.md) | 전체 | 분배·조율, 완료 후 테스→렉스 |
| 도미닉 | [dominic.md](dominic.md) | `domain/` | 순수 규칙, 값 객체, 정책 |
| 유리 | [yuri.md](yuri.md) | `application/` | use case, DTO, port 추상화 |
| 아다 | [ada.md](ada.md) | `adapters/` | DTO 변환, 외부 시스템 연동 |
| 테스 | [tess.md](tess.md) | `tests/` | 테스트 작성·보강 |
| 렉스 | [rex.md](rex.md) | CI/검증 | pytest→ruff→mypy→black 체인 |
| 지나 | [gina-gui.md](gina-gui.md) | `interfaces/` | UI 화면, 사용자 상태 |
| 데니 | [denny.md](denny.md) | `django_apps/`, `config/` | Django 런타임, ORM, admin, importer |

## 페르소나 다이얼로그 규칙

페르소나는 구현(10단계 중 6번)에서만 대화 형식으로 등장한다. 상세는 [persona-dialogue.mdc](../.cursor/rules/persona-dialogue.mdc)와 [protocols/README.md](../protocols/README.md)를 본다.

## 레이어 의존 방향

**Phase 2 hexagonal (`src/shapez2_factory/`):**

```
interfaces ──► application (유리)
adapters   ──► application.ports (유리)
application──► domain (도미닉)
bootstrap  ──► 모든 레이어 (시몬 조립)
domain     ──► (없음)
```

**Django-first 런타임 (`django_apps/`, `config/`):** 데니 단일 소유. 앱 간 import는 [`documents/ai/manuals/django.md`](../documents/ai/manuals/django.md) 정본.
