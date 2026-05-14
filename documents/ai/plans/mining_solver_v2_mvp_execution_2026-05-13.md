---
status: ACTIVE
owner: solver-architecture
last_reviewed: 2026-05-13
supersedes: []
superseded_by:
related_epics: [mining-solver-v2-greenfield]
---

# 소행성 채굴 솔버 v2 MVP — 실행 계획 (리뷰 반영본)

**정본(알고리즘·DTO)**: [`documents/Algorithm/mining_solver_cursor_sessions/`](../../Algorithm/mining_solver_cursor_sessions/) README 및 01–08, 13, 14.

**본 문서 역할**: Cursor 계획 파일과 별개로, **구현 게이트·PR 순서·todo 순서**를 저장한다. 알고리즘 세부는 위 CANON 문서가 이긴다.

---

## 1. 리뷰에서 반영한 보정 요약

1. **`asteroid_mining_layout` → `asteroid_mining_layout_old` 리네임은 맨 마지막 단독 PR**  
   v2 스캐폴드·domain(DTO/Enum/FSM)·**import 경계 테스트 green** 이후에만 수행한다. 그 전에는 **v1 경로·패키지명을 건드리지 않는다**(CI/import 폭발와 v2 버그 분리).
2. **초기 과추상화 완화**: `ports/`는 MVP에서 **`SolveRequest` / `SolveResult` 수준만** 두거나, 처음엔 `solver.py` 인자·반환으로 통일하고 web 연동 시점에 포트 파일을 추가해도 된다. 빈 래퍼·미사용 포트 파일 금지.
3. **패키지 폴더**: 초기에는 `dto/`·`pipeline/`·`step04/` 다중 분할보다 아래 **단순 트리**를 권장한다. STEP4가 커지면 `routing/` 내부 모듈만 쪼갠다.
4. **`QUARANTINED_UNROUTED` (MVP 고정 정책)**  
   - STEP4에서 라우트 실패 시 **일시적으로** `QUARANTINED_UNROUTED`를 기록할 수 있다(trace·FSM 일관성).  
   - Recovery가 MVP 범위 밖이므로, **동일 STEP4 세션 안에서 즉시 `ROLLED_BACK`으로 해소**하고 최종 후보 집합에서 제거한다.  
   - **STEP9 진입 시 `QUARANTINED_UNROUTED` placement는 0건**(assertion 실패).  
   즉 quarantine은 **디버그·중간 상태**이며, “남겨 두는” 종료 상태가 아니다.
5. **출력물**: `logs` / `replay_events` / `solver_summary` / NDJSON은 **증거 전용**이며 알고리즘 입력으로 읽지 않는다.
6. **비목표(MVP)**: Pass3, Reclaim, Recovery, protected corridor 교체, rated capacity·overflow 하드 검증( **`trunk_load` 누적 합 trace만** ).

---

## 2. 권장 패키지 트리 (v2 초기)

```text
django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/
  __init__.py
  domain/
    coords.py          # Coord, BBox
    enums.py           # TransportKind, PlacementCommitState, SourceKind, SolverTermination
    dto.py             # SolverRunContext 부분집합, Pass 결과, ExistingLayout 계열(또는 dto.py가 길어지면 existing_layout.py로만 분리)
    fsm.py             # placement 상태 전이 헬퍼(선택)
  foundation/
    geometry.py        # 4-neighbor CC 등 순수 기하 (문서 §E.12)
    grid.py            # shapez_grid 규약 얇은 래퍼
    dijkstra.py        # §3.5 셀 비용 정본 (RouteZone §11과 동일 경로에서 혼용 금지)
  steps/
    step00_decode.py
    step00_5_existing_layout.py
    step01_reconstruction.py
    step02_pass1.py
    step03_pass2.py
    step04_routing.py  # 커지면 steps/step04_*.py로 분리
    step09_validation.py
    step10_replay.py
  ports.py             # 선택: SolveRequest, SolveResult만 (디렉터리 ports/ 대신 단일 모듈로 시작 가능)
  solver.py            # orchestrator
```

