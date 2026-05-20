# Architecture Decision Records (ADR)

이 디렉터리는 프로젝트의 중요한 아키텍처 결정을 기록한다.

## 목적

- 왜 이 결정을 내렸는지 미래의 팀에게 설명한다.
- 되돌릴 수 없거나 비용이 높은 결정을 추적한다.
- 대안을 검토한 흔적을 남긴다.

## 작성 기준

다음 중 하나 이상에 해당하면 ADR을 작성한다.

- 레이어 경계 또는 의존 방향이 바뀌는 결정
- 외부 라이브러리/프레임워크 도입 또는 교체
- 데이터 저장 방식, 직렬화 형식 변경
- 테스트 전략 또는 검증 방식의 구조적 변경
- 성능/안정성 트레이드오프가 있는 결정

## 파일 명명

```
ADR-NNNN-<짧은-제목>.md
```

예: `ADR-0001-port-protocol-over-abc.md`

## 상태 목록

| 번호 | 제목 | 상태 |
|---|---|---|
| 0000 | Template | — |

## 상태 값

- `proposed` — 검토 중
- `accepted` — 채택됨
- `deprecated` — 더 이상 유효하지 않음
- `superseded` — 다른 ADR로 대체됨

## 참조

- [ADR template](ADR-0000-template.md)
- [Architecture](../architecture/README.md)
