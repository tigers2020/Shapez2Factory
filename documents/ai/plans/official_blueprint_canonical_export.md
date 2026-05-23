# 공식 Shapez2 blueprint export (dense 앵커)

**상태**: ACTIVE (구현 반영됨)  
**관련 코드**: [`django_apps/asteroid_lab/adapters/blueprint_canonical_export.py`](../../django_apps/asteroid_lab/adapters/blueprint_canonical_export.py), [`django_apps/asteroid_lab/snapshots/blueprint_equivalence.py`](../../django_apps/asteroid_lab/snapshots/blueprint_equivalence.py)

## 목적

랩 내부 레이아웃(`V:1`, raw `X,Y`)을 게임 export 형태(`V`/`BP.BinaryVersion` 1137, `Icon`, 기본값 생략)로 바꾼 뒤, **dense 열이 붙은** 좌표를 낸다. 바이트 고정 골든(`H4sIAH8kC2oA/…` 남쪽 3-ext spread)은 **회귀 정본에서 제외**했다.

## 버그 (폐기한 앵커)

```text
export_x = raw_x - (extractor_x + 1)   # west raw -1 → game X=-3, miner X=-1 → dense {-3,-1,0} 갭
export_y = raw_y - (extractor_y + 2)
```

| 구분 | 복사 접두 | dense(export `X`) | 증상 |
|------|-----------|-------------------|------|
| **버그** | `H4sIAAAAAAACC…` | `{-3,-1,0}` | -2 열 공백, Admin·게임에서 한 칸 벌어짐 |
| **정상** | `H4sIAMsrC2oA/…` | `{-1,0}` (+ pipe `X=1`) | 인접 |

픽스처: `tests/fixtures/asteroid_lab/spread_branch_fluid_pipe_bug.txt`, `connected_branch_fluid_pipe.txt`.

## JSON 직렬화 계약

- 최상위 키 순서: `V`, `BP`
- `BP` 키 순서: `$type`, `Icon`, `Entries`, `BinaryVersion`
- 각 `Entries` 항목: `X`/`Y`/`R`는 값이 **0일 때 키 생략**, `T`는 항상 마지막
- `Icon`: `icon:Platforms` + `shape:RuRuRuRu`

## Copy JSON island-local (디코드 입력)

`BP.Entries` `X`/`Y`/`R` 는 **섬 블루프린트 로컬** (생략 → `0`, `X+1` 오른쪽, `Y+1` 아래). 월드/Server 좌표 아님. 정본: [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](../../research/research_shapez2_copy_json_island_local_coords_2026-05-23.md).

## 좌표 (랩 raw → 게임 export)

extractor raw \((e_x, e_y)\), `e_dense = raw_x_to_dense_index(e_x)`:

```text
export_x = raw_x_to_dense_index(raw_x) - e_dense
export_y = raw_y - e_y - 1
```

Export-column projection: [`copy_json_coords.py`](../../django_apps/asteroid_lab/snapshots/copy_json_coords.py) (PR-F: no `server_coords.py`). Persist: `island_bbox_left_bottom_raw_xy_v1`.

**생산기** [`sample_gene_exhaustive_generator.py`](../../django_apps/asteroid_lab/services/sample_gene_exhaustive_generator.py) 의 `abstract_grid_to_raw_xy` / NWS 배치는 변경하지 않는다 (버그는 export 층만).

## 상수·gzip

- `CONNECTED_BRANCH_FLUID_PIPE_COPY` / `_JSON_BYTES`: 사용자 **정상** `H4sIAMsrC2oA/…` (payload 끝에 불필요한 `=` 없음).
- `encode_official_copy_string`: JSON 직렬화 후 `gzip.compress(..., mtime=0)` — **레이아웃별 gzip 바이트 고정 없음**.

## 레이아웃 동치

[`blueprint_equivalence.py`](../../django_apps/asteroid_lab/snapshots/blueprint_equivalence.py): extractor 앵커 + dense_x / raw Y 평행 이동.

## 검증

- `tests/unit/asteroid_lab/test_official_canonical_export.py`
- `tests/unit/asteroid_lab/test_export_dense_contiguity.py`
- `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py`
- `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py`

## 완료 조건 (요약)

- 생성 `code` ≠ spread 버그 copy; connected branch topology는 정상 fixture와 JSON bytes·layout 동치.
- export dense 열 집합에 `{-3,-1,0}` 갭 패턴 없음.
