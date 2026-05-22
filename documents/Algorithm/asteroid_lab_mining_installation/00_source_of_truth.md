---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: ko
supersedes: []
related_docs:
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - docs/domain/asteroid_game_data_snapshot.md
---

# Asteroid Lab — 정본 우선순위 (채굴기·확장기·설치)

## 문서 허브 (한 폴더 모음)

여러 분산 문서·코드·DB 증거를 **`asteroid_lab_mining_installation/` 한 곳에서 진입**한다. 옛 파일을 전부 이곳으로 옮기지 않는다. 대신:

- **목차:** [`README.md`](README.md) — 읽기 순서 `00` → `04`
- **판정:** `01` 모순 표, `02` drift matrix
- **DB 사실:** `03` 교차 참조 (PR-1+)
- **서술:** `04` 설치 가이드 (PR-2)

이 폴더는 **채굴기·확장기·설치 흐름**에 대한 정본 재정렬(D2) **감사(audit) 허브**이다. `00`–`04`·`README`가 한 세트이며, 바깥 Phase RESEARCH 본문 일괄 수정은 허브 범위 밖이다. 미완료 항목은 `01`의 `needs-review`·`02` 조치 열에서 추적한다.

## 우선순위 스택

| 순위 | 소스 | 역할 |
|:--:|---|---|
| 1 | 최신 `game_data` import DB + dump 감사 | 분산된 **사실값** (miner 전용 단일 테이블 아님) |
| 2 | `django_apps/asteroid_lab/**` + 통과 pytest | Lab **런타임 동작** |
| 3 | `ACTIVE` / `CANON` (`game_rules`, `solver_runtime/*`, `asteroid_lab_09` 등) | **설계 계약** |
| 4 | `documents/Algorithm/asteroid_lab_0*` (`RESEARCH`) | 역사·배경 |
| 5 | replay / NDJSON / artifact | **관측 전용** — 알고리즘 입력 금지 |

## 충돌 규칙

```text
RESEARCH/REPORT vs 코드·테스트 → 코드가 아니라 02_doc_drift_matrix의 문서 행을 수정·삭제 대상으로 표시.
CANON 승격 → normalized_db 및/또는 code_invariant 및/또는 test_evidence 필요 (01 참고).
replay/metrics는 코드 불변식(층 C/D)을 덮어쓰지 않는다.
```

## 분산 DB 사실 (규범 문장)

```text
현재 game_data dump는 miner/extension/throughput을 단일 전용 정규화 테이블로 제공하지 않는다.
증거는 building geometry, toolbar placement, simulation/reflection row, Lab code invariant에 분산되어 있다.
```

## 증거 층 (A–E)

| 층 | 표 열 이름 | 예시 | 신뢰도 |
|----|------------|------|--------|
| A | `normalized_db_evidence` | `buildingvariant`, `buildinggroup`, `buildingfootprinttile`, `buildingconnector`, transport registry, `toolbar*` | geometry/registry에 높음 |
| B | `reflected_db_evidence` | `simulationsystem`, `unknownproperty`, `clrtyperegistryentry`, `simulation_systems` JSON 경로 | 중간 |
| C | `code_invariant` | `GeneTemplate`, `VALID_THROUGHPUT_FACTORS`, `throughput_factor_for_extension_count()`, `ExtractorPlacementPolicy.RIM_ONLY` | Lab 규칙에 높음 |
| D | `test_evidence` | pytest 경로, `ReplayEventType` wire 값 | 동작 고정에 높음 |
| E | `manual_gameplay_evidence` | A–D로 부족할 때만 플레이 규칙 | 낮음 — 명시적일 때만 |

**처리량:** 전용 rate 테이블이 없다는 것만으로 판정을 끝내지 않는다. B + C + [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) + D로 연결한다. 「DB에 없음 → BLOCKED」로 행을 닫지 않는다.

## 이름 규칙

`BuildingSnapshot` / `TransportRegistryEntry`는 **소비자 DTO**(`AsteroidGameDataSnapshot`)이며 Django ORM 모델명이 아니다. 층 A에는 dump/ORM 테이블명을 쓰고, DTO는 층 C 또는 adapter 메모에만 인용한다.

## PR별 파일 맵

| 파일 | PR |
|------|-----|
| `00_source_of_truth.md` | PR-0 |
| `01_rule_reconciliation.md` | PR-0 |
| `02_doc_drift_matrix.md` | PR-0 |
| `03_db_cross_reference.md` | PR-1 |
| `04_installation_guide.md` | PR-2 |

## 허브 완료 기준 (D2 프로그램)

- `01`의 `needs-review` 행마다 **owner**, **evidence gap**, **next PR** 명시
- C/D 증거 없이 `keep`를 CANON 대용으로 올리지 않음 (throughput은 `needs-review` 유지 가능)
- **`needs-review = 0`은 프로그램 전체 목표**이며, PR-0 단독 완료 조건은 아님
- `00`–`04`·`README` 메타 문구가 실제 파일 구성과 일치할 것
