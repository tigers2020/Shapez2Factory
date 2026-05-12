# Pass12 stub-route recovery (NEAR_TRANSPORT) — 구현 결정 메모

날짜: 2026-05-11

## 목적

`NO_MATCHING_STUB` 보존 드롭 중 `nearest_same_kind_transport_hops`가 작은 경우, 출력 인접 `inferred`/빈 칸에 stub를 materialize하고 same-kind 트렁크까지 제한 BFS로 연결한 뒤 `scratch.transport_cells`에만 반영한다 (`ROUTED_CONFIRMED`).

## 상한 구분

- `MAX_PASS12_RECOVERY_BFS_HOPS`(8): `recoverability_class`의 NEAR_TRANSPORT 밴드 등 **분류·트레이스**에 사용.
- `MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS`(6): **stub-route recovery 시도 eligibility** — 더 좁게 둘 수 있음.

## goal / 신규 transport / route 길이

- `goal_transport_cells` = merged 맵의 `role == want_wr` + 시도 시점 `scratch.transport_cells`(실패 프로브는 scratch를 변이하지 않으므로 shadow 경로 없음).
- `new_transport_cells` = `path_cells - existing_same_kind - scratch.transport_cells`(stub이 path에 포함되면 신규 1칸 이상으로 계산).
- `route_len_edges` = `len(path_cells) - 1`; 상수 `MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN`은 edge 상한.

## 플래그

- `SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY`: 기본 **False**. relaxed(`SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY`)와 분리.

## 비범위 (MVP)

extension carve, Pass3/P4 튜닝, 외부-only `probe_stub_to_external` 대체.
