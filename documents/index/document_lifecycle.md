# 문서 라이프사이클 정책

이 문서는 `documents/` 아래 문서의 상태와 읽기 우선순위를 고정한다. 목적은 AI agent가 폐기된 플랜이나 실험 문서를 정본처럼 읽어 아키텍처 drift를 만드는 일을 막는 것이다.

## 상태 enum

| 상태 | 의미 | 기본 context 포함 |
|------|------|------------------|
| `CANON` | 현재 시스템 계약의 정본. 구현·검증·리플레이 계약을 판단할 때 우선한다. | 예 |
| `ACTIVE` | 승인 대기 또는 진행 중인 작업 플랜. 정본을 바꾸려면 완료 후 `CANON` 또는 ADR에 반영한다. | 필요한 경우 |
| `COMPLETED` | 완료된 작업 기록. 왜 했는지와 검증 결과를 남기지만 살아있는 spec은 아니다. | 아니오 |
| `ARCHIVED` | 구버전 또는 보관 문서. 현재 설계 판단에 쓰지 않는다. | 아니오 |
| `RESEARCH` | 조사·실험·아이디어. 확정 전제나 구현 계약이 아니다. | 필요한 경우 |
| `REPORT` | 실행 보고·로그 분석·회귀 분석. 관측 결과이며 spec이 아니다. | 필요한 경우 |
| `SUPERSEDED` | 다른 문서가 대체한 문서. 상단에 `superseded_by`를 반드시 적는다. | 아니오 |

## 읽기 우선순위

1. `AGENTS.md`, `.cursor/rules/`, `documents/ai/manuals/`
2. `documents/index/document_inventory.md`에서 상태 확인
3. `CANON` 문서
4. 현재 작업의 `ACTIVE` 플랜
5. 필요한 `RESEARCH` 또는 `REPORT`
6. `COMPLETED`, `ARCHIVED`, `SUPERSEDED`는 역사 확인용으로만 읽는다

## 문서 헤더 권장 형식

새 문서에는 가능하면 본문 맨 위에 아래 메타 블록을 둔다.

```yaml
status: ACTIVE
owner: solver-architecture
last_reviewed: 2026-05-12
supersedes: []
superseded_by:
related_epics: []
```

## 운영 규칙

- competing spec은 허용하지 않는다. 같은 주제의 새 정본이 생기면 이전 문서는 `SUPERSEDED` 또는 `ARCHIVED`로 표시한다.
- `REPORT`와 `RESEARCH`는 정본 문구를 직접 담지 않는다. 정본으로 승격할 내용은 `CANON` 문서 또는 ADR에 반영한다.
- 완료된 플랜은 `COMPLETED`로 남기고, 다음 작업 큐에서 제거한다.
- 대규모 문서 이동은 별도 플랜에서 수행한다. 우선순위는 상태 표시와 inventory 정확도다.
