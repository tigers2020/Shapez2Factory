# Pass3 라우팅 전 low-ROI 번들 prune (P2)

## 목표

Pass2 스캔 완료 직후·premerge Pass3 루프 진입 전에, 기존 **P1 coarse ROI 게이트**(`_placement_p1_roi_gate_ok`, `roi_pass_key="pass2"`)를 통과하지 못한 채굴기 번들을 제거해 장거리 라우팅 부담을 줄인다.

## 동작

- 후보: 게이트 실패 extractor만.
- 정렬: `_bundle_placement_roi_score` 오름차순(낮을수록 먼저). marginal·ROI 계산 시 transport 키는 prune 시작 시점 스냅샷으로 고정.
- 상한: `MAX_PREPASS3_PRUNE_BUNDLES`.
- 제거: `_demolish_extractor_bundle` 재사용.
- 롤백: prune 직전 `MiningLayoutGridRollback.capture`. 각 제거 후 **anchor 기준** 도달성으로 trunk 단절을 검사한다 (`flood_fill_component(anchor, transport_only) == transport_only`, `transport_only = set(transport_cells) | {anchor}`). Shapez 그리드에서 cardinal 이웃이 비대칭이므로 `transport_is_connected`(집합의 임의 시작점) 대신 위 검사를 쓴다. 실패 시 `restore_into`로 전체 복구 후 중단.
- Trace: `prepass3_low_roi_bundle_removed`(선택), `prepass3_low_roi_prune_summary`.

## 비고

- 배치 후 extension 수는 `buildings` / `extension_parents`에서 extension·fluid_extension 타일만 센다.
- 플랜 파일 [`zero_extension_placement_gate_2026-05-09.md`](zero_extension_placement_gate_2026-05-09.md) P2는 본 문서를 정본으로 한다.
