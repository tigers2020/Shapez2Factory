# 리서치: 영상 기반 다단계 개발 구조 문서 반영

- 날짜: 2026-04-17
- 목적: 영상에서 설명한 `디렉터 → 기획 듀오 → 개발 → 리뷰 → QA → 하네스 → 위키` 흐름을 현재 문서 체계에 어떻게 매핑할지 정리

## 확인한 현재 문서

- `AGENTS.md`
- `protocols/README.md`
- `.cursor/rules/root.mdc`
- `.cursor/rules/cursor-usage.mdc`
- `.cursor/rules/persona-dialogue.mdc`
- `persona/README.md`
- `persona/simon.md`
- `persona/dominic.md`
- `persona/yuri.md`
- `persona/tess.md`
- `persona/rex.md`
- `persona/ada.md`
- `persona/gina-gui.md`

## 확인 결과

현재 저장소의 핵심 문서는 이미 아래 구조를 반영하고 있다.

1. `protocols/README.md`가 10단계 정본 역할을 수행한다.
2. `AGENTS.md`는 요약본으로 같은 흐름을 짧게 안내한다.
3. `persona-dialogue.mdc`는 Persona Dialogue 3단계를 파이프라인 6번(구현)에만 한정한다.
4. `persona/*`는 기존 캐릭터를 영상의 역할군에 매핑한다.
5. 리뷰어(7), QA(8), 하네스(9)가 서로 다른 축이라는 설명이 이미 분리되어 있다.

## 남아 있던 공백

문서 규칙은 `documents/`에 리서치/플랜/CURSOR_MEMO를 남기도록 요구하지만, 실제 폴더와 파일은 없었다.

이 공백 때문에 운영 규칙은 선언되어 있지만, 실제 게이트 산출물은 저장되지 않는 상태였다.

## 반영 방침

1. 기존 본문 구조는 유지한다.
2. 이번 변경을 위한 리서치 문서와 플랜 문서를 `documents/`에 생성한다.
3. 규칙 파일들이 참조하는 `documents/CURSOR_MEMO.md`를 생성한다.
4. 새 페르소나는 추가하지 않는다.

## 매핑 메모

| 영상 역할 | 저장소 매핑 |
|---|---|
| 디렉터 | 시몬 |
| 기획자 듀오 | 도미닉 + 유리 |
| 개발팀 | 도미닉 + 유리 + 아다 + 지나 |
| 리뷰어 | 유리 주도, 시몬 보조 |
| QA | 테스 |
| 하네스 | 렉스 |
| 위키/문서 동기화 | 시몬 클로징 + `documents/` |
