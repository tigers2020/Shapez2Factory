# Asteroid Lab: server 좌표계 및 레이아웃 핑거프린트 (결정안)

**상태**: 구현 기준 문서 (CANON 아님, 리팩터리 참고용)  
**날짜**: 2026-05-16

## 목적

- Shapez2 디코드 **raw `X`/`Y`**는 게임·재생성·디버그용으로 **유지**한다.
- **내부 계산**: layout hash·`decoded_json` 부착·Lab 그리드(가능 시)는 **`server_x` / `server_y`** 를 쓴다.
- **운송 BFS(`existing_layout_inspection`)** 는 **raw `iter_four_neighbors`** 를 유지한다. rank `dense_x` 가 연속 양의 raw `X`(예: 1과 2)에서 충돌할 수 있어, 서버 격자 4이웃만으로는 기존 관측과 어긋날 수 있기 때문이다.
- **coord_system** 문자열: `server_bbox_right_bottom_dense_x_v1`

## raw x → dense x (x == 0 컬럼 없음)

- `raw_x == 0` 인 엔트리는 그리드에 없는 열이므로, dense 변환 시 **해당 엔트리에는 `server_x`/`server_y`를 부착하지 않는다**(기존 `X`/`Y`는 그대로 둠).
- 공식:
  - `raw_x < 0` → `dense_x = (raw_x + 1) // 2`
  - `raw_x > 0` → `dense_x = (raw_x - 1) // 2 + 1`

## bbox 기준 server 좌표 (맵 로컬, 양의 정수)

- 맵 = 해당 decode의 `BP.Entries` 전체로 bbox를 잡는다.
- `max_dense_x = max(dense_x)`, `min_raw_y = min(Y)`, `max_raw_y = max(Y)` (유효 엔트리만).
- **server_x** = `max_dense_x - dense_x` → **가장 오른쪽 열이 `server_x == 0`**.
- **server_y** = `raw_y - min_raw_y` → **가장 아래 행이 `server_y == 0`** (raw Y가 위로 갈수록 커지는 전제).  
  - 게임에서 반대로 확인되면 `server_y = max_raw_y - raw_y` 로 바꾸고 본 문서를 갱신한다.

**주의**: `server_x`/`server_y`는 **Shapez2 전역 좌표가 아니라**, 해당 맵 bbox에 종속된 **프로젝트 내부 좌표**다. 맵 bbox가 바뀌면 동일 raw 셀의 server 값도 바뀔 수 있다.

## `visual_col` / Lab JS `visualCol` 과의 차이

- 기존 Lab용 `visual_col`(음수 raw x 그대로, 양수는 `x-1`)은 **본 server 좌표와 수치가 다르다**.
- 신규 경로는 **rank 기반 `dense_x` + 우하단 원점 bbox** 만 `server_*` 및 fingerprint에 쓴다.
- 이행 기간: UI는 `server_x`/`server_y`가 있으면 우선, 없으면 legacy `visualCol`/raw fallback.

## 해시 필드 역할

| 필드 | 의미 |
|------|------|
| `content_sha256` | 원문 copy 코드 등 **입력 바이트** 식별 |
| `layout_fingerprint` | **bbox 정규화 server 좌표** 기준 canonical map의 SHA-256. 동일 상대 패턴이 bbox와 함께 평행 이동하면 **동일 해시가 될 수 있음**. |
| `absolute_layout_fingerprint` | **dense_x + raw_y**(bbox 이동 없음) 기준 canonical의 SHA-256. 맵 전역에서 위치 비교가 필요할 때 사용. |

Canonical JSON에는 **`schema`**, **`coord_system`**(및 합의된 `origin`/`axis`/`bbox`)을 넣고, **coord_system 없이 해시하지 않는다**. fingerprint payload에는 **raw x/y를 넣지 않는다**.

## 구현 위치 (요약)

- 순수 로직: `django_apps/asteroid_lab/snapshots/server_coords.py`, `layout_fingerprint.py`
- 부착 시점: decode + normalize 직후, `AsteroidMapInput.decoded_json` 저장 전
- DTO: `DecodedCellDTO.server_x` / `server_y`
