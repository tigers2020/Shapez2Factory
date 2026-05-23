---
status: ARCHIVED
archived_date: 2026-05-22
archived_reason: Asteroid Lab optimization/solver pipeline removed from repository
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---

# asteroid_lab_optimization plans (ARCHIVED)

이 디렉터리의 `asteroid_lab_*.md` 는 **2026-05 이전 optimization 레이어** 설계·체크리스트 복사본이다.

- **현재 구현:** reconstruction + Lab replay만 유지 (`django_apps/asteroid_lab/reconstruction/`).
- **삭제됨:** candidate/route probe/commit/GA, `optimization/` 패키지, `solver_runtime_pipeline`.
- **활성 정본:** [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../../Algorithm/asteroid_lab_09_replay_timeline.md), strip-solver spec (링크 상단).

새 작업은 이 폴더를 수정하지 말고, reconstruction 또는 별도 spec에서 시작한다.

## Doc sweep (2026-05-23)

Each `asteroid_lab_*.md` file has a top-of-file banner pointing at **`documents/Algorithm/`** when a matching CANON doc exists.

- **PR-F:** Product code uses **island-local** `(x, y)` only; `server_coords.py` and dense server HUD are **removed**.
- Body text updated to island-local terminology (2026-05-23); banners still mention removed server frame for context.
