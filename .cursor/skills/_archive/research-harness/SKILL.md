---
name: research-harness
description: >-
  임의 주제를 웹·학술·커뮤니티에서 병렬 조사하고, 교차 검증 후 종합 보고서로 합친다.
  산출물은 RESEARCH 등 비정본 문서로 명시한다(AGENTS 문서 권위).
disable-model-invocation: true
---

# 리서치 하네스

**정본**: [AGENTS.md](../../../AGENTS.md) 문서 권위 — `RESEARCH`·`REPORT`는 **구현 계약이 아니다** ([document_lifecycle.md](../../../documents/index/document_lifecycle.md)). 프로젝트 절차 상 리서치 단계는 [protocols/README.md](../../../protocols/README.md) 1번·[기획과 코딩의 분리](../../../protocols/README.md)와 맞춘다.

**관계**: [shapez2-harness](../shapez2-harness/SKILL.md), [cursor-shapez2-harness](../cursor-shapez2-harness/SKILL.md). 도메인 근거가 shapez 2이면 [research_shapez2_game_systems](../../../documents/research/research_shapez2_game_systems_2026-05-01.md) 등 기존 CANON/RESEARCH와 **충돌 여부**를 통합 단계에서 적는다.

채팅에서 켜려면 `@research-harness` 또는 에이전트에 이 Skill을 포함한다.

## 병렬 조사 팀

동일 **질문서**(연구 질문, 범위·비범위, 성공 정의, 마감·언어, 금지: 예. 비밀·토큰을 검색어에 넣지 않음)를 세 축에 넘긴다. 초안은 **서로 인용하지 않고** 근거 링크만 단다.

| 태그 | 초점 | 도구·출처(예시) | 산출물(반드시) |
|------|------|-----------------|----------------|
| `[웹]` | 공식 문서, 릴리스 노트, 블로그, 뉴스 | `WebSearch`, `WebFetch`(URL 확정 시), 필요 시 Context7(MCP)로 라이브러리 문서 | 출처별 **요약 1~3문장**, URL, 접근일, 1차/2차 구분 |
| `[학술]` | 논문·표준·기술 보고서 | DOI/arXiv/학회·표준 기관, 인용 수·리트랙션 확인 | 인용 가능한 **서지 정보**, 핵심 주장·한계, 복제 여부 |
| `[커뮤니티]` | 이슈 트래커, 포럼, SNS, Q&A | GitHub Issues/Discussions, Stack Overflow, Reddit 등 | **사실** 주장 vs **의견·감정** 분리, 대표 링크, 확인 편향·노이즈 주의 |

## 교차 검증

| 태그 | 역할 |
|------|------|
| `[교차검증]` | 세 축 주장을 **대조표**로 정리: 합의·부분 합의·상충·증거 부족. 상충 시 **어느 근거가 1차인지**(공식·측정·동료 심사 등) 기준으로 권고 신뢰도를 매긴다(높음/중간/낮음/불명). |

`[교차검증]`은 새 증거를 **최소한만** 추가한다(상충 해소용 1차 출처 확인). 루프는 1회를 권장.

## 통합 보고

| 태그 | 역할 | 페르소나 정렬 |
|------|------|----------------|
| `[통합]` | 질문서에 대한 **최종 답** 초안: 조건부 결론, 미해결, 다음 액션(플랜/실험/구현 여부). | [시몬](../../../persona/simon.md)(범위·게이트) + 주제가 제품 도메인이면 [도미닉](../../../persona/dominic.md)(게임·도메인 정합) |

## 병렬 실행(권장)

- [ ] 질문서 1페이지: 가설, 용어 정의, **한국어 본문** 원칙([AGENTS.md](../../../AGENTS.md) `documents/` 규칙).
- [ ] **병렬**: 서브에이전트·백그라운드 **세 갈래**에 동일 질문서([cursor_usage.md](../../../documents/ai/manuals/cursor_usage.md) 컨텍스트 분리).
- [ ] 완료 후 `[교차검증]` → `[통합]` 순으로 **한 스레드**에서 실행해 맥락을 유지한다.

## 종합 보고서 목차(필수)

저장 권장: `documents/research/` (또는 팀 규칙 경로). 상단 메타에 `status: RESEARCH` ([document_lifecycle.md](../../../documents/index/document_lifecycle.md) 헤더 권장 형식).

```markdown
# 리서치: <질문 한 줄>

## 메타
- status: RESEARCH
- 질문·범위·조사 기간
- 참가 태그(웹/학술/커뮤니티/교차/통합)

## 요약 (비기술 5문장 이내)

## 근거 표
| 주장 | 웹 | 학술 | 커뮤니티 | 교차 판정 | 신뢰도 |

## 상충·공백
- ...

## 결론 (조건부) 및 권고
- 구현/플랜에 넘길 때 주의할 전제

## 참고 문헌·링크
- URL, 제목, 접근일
```

## 미니 체크리스트

**공통**

- [ ] 검색어·로그에 **비밀·개인정보**를 넣지 않는다.
- [ ] 날짜·버전을 명시(특히 빠르게 변하는 API·정책).
- [ ] 단일 익명 출처만으로 확정하지 않는다.

**`[웹]`**

- [ ] 공식 문서·릴리스를 우선; 블로그는 2차로 표시.

**`[학술]`**

- [ ] peer review 여부, 이해관계·스폰서 공개 여부(가능 시).

**`[커뮤니티]`**

- [ ] 업보트·감정적 표현과 **재현 단계**를 구분.

## 구현과의 경계

리서치 결론은 **플랜·승인** 없이 구현 근거로 단정하지 않는다([protocols/README.md](../../../protocols/README.md)).

## 참고

- 문서 인덱스: [document_inventory.md](../../../documents/index/document_inventory.md)
- MCP 선택 원칙: [mcp.mdc](../../rules/mcp.mdc)
