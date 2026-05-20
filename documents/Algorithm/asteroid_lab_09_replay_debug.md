# Phase 9 — Replay and Debug Artifact (DEPRECATED)

> **이 문서의 제품 정본은 [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) 로 이전되었다.**  
> 아래 dual-track·HUD-only optimization replay·별도 optimization controller 정책은 **obsolete**이다. 구현·리뷰·테스트 설계 시 **적용하지 않는다.**

---

## Deprecated policy (요약)

```text
Deprecated:
The previous dual-track Lab replay / Optimization replay policy is obsolete.
The product replay model is now a single Lab replay timeline.
Optimization events must be projected into 2D map frames, not displayed as HUD-only metadata.
```

| 폐기 문장 | 새 정본 |
|-----------|---------|
| Lab replay authoritative; Optimization metadata only | 하나의 Lab Replay Timeline |
| Run Solver는 Lab timeline을 바꾸지 않음 | 전 lifecycle이 동일 timeline에 append |
| Lab frame index ↔ Optimization frame index 연결 금지 | **하나의** global monotonic `frame_index` |
| 11A/11B optional overlay | 9C–9E 핵심 map projection·렌더 파이프라인 |

**새 North Star:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)

---

## 역사 보관 (dual-track 원문)

<details>
<summary>Frontend Dual-track Replay Policy (폐기 — 펼치기)</summary>

프론트엔드에서 **Lab replay**와 **Optimization replay**는 **이중 트랙(dual-track)**으로 취급했다.

- Lab: `lab_replay_frames_json` — map 렌더 권위
- Optimization: metadata only (10E까지); 11B에서 optional overlay
- `no implicit index sync` between Lab and Optimization frame indices
- 별도 `optimizationReplayFrameIndex`

**→ 제품 목표 변경으로 전부 폐기.** 상세: unified 정본 문서 「Deprecated」절.

</details>

---

## 역사 보관 (계측·스케일 — 여전히 참고 가능)

Sequence **13A·13B** 계측·HAR·`measure_json_sections`·Lab `full_map` 미캡 갭 등은 **페이로드 연구 근거**로 유효하다. 다만 불변 조건 문구 중 **「dual-track 유지」**는 replay timeline 정본으로 **대체**한다.

- **13 로드맵 정본:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)
- **13A·13B 상세 (본 파일 git 역사 또는 archive):** HAR ~22.6MB, `MAX_REPLAY_FRAMES`/`MAX_REPLAY_CELLS_PER_FRAME`, Lab vs optimization attribution

**13 시리즈에서 갱신할 불변 (2026-05-19):**

```text
Replay is output-only.                    # 유지
One unified product replay timeline.      # dual-track → 대체
No solver reads replay payload.           # 유지
```

---

## 마이그레이션 포인터

| 이전 개념 | 새 위치 |
|-----------|---------|
| `OptimizationReplayFrame` | `ReplayTimelineFrame` + `ReplayMapView` |
| `OptimizationReplayEventType` | `ReplayEventType` (value 문자열 호환 가능) |
| Sequence 11A projection | Sequence **9C** |
| Sequence 11B overlay layer | Sequence **9E** (단일 map, overlay는 `map_view.overlay_cells`) |
| Phase 9 invariant·테스트 | unified 정본 「Invariants」「Test Plan」 |

---

## 링크

- **정본:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)
- **개발 순서:** [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md)
- **런타임 배선:** [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md)
