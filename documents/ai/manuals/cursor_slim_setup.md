# Cursor Slim 설정 가이드

shapez2 Factory Planner 작업 시 Cursor 전역 설정을 최소화해 컨텍스트 부담을 줄이는 체크리스트다.  
저장소 규칙(`shapez2-core.mdc`·`AGENTS.md`)은 자동 적용되므로, **전역 설정은 중복을 제거**하는 데 집중한다.

## MCP 서버 — 권장 구성

### 기본 ON (shapez2 일상 개발)

| MCP 서버 | 용도 | 비고 |
|----------|------|------|
| **context7** (하나만) | 라이브러리·프레임워크 최신 문서 | plugin·user 버전 중복이면 **하나를 비활성** |
| **github** | PR·이슈 조회 | 필요 시에만 켜도 무방 |
| **playwright** | UI·그래프 시각 검증 | solver UI 또는 프론트 작업 시 |

### 기본 OFF 권장 (필요할 때만 켜기)

| MCP 서버 | 이유 |
|----------|------|
| Linear | 이슈 관리 안 쓰면 부담만 |
| Figma | 디자인 작업 없으면 불필요 |
| Vercel | 배포 작업 없으면 불필요 |
| Google Developer Knowledge | 로컬 grep·context7로 대체 가능 |
| sequential-thinking | 단계 추론은 모델 자체로 충분 |
| GitLens MCP | 로컬 `git` 명령으로 충분한 경우 |
| Serena | 심볼 탐색 안 쓰면 OFF; 사용 시 `initial_instructions` 먼저 |
| duplicate context7 | plugin·user 중 하나만 유지 |

설정 위치: **Cursor → Settings → MCP** 또는 프로젝트 `.cursor/mcp.json`.  
최소 템플릿: [`.cursor/mcp.json.example`](../../../.cursor/mcp.json.example)

## 플러그인 — Redis Development

이 레포는 Redis를 사용하지 않는다.  
→ **Cursor Settings → Extensions/Plugins**에서 `redis-development` 플러그인을 **이 워크스페이스에서 비활성**하거나 OFF.  
이유: 플러그인이 주입하는 Redis 규칙 다수가 매 턴 컨텍스트에 실린다.

## User Rules (전역)

`AGENTS.md`·`shapez2-core.mdc`와 **중복되는 장문 규칙은 제거**한다.  
이 레포에 대한 전역 User Rule은 아래 한 줄로 충분하다:

```
shapez2Factory: AGENTS.md + .cursor/rules/shapez2-core.mdc 를 따른다.
```

긴 workflow·테스트·레이어 규칙을 User Rules에 넣으면 매 대화에 이중 로드된다.

## 글로벌 Caveman 스킬

`C:\Users\<user>\.agents\skills\caveman\` 등의 전역 caveman 스킬은  
이 레포에서 자동 트리거되지 않도록 한다.  
이유: 프로젝트 정본은 `shapez2-core.mdc` Caveman 6절이다.  
방법: 해당 스킬의 `disable-model-invocation: true` 설정 또는 trigger 키워드를 프로젝트 전용으로 한정.

## 컨텍스트 절약 습관

| 습관 | 설명 |
|------|------|
| 작업 단위 스레드 분리 | 주제가 바뀌면 새 채팅으로 시작 |
| `@` 범위 최소화 | 필요한 파일·폴더만, 코드베이스 전체 금지 |
| 서브에이전트 분리 | 광역 탐색은 별도 컨텍스트에서 돌리고 결과만 가져옴 |
| 긴 대화 재시작 | 동작 이상 시 세션 갈아엎기 |

상세: [`cursor_usage.md`](cursor_usage.md) §4·§6·§14

## 관련 문서

- 상시 규칙: [shapez2-core.mdc](../../../.cursor/rules/shapez2-core.mdc)
- 운영 계약: [AGENTS.md](../../../AGENTS.md)
- MCP 스키마 확인: `mcps/<server>/tools/` 폴더
- 개발 명령: [dev_commands.md](../runbooks/dev_commands.md)
