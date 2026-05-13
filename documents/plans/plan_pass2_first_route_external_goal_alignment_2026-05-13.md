# Pass2 첫 라우트 외부 goal 정렬 (2026-05-13)

## 목적

- `build_pass2_step4_aligned_routing_goals`가 STEP4 §9.2와 동일한 **외부 margin ∪ trunk_seed ∪ (외부 도달 가능한 기존 trunk)** 계약을 따르는지 감사한다.
- `final_goal_count == 0`이 **버그인지**, **기하·픽스처 한계(orphan 전부·margin 0)** 인지 구분한다.

## 정본·관련

- 구현: [`pass12_route_probe.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py) `build_pass2_step4_aligned_routing_goals`
- `is_external`·bbox: [`final_validation.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/validation/final_validation.py) `external_predicate_for_mining_map` / `_external_predicate_axis_bbox`
- Pass2 pack 셸: [`pass1_timeline_integration.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass1_timeline_integration.py) `Pass2RouteProbePack` (`is_external_shell_bbox` / `is_external_shell_margin`)
- 배경 플랜: [`plan_pass2_external_predicate_shell_alignment_2026-05-13.md`](plan_pass2_external_predicate_shell_alignment_2026-05-13.md)

## 비협상

- **orphan transport**를 goal로 승격하지 않는다 (`transport_cells_before` 전체 fallback 금지).
- `pass2_external_margin_diagnostic`는 관측·요약용; NDJSON을 알고리즘 입력으로 쓰지 않는다.

## 감사 판정 기준

| 상황 | 판정 |
|------|------|
| `goal_set_kind == "first_route"` 이고 `exterior_margin_cell_count > 0` 인데 `final_goal_count == 0` | **불일치 후보** → `raw_goal`·`trunk_seed_by_kind`·`universe_extra` 주입 경로 점검 후 최소 패치 |
| `exterior_margin_cell_count == 0` 이고 `pass2_external_margin_diagnostic.margin_generation_reason_if_zero`에 `is_external_never_true_on_sampled_neighbors` / `all_sampled_neighbors_inside_predicate_shell_or_x0` / `skipped_x0_only_universe` 등 | [외부 셸 정렬 플랜](plan_pass2_external_predicate_shell_alignment_2026-05-13.md) **ID C(관측 유지)** 에 해당할 수 있음 → 코드 변경 없이 **유효(기하)** 로 기록 가능 |
| `pass2_prior_transport_all_orphan is True` 이고 goal 비어 있음 | **의도된 계약** (orphan 미승격) |

## 검증

- [`test_external_predicate_equipment_shell_alignment.py`](../../tests/unit/shapez_asteroid/test_external_predicate_equipment_shell_alignment.py)
- [`test_step4_first_route_goal_set.py`](../../tests/unit/shapez_asteroid/test_step4_first_route_goal_set.py)

## 승인

- 본 문서는 구현·회귀 테스트와 함께 검토·합의 후 CANON 보강으로 승격할 수 있다.

## 구현 결과 (감사)

- `pass1_timeline_integration`에서 `Pass2RouteProbePack`에 `external_bbox_margin_for_mining_map` 기반 셸이 주입되며, `pass12_bundle_commit`이 goal 빌드 시 동일 인자를 전달한다.
- `final_goal_count == 0` 이 `margin==0`·`is_external` 샘플 불가·orphan-only 등 **문서화된 기하**인 경우 별도 predicate 변경 없이 유효로 본다.
