# 문서 라이프사이클 정책

이 문서는 `documents/` 아래 문서의 상태와 읽기 우선순위를 고정한다. 목적은 오래된 계획·보고서가 현재 구현 계약처럼 읽혀 architecture drift를 만드는 일을 막는 것이다.

## 상태 enum

| 상태 | 의미 | 기본 context 포함 |
|------|------|------------------|
| `CANON` | 현재 시스템 계약의 정본. 구현·검증·리뷰에서 우선한다. | 예 |
| `ACTIVE` | 진행 중이거나 대기 중인 작업 계획. 완료 후 `CANON`, ADR, `COMPLETED`, `ARCHIVED` 중 하나로 정리한다. | 필요 시 |
| `RESEARCH` | 조사, 근거, 아이디어. 확정 계약이 아니다. | 필요 시 |
| `REPORT` | 실행 보고, 로그 분석, 감사 결과. 관측 결과이며 spec이 아니다. | 필요 시 |
| `COMPLETED` | 완료된 작업 기록. 검증 결과를 남기지만 살아 있는 spec은 아니다. | 아니오 |
| `ARCHIVED` | 오래되었거나 보관용인 문서. 현재 설계 판단에 쓰지 않는다. | 아니오 |
| `SUPERSEDED` | 다른 문서가 대체한 문서. 상단에 `superseded_by`를 남긴다. | 아니오 |

### Operational label: QUARANTINE

Inventory may label paths **QUARANTINE** for AI routing. Map to lifecycle `ARCHIVED` or `SUPERSEDED` and set `do_not_use_as_authority: true` in front matter. QUARANTINE docs are historical context only — not implementation authority.

## 읽기 우선순위

1. `AGENTS.md`, `.cursor/rules/`, `documents/ai/manuals/`
2. [`documents/index/document_inventory.md`](document_inventory.md)의 상태 확인
3. `CANON` 문서
4. 현재 작업의 `ACTIVE` 계획
5. 필요한 `RESEARCH` 또는 `REPORT`
6. `COMPLETED`, `ARCHIVED`, `SUPERSEDED`는 역사 확인용으로만 읽는다.

## 권장 문서 헤더

가능하면 문서 맨 위에 아래 메타 블록을 둔다.

```yaml
status: ACTIVE
owner: solver-architecture
last_reviewed: 2026-05-15
supersedes: []
superseded_by:
do_not_use_as_authority: false
related_epics: []
```

## 운영 규칙

- 같은 주제의 competing spec을 방치하지 않는다. 새 정본이 생기면 이전 문서는 `SUPERSEDED` 또는 `ARCHIVED`로 표시한다.
- `REPORT`와 `RESEARCH`는 정본 문구를 직접 대체하지 않는다. 확정 내용은 `CANON` 문서나 ADR에 반영한다.
- 완료된 계획은 `COMPLETED`로 표기하거나 archive index에 묶고, 다음 작업 문맥에서는 제거한다.
- 대규모 파일 이동은 별도 계획에서 진행한다. 우선순위 정리는 inventory와 archive index 갱신만으로도 충분하다.
- `documents/`는 이 체크아웃에서 git ignored일 수 있으므로 검증 시 `git status --ignored`와 직접 파일 읽기를 함께 사용한다.
