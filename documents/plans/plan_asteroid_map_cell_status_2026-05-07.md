# 소행성 격자 셀 status (DB) — 구현 결정 (2026-05-07)

## 목적

맵 포인터에 **DB에 저장된 (x,y) status 라벨**을 표시하고, 블루프린트 `mining_map` 오버레이와 혼동하지 않게 한다.

## 좌표 정책

- 블루프린트와 동일하게 **`x == 0` 인 배치는 없음** → `AsteroidMapCell` 저장 및 조회 시 `x=0` 금지.
- `y`는 0 허용 (게임 기본 Y).
- `(0,0)`은 `x=0` 금지로 함께 배제.
- **솔버·라우팅**: 격자 이웃·맨해튼 거리는 `extraction/shapez_grid.py`의 규칙을 따른다(동서로 `x=0`을 건너뜀). 패치 내부 후보에 `(0,y)`가 섞일 수 있으나 `mineable_placement_cells`에서는 제거한다.

## DB vs 블루프린트

- **포인터에 보이는 status 문구는 DB 우선** (`AsteroidMapCell` + `AsteroidCellStatusKind`).
- 복사본에서 나온 `mining_map` 타일은 “배치 추정”용이며, DB world status와 불일치할 수 있다.

## API

- `GET /api/asteroid/map-cells/?x_min&x_max&y_min&y_max` 로 bbox 내 **저장된 셀만** 반환.
- bbox 밖 호버·DB에 행 없음 → 클라이언트는 `void` 종류의 기본 라벨로 표시.
- **보완 (UI)**: 같은 좌표가 디코드된 `mining_map`(occupied / inferred 타일)에 있으면, DB 행이 없어도 `void` 대신 블루프린트 기반 라벨(유체/도형/추론 내부 등)을 표시한다. DB 행이 있으면 여전히 DB 라벨이 우선이다.

## 확장

- 사용자별 맵이 필요하면 `user` FK 및 `UniqueConstraint(user, x, y)` 로 확장 가능.
