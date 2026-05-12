# CURSOR_MEMO

## 2026-04-17

- 영상 기반 다단계 개발 파이프라인 문서 정합화 작업에서 `documents/` 폴더를 실제 운영 산출물 저장소로 생성했다.
- 현재 정본은 `protocols/README.md`이고, `AGENTS.md` / `.cursor/rules/*` / `persona/*`는 이를 요약·참조한다.
- Persona Dialogue 3단계는 파이프라인 6번(구현)에서만 적용한다.
- 리뷰어(7) / QA(8) / 하네스(9)는 반드시 분리해서 다룬다.

## 2026-05-03

- 반복 패턴은 `prebuilt_pattern_registry`에서 패턴 정의와 템플릿 정의를 분리하되, 솔버 결과는 기존 `SolvedRecipe` 내부 노드로 확장한다.

## 2026-05-06

- Cursor 토큰·컨텍스트 매뉴얼(`documents/ai/manuals/cursor_usage.md`) 추가 및 `AGENTS.md` 라우팅·`cursor-usage.mdc` 참조 연결.
