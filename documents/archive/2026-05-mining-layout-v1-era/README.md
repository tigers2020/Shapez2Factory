# 채굴 레이아웃 v1 패키지 시대 문서 아카이브 (2026-05)

## 목적

- 런타임에서 제거된 Python 패키지 경로 `django_apps/shapez_asteroid/services/asteroid_mining_layout/`(v1) 및 PR-H 이후 `asteroid_mining_layout_v1_deprecated/` 스텁 시대의 **플랜·감사·보조 알고리즘 메모**를 한곳에 모았다.
- **현재 구현 권위**: `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/`.
- **알고리즘·DTO 정본(CANON)**: `documents/Algorithm/mining_solver_cursor_sessions/` — 본 아카이브 작업에서 **수정·이동하지 않았다**.

## 상태

| 상태   | 의미                                      |
|--------|-------------------------------------------|
| ARCHIVED | 설계 판단·구현 계약의 정본으로 쓰지 않는다. |

[`documents/index/document_lifecycle.md`](../../index/document_lifecycle.md)의 `ARCHIVED` 정의를 따른다.

## 하위 폴더

| 경로 | 출처 |
|------|------|
| [`refactory/`](refactory/) | 기존 `documents/refactory/` 전체 |
| [`algorithm-root/`](algorithm-root/) | 기존 `documents/Algorithm/*.md` 루트(세션 폴더 제외) |
| [`plans/`](plans/) | `documents/plans/` 중 v1 경로 참조 문서 |
| [`research/`](research/) | `documents/research/` 중 동일 |
| [`reports/`](reports/) | `documents/reports/` 중 동일 |
| [`ai-plans/`](ai-plans/) | `documents/ai/plans/` 중 동일 |
| [`ai/`](ai/) | `documents/ai/`에서 이관한 단발 문서(예: Step10 계약 스냅샷) |

## 운영 큐

- [`documents/ai/current_plan.md`](../../ai/current_plan.md), [`documents/ai/checklist.md`](../../ai/checklist.md)는 저장소에 **유지**하며, PR-H 완료 한 줄·본 README 링크로 정리한다.

## 이관일

- 2026-05-14 (PR-H 런타임 v1 차단 이후 문서 정리)
