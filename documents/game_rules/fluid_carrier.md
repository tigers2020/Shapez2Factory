# 유체 캐리어(Fluid carrier)

## 개념

게임에서 **빈 유체 캐리어**는 도형 생산물이 아니라 **균일한 색(잉크) 코드 한 종류**를 파이프로 실어 나른다. 이 저장소에서는 그 계약을 **칠 가능한 분면에 동일 색 문자가 깔린 `Shape` 코드**(순수 유체)로 모델링한다. 자세한 추출 규칙은 `django_apps/shapez_solver/services/fluid_semantics.py`의 `pure_fluid_color`와 같다.

## 소스에서 선택 가능한 색

- 유체 **소스**(`graph_document` 노드에 `source_carrier: "fluid"`)로 넣을 수 있는 균일 색은 **원색 RGB** 문자만 허용한다: `r`, `g`, `b`.
- **무채색 `u`** 나 **보조색 `c`, `m`, `y`, `w`** 는 유체 소스에서 직접 고를 수 없다. (레거시 그래프는 `source_carrier` 생략 시 기존과 동일하게 동작한다.)

## 보조색·Y/M/C/W

- `c`(시안), `m`(마젠타), `y`(옐로), `w`(화이트) 등은 **`color_mixer` 연산으로만** 만들 수 있다는 규칙을 따른다.
- 혼합 표의 구현은 `django_apps/shapez_solver/services/color_mix_semantics.py`를 본다. 추가 혼합(예: 화이트 조합)이 필요하면 별도 리서치 후 그 모듈을 확장한다.

## CMYK·`k`(블랙)

- 커뮤니티에서 말하는 YMCKW와 대응할 때, 이 프로젝트의 **한 글자 색 코드**에는 `c`, `m`, `y`, `w`가 있고 **`k`(블랙) 전용 문자는 아직 없다** (`django_apps/shapez_core/domain/shape_catalog.py`의 `COLOR_KINDS`). 블랙을 모델에 넣을 때는 카탈로그·혼합 규칙·UI를 함께 갱신한다.

## Painter 레거시 `paint_color`

- 두 입력(유체 와이어 + 도형)이 아닌 **단일 입력 + `paint_color`** 경로도 인라인 잉크로 간주하며, **RGB(`r`,`g`,`b`)만** 허용한다.

## Intermediate·팔레트 통합·포트 규칙

- **팔레트**: 빈 소스는 기본 **도형(material)** 한 종류로 추가한다. 유체가 필요하면 노드 편집에서 **carrier = fluid** 로 바꾼 뒤 RGB 유체를 설정한다.
- **`source_carrier`**: `kind: "shape"` 이고 `role` 이 `source` 또는 `intermediate` 일 때 **와이어 종류**로 쓴다. `"fluid"` = 액체 캐리어, 키 생략(또는 정규화 시 제거) = material. `role: "target"` 인 출력 노드에는 `source_carrier` 를 두지 않는다.
- **입력 포트(백엔드 `recipe_graph_input_carrier` / 프론트 `recipeConnection.ts` 동일 표 — 변경 시 양쪽 동기화)**:
  - `painter` 2와이어: 정렬상 인덱스 0 = **fluid**, 1 = **material**; `paint_color` 가 있으면 단일 **material** 입력만.
  - `painter` + `paint_color` 1와이어: **material**.
  - `color_mixer` 2와이어: 둘 다 **fluid**.
  - `swapper`, `stacker`, `crystal_generator` 2와이어: 둘 다 **material**.
  - 그 외 단항 연산: **material**.
- **연산 출력 → intermediate**: `color_mixer` 의 해당 출력 레인은 **fluid** intermediate(`source_carrier: "fluid"`)만 허용; 그 외 연산 출력은 **material** intermediate. 재계산(`recipe_graph_recompute`)이 출력에 맞게 intermediate 를 맞춘다.
- **납품(intermediate → output)**: material·fluid intermediate 모두 허용(동일 `shape_code` 복사 모델).
- **UI**: carrier 또는 `shape_code` 를 바꿀 때 그 노드에 연결된 엣지 중 위 규칙에 맞지 않는 것은 제거한다.

## 관련 문서

- [operation_color_mixer.md](operation_color_mixer.md)
- [operation_painter.md](operation_painter.md)
