# 매뉴얼: Refactor · 정리

## 목표

동작을 바꾸지 않거나, 요청된 동작만 바꾼다.

## 원칙 ([`.cursor/rules/root.mdc`](../../../.cursor/rules/root.mdc), [`karpathy-guidelines.mdc`](../../../.cursor/rules/karpathy-guidelines.mdc))

- 요청과 무관한 파일은 건드리지 않는다.
- 본인 변경으로 생긴 미사용 import·변수만 제거한다. **기존 dead code는 요청 없이 삭제하지 않는다.**
- 추측·요청 밖 추상화·「불가능 시나리오」 방어 코드를 추가하지 않는다.

## 넓은 재작성

명시 요청·플랜·승인 없이 넓은 재작성을 하지 않는다 ([`AGENTS.md`](../../../AGENTS.md)).

## 삭제

미사용 증명 없이 레거시 모듈을 삭제하지 않는다.

## 검증

[`testing.md`](testing.md)의 최소 명령을 통과시키거나 미실행 사유를 남긴다.

## 관련

- PR·범위 단위 **종합 리뷰**(아키텍처·보안·성능·스타일 병렬 감사 후 통합 리포트): [`.cursor/skills/code-review-harness/SKILL.md`](../../../.cursor/skills/code-review-harness/SKILL.md) (`@code-review-harness`)
