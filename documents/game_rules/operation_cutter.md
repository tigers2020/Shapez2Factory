# 연산: Cutter / Quad Cutter

## 이 레포 (`cut_vertical_halves`)

수직 반분은 **서쪽(west = SW+NW)** 과 **동쪽(east = NE+SE)** 이며, 반환 순서는 **`(west_half, east_half)`** 이다. 변수명 `left`/`right` 대신 이 이름을 쓰는 것이 [shape_encoding.md](shape_encoding.md)와 맞다.

## shapez 1 위키 계열 설명(요약)

- **Cutter**: 입력 도형을 **수직 방향으로 반절** 자른다. 왼쪽 절반과 오른쪽 절반이 **서로 다른 출력**으로 나간다.
- **Quad Cutter**: 도형을 **4분면**으로 자른다.

## 솔버 관점 서명(개념)

```text
cut_half(shape) -> (west_half, east_half)
quad_cut(shape) -> (NE, SE, SW, NW)   # 각 분면에 해당하는 출력 정의는 구현·게임판 기준으로 고정
```

## 좌표계 주의

- Cutter는 “플레이어가 바라보는 도형의 회전”이 아니라 **도형 좌표계(코드/분면 배열 기준)** 에서 자른다고 보는 편이 안전하다.
- 원하는 방향으로 자르려면 **먼저 회전 → 그 다음 절단** 같은 순서가 필요할 수 있다.

## Shapez 2: 출력 순서

east/west 레이블과 **어느 출력이 메인·보조인지**는 게임·위키 설명과 코드가 어긋나면 그래프 배선이 뒤틀린다. 자세한 값은 [shapez2_cutter_outputs.md](shapez2_cutter_outputs.md).

## 근거·신뢰도

- shapez 1 Fandom 등 커뮤니티 위키: **중간~높음** (교차 검증 권장).
