---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: ko
related_docs:
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
---

# 규칙 모순 표 — 채굴기·확장기·설치

9열 표. PR-0 시드 + PR-1 `03`으로 층 A/B 반영 완료. PR-2 `04` 서술과 정합 유지; `needs-review`(throughput)만 프로그램 잔여.

## 열 정의

| 열 | 의미 |
|----|------|
| `topic` | 규칙 이름 |
| `legacy_claim` | 기존 문서 주장 |
| `normalized_db_evidence` | 층 A — ORM/dump 테이블·행 |
| `reflected_db_evidence` | 층 B — simulation/reflection 경로 |
| `code_invariant` | 층 C — 코드 심볼 |
| `test_evidence` | 층 D — pytest / enum |
| `confidence` | `high` / `medium` / `low` |
| `verdict` | `keep` / `rewrite` / `clarify` / `delete` / `needs-review` |
| `action` | 대상 파일·PR; `needs-review`일 때 **owner**·**gap** 포함 |

## 시드 행 (PR-0)

| topic | legacy_claim | normalized_db_evidence | reflected_db_evidence | code_invariant | test_evidence | confidence | verdict | action |
|-------|--------------|------------------------|----------------------|----------------|---------------|------------|---------|--------|
| 확장기 최대 0..3 | `asteroid_lab_02`: linear 0–3 extension | `03`: `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` + toolbar miner 그룹; blueprint `Layout_*` ≠ variant 테이블 | `03`: `ShapeMinerExtensionPlacementHelper`, `FluidMinerExtensionPlacementHelper`, `*ExtensionMetadata` | `throughput_factor_for_extension_count()` >3 거부; `GeneTemplate` occupied = extractor + extensions | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count`; `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` | high (C+D); medium (A Layout vs DB) | keep | `03` § Blueprint vs DB; `04` §1·§3 |
| 처리량 4/8/12/16 | `game_rules` CANON: 기본 ×4, 확장기당 +×4, 최대 ×16 | `03`: `buildingvariant`에 rate 컬럼 없음; A에 internal variant 2종 | `03`: `unknownproperty` miner metadata; `simulationsystem` 경로 TBD | `VALID_THROUGHPUT_FACTORS = {4,8,12,16}`; `throughput_factor_for_extension_count()` (`gene_template.py`) | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` | medium | needs-review | **owner:** asteroid-lab · **gap:** simulation_systems rate 경로 → 스칼라 import · **next:** game_data phase import 또는 deep path 감사 |
| rim-only | `asteroid_lab_03`: `RIM_ONLY` / rim-only가 설치 순서처럼 읽힘 | `03`: rim은 topology 유도(`rim_cells`), DB 테이블 아님 | — | `ExtractorPlacementPolicy.RIM_ONLY` (`candidate_dtos.py`); `candidate_generator.py` 기본값 — **앵커 ∈ rim_cells**, greedy 설치 아님 | `tests/unit/asteroid_lab/test_candidate_generator.py::test_candidate_generator_does_not_commit_placements`; `::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | clarify | `04` §핵심 구분·§3 반영; **gap:** `asteroid_lab_03` RESEARCH 본문 · owner: asteroid-lab |
| 후보 route probe | Phase 3 / overview: 풀 전 probe | — | — | `BundleCandidate.route_probe_result`는 생성 시점; **commit 증명 아님** | `tests/unit/asteroid_lab/test_candidate_generator.py::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | clarify | `04` §3–5; `asteroid_lab_04_route_probe.md` 링크 |
| commit 시점 reprobe | `asteroid_lab_07`: 최신 `route_domain`으로 reprobe | — | — | commit마다 `RouteDomainSnapshotBuilder.build_snapshot`; 후보 probe는 참고용 | `tests/unit/asteroid_lab/test_incremental_commit.py::test_incremental_commit_reprobes_latest_domain` | high | keep | strong-canon; `04` §5; `asteroid_lab_07` 유지 |
| replay 이벤트 어휘 | UI / lab JS — 문서 매핑 없음 | — | — | `ReplayEventType` (`replay_enums.py`): `candidate.generated`, `route_probe.succeeded`, `route.committed` 등 | `tests/unit/asteroid_lab/test_replay_timeline_dto.py`; `tests/unit/asteroid_lab/test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` (입력 금지만) | medium | clarify | `04` §6 phase/이벤트 표 반영; **gap:** JS per-control 라벨 · owner: asteroid-lab |
| replay 알고리즘 입력 금지 | `asteroid_lab_00` / 불변식 | — | — | metrics/NDJSON/replay frame은 optimization 입력 제외 | `tests/unit/asteroid_lab/test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` | high | keep | `asteroid_lab_09_replay_timeline.md` (ACTIVE); `asteroid_lab_12_runtime_replay_wiring.md`; **`09_replay_debug`는 ARCHIVED** |

## 허브 마감 체크리스트

- [x] `needs-review` 행마다 owner + evidence gap + next PR
- [x] 최종 `verdict`로 「DB에 없음」 사용 안 함
- [x] `00`–`04`·`README` 존재 (`03` DB xref, `04` 설치 가이드 포함)
- [x] `01`·`03`·`04` 핵심 주장 정합 (후보 ≠ 확정 설치)
- [ ] throughput `needs-review` 해소 (simulation rate 경로 또는 import)
- [x] `02` 조치 열 PR-1/PR-2 완료·부분 완료 반영 (2026-05-22)
