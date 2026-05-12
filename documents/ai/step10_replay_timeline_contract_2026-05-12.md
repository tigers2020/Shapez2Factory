# STEP10 리플레이·타임라인 UI 계약 (2026-05-12)

본문은 [AGENTS.md](../../AGENTS.md) `documents/` 작성 언어(한국어)에 따른다.

## 용어: 타임라인 행 vs `computation_cycle` vs `cc_tick`

| 개념 | 출처 | 의미 |
|------|------|------|
| **통합 타임라인 인덱스** | `map_timeline` + `solver_timeline` 순서 합성 | Decode 후 슬라이더의 “전체 스텝 N” 중 몇 번째인지. |
| **Solver replay 슬라이더** | `solver_replay.ui_frames` (행 수 = `solver_timeline` 길이) | 맵 빌드 스텝 **이후** 구간만 별도 1…M 표시. 첫 틱 **1**은 첫 **`ui_frames` 행**이다. |
| **`timeline_row_id` / `solver_timeline[i].id`** | 서버 `solver_timeline` | 고정 프레임 식별자. 첫 solver 행은 계약상 `solver_init` ([`SOLVER_FRAME_INIT`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/foundation/constants.py)). |
| **`replay.events[].computation_cycle`** | `solver_replay.events` | 이벤트 로그의 단조 증가 인덱스(정규화 후 1…n). **타임라인 한 행과 1:1이 아님.** |
| **`ui_frames[].computation_cycle_start` / `_end`** | [solver_replay_frames.py](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_frames.py) | 해당 타임라인 행에 매핑된 이벤트들의 `computation_cycle` 최소·최대. |
| **`computation_cycle_ui_tick_*`** | 동일 | stride=10일 때 UI 틱 버킷(증거·라벨용). **알고리즘 규칙으로 사용하지 않는다.** |

**주의:** 사용자가 말하는 “cycle 1”이 **첫 리플레이 슬라이더 틱**이면, 그것은 **`computation_cycle == 1` 스냅샷이 아니라 `solver_init` 행**일 수 있다. 혼동 방지를 위해 UI에 `timeline_frame_id`를 병기한다([asteroid_optimizer.html](../../django_apps/web/templates/web/asteroid_optimizer.html) `replayPosEl`).

## 데이터 소스 (정본)

- **맵 픽셀(벨트/파이프/점유):** 각 스텝의 `mining_map` 배열. 후보 코리도는 `mining_map`에 섞지 않고, 옵션 오버레이로만 그린다(`protected_corridors`, 체크박스).
- **메타·이벤트 슬라이스:** `ui_frames[].event_indices` / `overlay_event_indices` → `solver_replay.events` 참조. 검증·로그용 evidence.

## 브라우저 디버그 페이로드

- 켜기: `localStorage.setItem("am_replay_frame_debug","1")` 또는 `window.AM_SOLVER_REPLAY_FRAME_DEBUG = true`.
- `renderPlot` 직전 `console.debug("[am replay frame]", …)`에 `timeline_row_id`, `computation_cycle_start/end`, 이벤트 슬라이스 요약, bbox echo 등이 포함된다.

## Bbox·요약 필드 (UI `effectiveSummaryForPlot`와의 관계) — 감사 결과

- **구현:** [asteroid_optimizer.html](../../django_apps/web/templates/web/asteroid_optimizer.html)의 `effectiveSummaryForPlot`는 `summary`에 `x_min`/`x_max`/`y_min`/`y_max`가 있으면 그대로 쓰고, 없으면 **`mining_map` 좌표로 bbox를 유도**한다.
- **서버:** `solver_init` 등 초기 행의 `summary`는 [finalize.py](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py)에서 `pass12_status_fields` 등만 붙이며 **좌표 bbox가 비어 있는 경우가 많다**. 이 경우 UI 유도 bbox는 “현재 프레임 셀만” 기준이라, **외곽 dashed(맵 빌드 단계·별도 summary)와 시각적으로 어긋날 수 있다.**
- **결론:** bbox 불일치가 의심되면 (1) 맵 빌드 마지막 스텝의 `summary` bbox, (2) 동일 디코드의 `solver_init` `mining_map` 유도 bbox를 나란히 비교한다. **서버가 solver 타임라인 summary에 bbox를 채우는 변경**은 계약·회귀 영향이 있으므로 **별도 플랜·승인** 후 진행한다.

## `ui_frames` 주기 경계 검증

- **소스:** `ui_frames[i].computation_cycle_start` / `_end`는 `event_indices`로 묶인 `solver_replay.events[j].computation_cycle`의 최소·최대다 ([solver_replay_frames.py](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_frames.py) `build_replay_ui_frames`).
- **검증 API:** 같은 모듈의 `verify_replay_ui_frames_computation_cycles(events, ui_frames)`가 인덱스 범위·정수 `computation_cycle`·min/max 일치를 깨는 경우 문자열 목록으로 반환한다. `build_solver_replay_snapshot` 직후 단위 테스트에서 호출한다.

## 코리도(티어) vs 트렁크 히트맵(committed)

| 레이어 | 데이터 | 의미 |
|--------|--------|------|
| **보호 코리도** | `ui_frames[].protected_corridors` (`hard` / `soft` / `candidate`) | `routing_state` 기반 **후보·예약 셀** (replay `corridor_*` 이벤트와 합침). candidate는 probe·완화 구간에 가깝다. |
| **트렁크 히트맵** | `ui_frames[].trunk_load_overlay` (`trunk_edge_load_observation` 요약) | STEP4가 **이미 칠한 경로**의 간선 통과 횟수 관측. 페이로드에 `trunk_observation_layer: "committed_step4_routes"`로 스코프를 명시한다. |

히트맵은 코리도 candidate와 **동일 집합이 아니다**; UI에서 체크박스·범례를 분리해 해석한다.

## Partial / skipped UI

- `solver_step4_routing` + `step4_committed === false`: Pass3/P4 최적화 수치·P4 오버레이·`route_replaced` 시각화를 “최종 최적화”처럼 보이지 않게 억제.
- `solver_pass3_transport` + Pass3 skip 계열: 동일 패턴으로 확장.
- `solver_validate` + `step4_partial_failure`: 동일.

## 검증 명령

```text
python -m pytest tests/unit/shapez_asteroid/test_copy_preview.py -q
```

전체 게이트는 [AGENTS.md](../../AGENTS.md) 품질 절차를 따른다.
