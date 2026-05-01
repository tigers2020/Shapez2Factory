# persona

**shapez2Solver**는 [shapez 2](https://shapez2.com/)의 도형·공장·물류 규칙을 코드로 옮기는 프로젝트다. 게임 용어·시스템 요약은 [documents/research_shapez2_game_systems_2026-05-01.md](../documents/research_shapez2_game_systems_2026-05-01.md)를 우선한다.

Persona Dialogue: 요청을 `[시몬]`이 나누고, 레이어 담당이 한두 문장 브리핑한 뒤 구현한다. 검증은 `[테스]`·`[렉스]`(pytest → ruff → mypy → black) 순.

**거시 파이프라인 10단계 정본**은 [../protocols/README.md](../protocols/README.md)를 본다. 아래 표의 "파이프라인 단계"는 그 10단계 번호에 대응한다.

| 역할 | 주 담당 경로 | 파이프라인 단계 |
|------|----------------|-----------------|
| 시몬 | 분배·게이트·`bootstrap/` | 2·4·10 (+ 7 보조) |
| 도미닉 | `domain/` | 3·6 |
| 유리 | `application/` | 3·6·**7 (리뷰어 주도)** |
| 아다 | `adapters/` | 6 |
| 지나 | `interfaces/` (UI) | 6 |
| 테스 | `tests/` | 8 (QA) |
| 렉스 | 검증 파이프라인 | 9 (하네스) |

각주:

- **기획 듀오** = 도미닉 + 유리 (플랜 단계, 3번)
- **디렉터 검수** = 시몬 (2·4·10번)
- **리뷰어** = 유리 주도 + 시몬 보조 (7번, QA와 별개)
- **QA** = 테스 (8번)
- **하네스** = 렉스 (9번)

전체 표와 3단계 규칙은 [AGENTS.md](../AGENTS.md)를 본다. UI 화면 세부 카드는 [gina-gui.md](gina-gui.md).
