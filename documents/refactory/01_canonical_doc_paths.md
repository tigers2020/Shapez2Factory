# 목표: 정본 문서 경로 혼동 제거

## 배경

- 작업·감사 브리프에 `documents/ai/01_project_overview.md` 등 경로가 쓰이면 저장소에서 파일을 찾지 못하는 경우가 있다.
- 실제 Cursor 세션용 정본은 `documents/Algorithm/mining_solver_cursor_sessions/`에 있다.

## 현재 상태

- `documents/ai/`에는 `README.md`, `checklist.md` 등이 있으나 번호 체계 `01_`…`14_` 조각은 `Algorithm/mining_solver_cursor_sessions/`에만 존재한다.

## 목표 상태

- AI·인간 모두가 동일한 **한 줄 canonical base path**를 인용한다.
- 선택: (A) `documents/ai/`에 정본으로의 인덱스·링크만 두거나, (B) symlink/복사는 하지 않고 `documents/README.md`에 표로 고정한다.

## 작업 항목

1. `documents/README.md` 또는 `documents/ai/README.md`에 **정본 경로 표** 추가: `01`↔`14` 파일명 → 실제 경로.
2. AGENTS / 매뉴얼에서 “mining solver 세션 정본” 검색 시 위 표를 가리키도록 한 줄 보강(중복 서술 최소화).
3. (선택) 레거시 URL/문서에 `documents/ai/08_...` 형태가 남아 있으면 리다이렉트 문구만 추가.

## 검증

- 신규 기여자가 `01_project_overview`만 검색해도 1회 클릭으로 정본에 도달하는지.

## 위험

- 경로 이중 유지 시 한쪽만 갱신되는 드리프트 → **단일 인덱스만 정본**으로 둔다.

## 참고 정본

- `documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md` 등.
