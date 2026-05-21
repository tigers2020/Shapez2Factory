# Domain Manual

**소유**: 도미닉 (`persona/dominic.md`)

이 디렉터리는 프로젝트의 핵심 도메인 지식을 보관한다. AI와 사람이 함께 읽는 "진실의 단일 출처"다.

## 역할

- 도메인 용어, 불변식, 정책을 명문화한다.
- `src/{{package_name}}/domain/`의 코드가 이 문서를 따른다.
- 코드와 문서가 충돌하면 이 문서를 먼저 수정하고 코드를 뒤따르게 한다.

## 도메인 용어 (placeholder — 프로젝트 시작 시 채울 것)

| 용어 | 설명 | 참고 |
|---|---|---|
| {{TERM_1}} | {{TERM_1_DESC}} | — |
| {{TERM_2}} | {{TERM_2_DESC}} | — |
| {{TERM_3}} | {{TERM_3_DESC}} | — |

## 불변식 (placeholder)

> 시스템이 항상 만족해야 하는 조건을 여기에 기록한다.

- INV-1: (설명)
- INV-2: (설명)

## 파일 구성 규칙

- 파일 하나는 하나의 개념(엔티티/값 객체/정책)만 다룬다.
- 파일명은 `<개념명>.md` 형식으로 한다.
- 새 파일 추가 시 이 README의 목차를 갱신한다.

## 참조

- [Architecture](../architecture/README.md)
- [ADR](../adr/README.md)
