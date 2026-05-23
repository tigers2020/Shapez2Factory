# Asteroid Lab — 채굴기·확장기·설치 (문서 허브)

채굴기·확장기·Lab 설치 흐름 관련 내용을 **이 폴더 한곳**에서 다룬다. 기존 Phase 문서는 원래 위치에 두고, 여기는 **진입점**(목차 + 판정 + DB 사실 + 서술)이다.

## 읽기 순서

| # | 파일 | PR | 역할 |
|---|------|-----|------|
| 1 | [`00_source_of_truth.md`](00_source_of_truth.md) | PR-0 | 정본 우선순위, 증거 층 A–E, 충돌 규칙 |
| 2 | [`01_rule_reconciliation.md`](01_rule_reconciliation.md) | PR-0 → PR-1 | 규칙별 판정표(9열) |
| 3 | [`02_doc_drift_matrix.md`](02_doc_drift_matrix.md) | PR-0 | 기존 문서 카탈로그 + drift 유형 + 조치 |
| 4 | [`03_db_cross_reference.md`](03_db_cross_reference.md) | PR-1 | 정규화 DB + dump 반영 행 목록 |
| 5 | [`04_installation_guide.md`](04_installation_guide.md) | PR-2 | 끝까지 읽는 설치 흐름 (후보 ≠ 확정) — **작성 완료** |
| 6 | [`05_island_extractor_variants.md`](05_island_extractor_variants.md) | — | 섬 추출기 기본 블루프린트 (balance / omni / fluid) copy 정본 |

**상위 목차:** [`documents/Algorithm/README.md`](../README.md) 6번 항목.

**설계 스펙:** [`docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md`](../../../docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md)

## 이 폴더 밖에 두는 것

| 위치 | 옮기지 않고 링크만 하는 이유 |
|------|---------------------------|
| `documents/Algorithm/asteroid_lab_0*` | Phase RESEARCH 계약 |
| `documents/game_rules/shapez2_asteroid_space_transport_throughput.md` | 처리량 CANON |
| `django_apps/asteroid_lab/` | 런타임 코드·테스트 |
| `docs/domain/asteroid_game_data_snapshot.md` | 소비자 DTO 계약 |

Phase 본문을 여기에 통째로 복사하지 않는다. **판정**과 **링크**는 `01` / `02`에서 갱신한다.

## 허브 상태 (2026-05-23)

- **완료:** PR-0–PR-2 (`00`–`04`); `05` 섬 추출기 copy 카탈로그 + `IslandExtractorBlueprint` 시드
- **이전:** PR-0–PR-2 (`00`–`04`); 메타 정합 갱신 (`00`·`01`·`02`)
- **잔여:** `01` throughput `needs-review` (simulation rate → import); `asteroid_lab_03` RESEARCH 본문(선택); Lab JS per-control replay 라벨
