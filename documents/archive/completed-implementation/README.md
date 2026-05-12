# 아카이브: 구현 완료 플랜·리서치 (`completed-implementation/`)

`documents/plans/`·`documents/research/`에 있던 **실행 플랜과 조사 문서 1:1 쌍** 중, 코드베이스에 반영된 것으로 보는 항목을 **주제별 스템 폴더**로 옮겨 둔다. 활성·백로그·설계 전용 문서는 상위 [`../../plans/`](../plans/)·[`../../research/`](../research/)에 남긴다.

## 배치 규칙

| 항목 | 설명 |
|------|------|
| 경로 | `by-stem/<stem>/plan_<stem>.md`, 같은 폴더에 `research_<stem>.md` (있을 때만) |
| 스템 | 파일명에서 `plan_` 접두·`.md` 접미를 뺀 식별자 (`planner_service_split_2026-05-01` 등) |
| 상대 링크 | 이동 시 레포 루트 기준 경로는 `../../../../../django_apps/...` 형태로 조정됨 (`documents/plans/` 대비 3단계 추가) |
| 활성에 남긴 예외 | 다단계 로드맵·수평 레이아웃 단독 플랜·미래 DTO 설계 등: `factory_throughput`, `solver_graph_horizontal_layout_2026-05-01`, `solve_progress_rendering_2026-05-01` |

## 세션별 아카이브와의 관계

- [`../2026-05-completed/README.md`](../2026-05-completed/README.md): Recipe Graph Editor·Python 정리 등 **특정 일자 세션**에서 묶어 둔 사본.
- 본 디렉터리: **파일명 스템 기준**으로 플랜·리서치 쌍을 재배치한 보관함. `dead_code_cleanup_2026-05-01` 등 **이전 날짜 플랜**은 세션 아카이브의 `2026-05-04` 정본과 주제가 겹칠 수 있으니, 최종 실행 기준은 코드와 최신 플랜을 우선한다.

## 재현·추가 이동

초기 일괄 이동은 저장소 루트에서 `python scripts/archive_completed_plans.py` 로 수행했다. 스크립트의 `EXCLUDE_STEMS`를 조정한 뒤 다시 실행할 수 있다(이미 옮긴 파일이 없으면 실패하므로, 재실행 전에 Git 상태를 확인한다).

## 상위 인덱스

- [`../../README.md`](../../README.md) — `documents/` 전체 맵
- [`../README.md`](../README.md) — `archive/` 하위 요약

## 2026-05-12 점검

- 현재 `by-stem/`에는 구현 완료로 보관된 26개 스템 폴더가 있다.
- 2026-05-09 이후 asteroid mining layout 관련 플랜·리서치·알고리즘 스펙은 아직 활성 문서로 남겨 둔다. 완료 판정 후에만 이 디렉터리로 이동한다.
