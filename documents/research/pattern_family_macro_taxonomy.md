# 패턴 패밀리·매크로 분류 (솔버 카탈로그)

## 정본 소스

기본 카탈로그(6종 `PatternFamily` + 내장 매크로 2종 및 스텝)의 **정본은 Django 데이터 마이그레이션**이다.

- 파일: [`django_apps/shapez_solver/migrations/0006_seed_pattern_catalog.py`](django_apps/shapez_solver/migrations/0006_seed_pattern_catalog.py)
- `PatternFamily`는 `code` 기준 `update_or_create`; 레거시 패밀리 `code="abcc-batch"`가 있으면 같은 행을 `pair-plus-singles`로 바꾸거나, `pair-plus-singles`와 중복 시 매크로 FK를 옮긴 뒤 레거시 행을 삭제한다.
- `MacroRecipe.code`는 `abcc-batch`(매크로 코드)·`swap-rotate-swap-checker` 그대로 유지한다.
- 역방향(`migrate` 롤백)은 **noop** — 롤백 시 카탈로그 행은 자동 삭제하지 않는다.

[`django_apps/shapez_solver/fixtures/pattern_catalog_seed.json`](django_apps/shapez_solver/fixtures/pattern_catalog_seed.json)은 마이그레이션과 동일 스냅샷을 유지하는 **참고·데모용** 복사본으로 두며, 애플리케이션 동작의 단일 진실은 아니다.

## 요약

한 레이어의 네 사분면을 **집합 분할(set partition)** 관점에서 보면, 서로 다른 등가류의 최대 개수는 Bell 수 \(B_4 = 15\)이다. 매크로 설계에서는 회전·반사 등가까지 묶어 **실무적으로 6축**으로 두는 것이 안정적이다.

DB의 `PatternFamily`는 새 enum을 두지 않고, **`signature` 문자열 + `allow_rotation` / `allow_reflection`** 으로 표현한다.

## 시그니처 문자열 (`PatternFamily.signature`)

런타임 계산은 `django_apps.shapez_solver.services.pattern_classifier.pattern_signature`이다.

- 사분면 순서(SW → NW → NE → SE, 레이어 문자열과 동일)대로 토큰을 읽으며, **처음 등장하는 순서**에 `A`, `B`, `C`, … 를 부여한다.
- 따라서 이 문자열은 Bell 분할의 **정규형(canonical) 이름이 아니라**, “왼쪽부터 읽은 라벨링”이다.

동일한 분할 타입이라도 사분면 배치에 따라 **`AABC`와 `ABCC`처럼 다른 문자열**이 나올 수 있다.

## 카탈로그 조회 방식

`PatternCatalogRepository.find_macro_candidates`는 `MacroRecipe`를 **`family__signature`와 요청 시그니처가 완전히 같은 행**만 고른다.

그래서 시드에서 2+1+1 클래스의 대표만 `AABC`로 바꾸면, `pattern_signature`가 여전히 `ABCC`를 내는 목표에 대해 **매크로 후보가 매칭되지 않는 회귀**가 생긴다.

현재 구현에서는 다음이 바인딩되어 있다.

- `macro_strategy_registry`의 `ABCC_BATCH` 분기는 `pattern_signature(...) == "ABCC"`를 전제로 한다.
- AB half + CC half 기하를 기준으로 한 시드 스텝 출력 슬롯도 `ABCC` 표기를 사용한다.

**결론**: 2+1+1 클래스의 DB 대표 문자열은 **`ABCC`를 유지**하고, Bell 진행형으로 보기 좋은 `AABC`는 문서·설명용으로만 구분한다. 향후 전부 `AABC`로 통일하려면 `pattern_signature` 정규화와 저장소 조회·매크로 분기 문자열을 **한 번에** 바꿔야 한다.

## 6축(실무 패밀리)과 시드 `code`

| 의미 | 권장 `code` | 예시 `signature` |
|------|-------------|------------------|
| 전부 동일 | `full-source` | `AAAA` |
| 3+1 | `single-different` | `AAAB` |
| 인접 2+2 | `half-split` | `AABB` |
| 교차 2+2 | `checker` | `ABAB` |
| 2+1+1 | `pair-plus-singles` | `ABCC` (대표; 동클래스에 `AABC` 가능) |
| 전부 서로 다름 | `full-mixed` | `ABCD` |

위 6종 패밀리는 마이그레이션으로 보장된다. 매크로 레시피가 없는 패밀리는 활성만 두거나 추후 매크로를 붙인다.

## `allow_rotation` / `allow_reflection`

패턴 랩·매크로 단계에서 동치 확장을 허용할지 나타낸다. 상세 규칙은 패턴 랩 서비스와 솔버 후보 선택 로직을 따른다.

## 참고

사분면당 원자(도형·색 등) 개수를 \(36^4\) 형태로 세는 것은 **상한**에 가깝고, 빈 사분면·게임 규칙상 불가 조합을 빼면 실제 가능 조합은 더 작다. 패밀리 분류 안정화 후 별도 문서에서 검산한다.
