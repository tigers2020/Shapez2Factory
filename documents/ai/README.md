# AI 작업 허브 (`documents/ai`)

루트 [`AGENTS.md`](../../AGENTS.md)는 **짧은 규칙 + 매뉴얼 라우팅**만 담고, 상세 절차·도메인 메모는 여기와 [`manuals/`](manuals/)에 둔다.

전체 `documents/` 폴더 맵·아카이브·플랜-리서치 짝: [`../README.md`](../README.md).

프로젝트 규칙상 본 디렉터리 Markdown 본문은 **한국어**로 쓴다.

## 파일

| 파일 | 용도 |
|------|------|
| [`current_plan.md`](current_plan.md) | 이번 세션/작업의 목표·범위·금지 사항 |
| [`context_notes.md`](context_notes.md) | 가정, 결정, 관련 이슈·경로 링크 |
| [`checklist.md`](checklist.md) | 단계별 완료 체크·품질 게이트 |
| [`manuals/cursor_usage.md`](manuals/cursor_usage.md) | Cursor·에이전트 워크플로 요약 |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | 상시 규칙·Caveman 6절 (§17 [`cursor_usage.md`](manuals/cursor_usage.md)) |

하네스 엔지니어링 4요소·10단계 파이프라인과의 매핑은 [`protocols/README.md`](../../protocols/README.md) 정본을 본다.

## 매뉴얼

[`manuals/`](manuals/) — 작업 유형별로 **필요한 챕터만** 연다 (전체를 매번 읽지 않는다).

| 매뉴얼 | 용도 |
|--------|------|
| [`manuals/testing.md`](manuals/testing.md) | **Contract-first TDD** · invariant · dual gate · PR 체크리스트 정본 |
| [`manuals/cursor_usage.md`](manuals/cursor_usage.md) | Cursor·컨텍스트·에이전트 네이티브 엔지니어링 |
| [`manuals/cursor_slim_setup.md`](manuals/cursor_slim_setup.md) | MCP·플러그인·User Rules slim 설정 가이드 |

## 런북

[`runbooks/`](runbooks/) — 반복 개발 절차.

| 런북 | 용도 |
|------|------|
| [`runbooks/dev_commands.md`](runbooks/dev_commands.md) | pytest·runserver·pycache·빌드 명령 빠른 참조 |

참고: [`AGENTS.md`](../../AGENTS.md) Manual Routing — 작업 유형별 매뉴얼 라우팅 표.
