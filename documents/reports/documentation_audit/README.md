# 문서 감사 보고서 인덱스

> 생성: 2026-05-15. 이 디렉터리는 문서 정리와 코드-문서 대조를 위한 감사 산출물이다. 정본 algorithm spec이 아니다.

## 읽는 순서

1. [`repository_map.md`](repository_map.md) — 코드/문서/생성물 위치 지도.
2. [`document_authority_matrix.md`](document_authority_matrix.md) — 문서 범주별 권위 체계.
3. [`document_inventory.md`](document_inventory.md) — `documents/` 파일별 1차 분류.
4. [`code_doc_crosscheck.md`](code_doc_crosscheck.md) — v2 코드와 canonical docs의 drift/미구현 대조.
5. [`obsolete_candidates.md`](obsolete_candidates.md) — 중복/오래된/충돌 후보.
6. [`cleanup_plan.md`](cleanup_plan.md) — 삭제 없이 적용 가능한 정리 계획.

## 권위 규칙

- 이 보고서는 `REPORT`다.
- 구현 판단은 `documents/Algorithm/mining_solver_cursor_sessions/README.md`와 01-14 canonical session docs가 우선한다.
- NDJSON, replay events, behavior artifact, solver_summary는 output evidence이며 algorithm input이 아니다.
