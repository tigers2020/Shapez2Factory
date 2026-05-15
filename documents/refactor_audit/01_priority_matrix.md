# Priority Matrix

| Priority | File | System | Issue | Risk | Recommended Action |
|---|---|---|---|---|---|
| P0 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py` | orchestration | end-to-end solve가 `solve_mining_layout_v2_stub`로 비어 있음 | 정본 STEP 0~10 파이프라인 부재 | `freeze` 후 새 orchestration seam 정의, 이후 `rewrite` |
| P0 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/merge_aware_router.py` | step4 routing | STEP 4 핵심 라우터가 skeleton | routing/merge/capacity/recovery 경로 공백 | `rewrite` |
| P0 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/trunk_seed.py` | step4 routing | trunk seed 생성이 skeleton | STEP 4 goal authority 부재 | `rewrite` |
| P0 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | validation | assertion gate가 skeleton leniency에 머묾 | validation corruption 고착 위험 | `rewrite` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/__init__.py` | domain boundary | domain public package가 placement/runtime를 재export | DTO 계층 오염, 순환 의존 유발 | `split`, `isolate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py` | dto/runtime boundary | DTO alias 모듈이 runtime `TraceEvent`를 직접 재export | DTO immutable layer와 runtime 관찰 계층 혼합 | `split`, `isolate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/runtime/trace_events.py` | runtime/domain boundary | runtime trace가 domain package를 통해 semantic validator를 끌어옴 | runtime/domain import knot 확대 | `split` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/corridor_probe.py` | routing boundary | routing이 placement helper 3개에 의존 | pass 책임 경계 붕괴 | `migrate`, `split` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/step4_corridor_recovery.py` | recovery boundary | routing 모듈이 placement recovery wrapper에 불과 | recovery 위치/소유권 불명확 | `migrate`, `deprecate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py` | replay coupling | 알고리즘이 replay event dict를 직접 생성 | output concern이 core placement에 침투 | `split`, `isolate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/corridor_opening.py` | recovery + trace coupling | recovery logic가 TraceEvent 생성과 rollback mutation을 동시 수행 | side effect chain 확대 | `split`, `isolate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/diagnostics.py` | diagnostics/UI boundary | read-only diagnostics가 preview timeline builder에 의존 | observability가 UI stack에 종속 | `split` |
| P1 | `django_apps/web/templates/web/asteroid_optimizer.html` | UI/replay integration | 프론트가 `solver_replay`/`solver_timeline`/`ui_frames` 계약을 계속 가정 | backend partial pipeline과 drift | `isolate`, `investigate-further` |
| P1 | `django_apps/shapez_asteroid/services/blueprint_map_summary.py` | duplicate preview stack | old map timeline/service가 여전히 살아 있음 | v2 preview와 shadow logic 경쟁 | `migrate`, `deprecate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_reconstruction.py` | duplicate reconstruction | old STEP1 reconstruction 경로가 남아 있음 | reconstruction semantic drift | `migrate`, `deprecate` |
| P1 | `django_apps/shapez_asteroid/services/asteroid_patch_interior.py` | duplicate geometry util | old interior fill util이 v2와 병존 | geometry logic shadow risk | `extract`, `migrate` |
| P2 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/preview_reconstruction_timeline.py` | UI adapter complexity | 1200+ line giant file, preview/painter/pass1 invocation 결합 | 유지보수 비용 과다 | `split` |
| P2 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/decode/existing_layout_analysis.py` | decode complexity | 649-line 단일 파일, 분석/이슈/힌트 조립 결합 | 테스트는 있으나 분해 비용 큼 | `split` |
| P2 | `tests/unit/web/test_asteroid_optimizer_page.py` | testing | 템플릿 문자열 smoke 위주 | 실제 replay/backend contract 회귀 미포착 | `test-only` |
| P3 | `django_apps/shapez_asteroid/services/copy_preview_debug_dump.py` | debug tooling | 출력 유틸 인코딩 주석/표현 정리 필요 | 기능 리스크는 낮음 | `cleanup`, `freeze` |
