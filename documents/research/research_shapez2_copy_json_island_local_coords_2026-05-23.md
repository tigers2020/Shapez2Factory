# Shapez2 copy JSON — island blueprint local coordinates

**상태**: 규약 고정 (게임 paste 검증, 2026-05-23)  
**코드**: `django_apps/asteroid_lab/snapshots/copy_json_coords.py`

## 요약

`SHAPEZ2-4-…` copy string을 디코드한 `BP.Entries`의 `X` / `Y` / `R`는 **소행성 월드 절대 좌표가 아니라**, 붙여넣은 **섬(Island) 블루프린트 내부 로컬 격자**다.

| 규칙 | 의미 |
|------|------|
| 생략된 `X` / `Y` / `R` | `0` |
| `X + 1` | 화면에서 **오른쪽** 한 칸 |
| `Y + 1` | 화면에서 **아래쪽** 한 칸 |
| `X == 0` | copy JSON에서 **유효** (중앙 extension 등) |

**혼동 금지**: copy **island-local**, reconstruction **world map** (`x == 0` 열 없음), gene **canonical E** — 별도 프레임. **PR-F:** dense server `(server_x, server_y)` **삭제** — archived: [`research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](research_asteroid_server_coords_layout_fingerprint_2026-05-16.md).

## 검증 예시 (3-ext + miner + belt)

**Copy code** (게임에서 복사):

```text
SHAPEZ2-4-H4sIAJmKEWoA/5SQwQrCMBBE/2XwGA+1ByFHsUJBQaqIIiJLGzEQ05KkaCn5d9PmInqShYVl38zA9DiAJ0k6Z1hswXtMXNcIcORWka7AkJe1Hh5LcgR+hgw33ypyt9o8LJhulYoL9k6N4EUbBxfPkGlnpLBB2OMIPp0xnEIgwz5krKmrW3fdDbKN1MJkLye0lSHQs8gnf/D/GAewAE8jvmuoFAuh3HVVmyeZ6oM6fbE/1vCX0J3UZLqDMGPGWKj3bwEGAPvbCnpcAQAA$
```

디코드 후 `Entries` (일부 키 생략):

```json
[
  {"X": -2, "Y": 1, "T": "Layout_ShapeMinerExtension"},
  {"X": -1, "Y": 1, "T": "Layout_ShapeMinerExtension"},
  {"Y": 1, "T": "Layout_ShapeMinerExtension"},
  {"X": 1, "R": 3, "T": "SpaceBelt_Forward"},
  {"X": 1, "Y": 1, "R": 3, "T": "Layout_ShapeMiner"}
]
```

생략 필드 적용 후 좌표:

| 화면 (Y=0 위, Y=1 아래) | `(X, Y)` | 타입 |
|-------------------------|----------|------|
| 왼쪽 ext ×3 (row 1) | `(-2,1)`, `(-1,1)`, `(0,1)` | `Layout_ShapeMinerExtension` |
| 오른쪽 miner (row 1) | `(1,1)` | `Layout_ShapeMiner` |
| miner 위 belt (row 0) | `(1,0)` | `SpaceBelt_Forward` (`Y` 생략 → `0`) |

ASCII (copy local, `Y` 아래로 증가):

```text
Y=0:              (1,0) belt
Y=1:  (-2,1) (-1,1) (0,1) (1,1) miner
```

로컬 원점 근처: `(0,1)` = 세 번째 extension, `(1,1)` = miner, `(1,0)` = miner 위 belt.

## 좌표계 대비표

| 프레임 | `X==0` | 용도 |
|--------|--------|------|
| **Copy JSON island-local** | 허용 | 게임 paste / export `BP.Entries` |
| **Island map grid (`Coord`)** | copy-local과 lab 경계에서 동일 | fingerprint, optimization input (PR-F) |
| **World / reconstruction map** | **열 없음** | transport BFS, asteroid evidence |

상세 (world map): [`research_blueprint_grid_coordinates_2026-05-10.md`](research_blueprint_grid_coordinates_2026-05-10.md).

## 구현 맵

| 단계 | 모듈 |
|------|------|
| 디코드 (omitted → 0 문서) | `decode_adapter`, `shapez_copy_decode` |
| island-local 읽기 | `copy_json_coords` |
| island meta attach | `attach_island_coord_meta_to_decoded_json` / `island_bbox.py` |
| lab → game export XY | `blueprint_canonical_export.translate_lab_entries_to_official_xy` |

## 테스트

- `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py` — 생략 키·검증 copy string
- `tests/unit/asteroid_lab/test_island_bbox.py` — island bbox / persist meta
