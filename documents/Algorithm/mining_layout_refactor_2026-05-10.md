# asteroid_mining_layout 패키지 리팩토링 (2026-05-10)

## 목표

- 거대 모듈(`reclaim_shadow`, `pass3_transport`, `solver_service`, `step4_merge_routing`)을 단계적으로 분할한다.
- `layout_kind`·라우팅 잡 수집 등 **중복 제거** 및 `step4` 비공개 심볼에 대한 **교차 import**를 줄인다.
- **동작·알고리즘 결과는 변경하지 않는다** (단위 테스트가 회귀 정본).

## 모듈 트리 (목표)

- `routing_cells.py` — `layout_kind`, `mineable_and_asteroid_coords`, `collect_routing_jobs`, `blocked_cells`, `want_role`, extractor 관련 `layout_kind` 집합 상수.
- `pass3_transport.py` — 공개 API·상수 **façade** (하위 `pass3_*.py`로 위임).
- `reclaim_shadow.py` — P4 공개 엔트리·상수 **façade** (하위 `reclaim_*.py`로 위임). **(3단계 완료 — 아래 §3 완료 기록 참고.)**
- `solver_timeline.py` — (선택) 타임라인/요약 헬퍼; `solver_service.py`는 오케스트레이션만 유지.

### 3단계 완료 기록 (`reclaim_shadow` 분할·최적화)

- **서브모듈** (`django_apps/shapez_asteroid/services/asteroid_mining_layout/`):
  - `reclaim_p4_bundle.py` — 번들 `_P4BundleEval`·정렬·선택.
  - `reclaim_map_ops.py` — 스냅샷/재구성, provisional row, overlap, transport·mineable·budget 헬퍼.
  - `reclaim_route_metrics.py` — `_path_additional_route_cost`, 존 trace, incremental transport 집계.
  - `reclaim_soft_replace.py` — §14.3 soft-corridor 원자 치환.
  - `reclaim_shadow_scan.py` — `_evaluate_one_shadow_bundle`, `reclaim_shadow_scan_core_after_pass3`, `run_reclaim_shadow_scan_after_pass3`.
  - `reclaim_shadow_commit.py` — B1/B2, `run_p4_reclaim_loop_after_pass3`, `p4_reclaim_shadow_placeholder`.
- **`reclaim_shadow.py`**: 상수·`reclaim_corridors` 재export + 위 모듈 재export 유지. unittest가 `patch("...reclaim_shadow.…")` 하는 대상(`placement_stub_route_probe_path`, `_path_additional_route_cost`, `validate_final_mining_layout` 등)은 façade에 노출하고, 스캔·커밋·소프트 치환 쪽은 호출 시 `reclaim_shadow`를 통해 위임(패치가 적용되도록).
- **핫패스 최적화 (동작·trace 계약 유지)**:
  - `_path_additional_route_cost`에서 `route_tree`를 경로 스텝 루프 밖에서 1회 계산.
  - 스캔당 `_P4ShadowScanShared`로 `cells`/`probe_buildings`/`transport_cells`/stub 집합/`anchor_cell`/`existing_transport` 등 1회 구성 후 번들 평가에 재사용; `anchor_cell is None`이면 무거운 셀 구축 없이 동일 거부 eval만 생성.
- **검증**: `tests/unit/shapez_asteroid/test_reclaim_shadow.py`, `test_pass3_transport.py` 및 `ruff` / `mypy` / `black --check` 통과 기준으로 회귀 확인.

## 유지할 공개 import 경로

- 패키지 `django_apps.shapez_asteroid.services.asteroid_mining_layout`의 `__init__.py` 재export.
- `pass3_transport`, `reclaim_shadow`, `solver_service`, `step4_merge_routing` 등 기존 모듈 경로.
- 테스트에서 `pass3_transport`의 상수·`_p3e3_*` 등으로 import하는 심볼은 façade에서 재export.

## 검증

```text
python -m pytest tests/unit/shapez_asteroid/
ruff check .
mypy .
black --check .
```

(로컬은 AGENTS.md의 pytest 구간으로 축소 가능.)

## 단계

1. `routing_cells` 추출 및 `_layout_kind` 중복 제거.
2. `pass3_transport` 서브모듈 분할 + façade.
3. `reclaim_shadow` 서브모듈 분할 + façade. **(완료 — §「3단계 완료 기록」참고.)**
4. `solver_service` 슬림화(선택): `solver_timeline.py`.
5. 전 구간 검증.