**금지**: `asteroid_mining_layout_v2`가 `django_apps.shapez_asteroid.services.asteroid_mining_layout` (v1) **내부 모듈을 import**하는 것. fixture는 **복사본**만 사용.

---

## 3. 수정된 Todo 순서 (구현 시)

| 순서 | id | 내용 |
|:--:|---|---|
| 1 | doc-gate | 본 ACTIVE 플랜·`current_plan` 링크·inventory 반영·사람 승인 |
| 2 | scaffold-v2 | `asteroid_mining_layout_v2` 패키지 + `solver.py` 스텁 + 빈 `steps/` |
| 3 | (domain) | `domain/`에 Enum·DTO·Coord 일괄 (기능 없이 타입만 가능) |
| 4 | tests-per-step (선행) | **import 경계**: v2 트리가 v1을 import하지 않는다는 테스트(grep/AST 또는 `importlib` 로드 규칙) |
| 5 | impl-pipeline | STEP0→0.5→1→2→3→4→9→10 순 구현 |
| 6 | flag-web | 환경 플래그 + web 팩토리 분기 + `solver_engine` |
| 7 | replay-output | NDJSON 등은 adapter 출력만, 역피드 금지 |
| 8 | rename-v1-old | **v2 MVP 최소 파이프라인 + 경계 테스트 green 뒤**, `asteroid_mining_layout` → `asteroid_mining_layout_old` 물리 이동 및 import 전역 치환을 **단독 PR**로 수행 |

`rename-v1-old`는 **scaffold 직후가 아니라** 표에서 맨 마지막으로 고정한다.

---

## 4. PR 시퀀스 (명시)

```text
PR-A  documents: 본 파일 + inventory (+ 필요 시 current_plan 한 줄 링크)
PR-B  v2 scaffold + domain 타입 + import-boundary 테스트만 (v1 무변경)
PR-C  STEP0 / 0.5 / 1 (순차 또는 묶음)
PR-D  Pass1 / Pass2
PR-E  STEP4 routing MVP + quarantine→즉시 rollback 정책
PR-F  STEP9 assertion-only + STEP10 최소 스냅샷
PR-G  orchestrator 완성 + feature flag + web adapter
PR-H  v1 → asteroid_mining_layout_old 리네임 전용 (대규모 치환, 동작 동일 목표)
PR-I  v2 MVP cross-check 리포트(선택, REPORT)
```

---

## 5. 위험·완화 (갱신)

| 위험 | 완화 |
|------|------|
| v1 리네임을 이르게 하면 v2 디버깅과 import 회귀가 섞임 | **PR-H를 반드시 PR-G 이후**로 둔다. |
| `domain/` vs `dto/` 이중 구조 혼란 | 초기에는 **`domain/` 단일**; 파일이 커질 때만 분리. |
| STEP4에서 quarantine 잔류 | 코드 리뷰 체크리스트: **STEP4 함수 종료 시** `placement_commit_by_id`에 `QUARANTINED_UNROUTED` 없음. |
| 문서 §9.3 capacity-aware vs MVP trunk_load만 | 구현 주석 + trace에 `capacity_mode: aggregate_only` 명시. |

---

## 6. v2 전환 조건 (플래그 ON 권장 전)

- `pytest` 구간: `tests/unit/shapez_asteroid/mining_layout_v2/` + 경계 테스트 green
- `ruff` / `mypy` / `black --check` 프로젝트 규칙 준수
- STEP9가 **새 route 생성 없이** hard invariant만 검사함을 테스트로 고정

---

## 7. 이전 Cursor 계획과의 차이

- Cursor `.cursor/plans/mining_solver_v2_mvp_*.plan.md`에 있던 **“승인 후 PR 순서: … 3. `_old` 리네임 … 4. 파이프라인”** 순서는 **폐기**하고, 본 문서 **§3·§4**를 따른다.
- `ports/` 다중 파일 제안은 **축소**한다.

---

## 8. 다음 액션 (구현 담당)

**Sequence 01**: PR-B — `asteroid_mining_layout_v2` 스캐폴드만, v1 미터치.
