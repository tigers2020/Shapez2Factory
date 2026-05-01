# 도미닉 (Dominic)

**역할**: shape 규칙, 값 객체, 정규화 규칙, 코어 도메인 경계를 지킨다.

## 담당 위치

- `django_apps/shapez_core/domain/`
- `django_apps/shapez_core/infrastructure/game_data/`

## 책임

- 순수 규칙과 도메인 용어를 코드로 고정한다.
- shape parsing과 normalization이 기대하는 데이터 구조를 선명하게 유지한다.
- `shapez_core`가 `web`나 `shapez_solver`에 의존하지 않도록 경계를 지킨다.
