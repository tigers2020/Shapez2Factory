# Recipe Graph Workbench — 실행 계획 (2026-05-04)

본 문서는 스태프 매크로 **그래프 편집기**를 첨부 목업 수준으로 **레이아웃 전면 리디자인**하고, 연결 규칙·COLOR_MIXER·검증 UX를 단계적으로 반영하기 위한 계획이다.  
(`graph_document` 스키마·도메인 경계는 기존 [AGENTS.md](../../../../AGENTS.md)·[`architecture.mdc`](../../../../.cursor/rules/architecture.mdc)를 따른다.)

---

## 1. 목표 요약

| 축 | 내용 |
|----|------|
| **UI** | 아래 **§2 목업 레이아웃**에 맞춘 전면 리디자인(헤더·팔레트·캔버스·하단 인스펙터·풋터). |
| **도메인** | `shape → operation → intermediate(shape) → … → target` 토폴로지 강제; `operation → operation` 등 금지. |
| **팔레트** | 엔진이 지원하는 연산만 노출(SHAPE / ROTATE / CUT / FLOW / COLOR). 목업의 LOGIC·UTILITY 등은 **노출하지 않음**(설계 전). |
| **색** | 기존 채널 문자 혼합에 `ColorMode` 확장 여지; 테이블 기반 검증. |

---

## 2. 레이아웃 목업과의 정렬 (첨부 이미지 기준)

전면 리디자인 시 **다음 구역을 1차 목표**로 한다. (픽셀 단위 복제가 아니라 **구역·역할·정보 계층** 동일.)

### 2.1 헤더 (상단 바)

- 앱/페이지 타이틀(예: Staff · Graph editor), 레시피 코드·이름 등 메타 한 줄.
- 우측 액션: **Catalog**, **Edit metadata**(기존 URL 유지).

### 2.2 메인 중단 — 2열 (좌 팔레트 | 우 캔버스)

**좌: Operations / Node 팔레트**

- 상단 **검색** 입력(라벨·연산 키 필터).
- 카테고리별 접기/제목: 실제 데이터는 **§4 팔레트 범위**만 표시. (목업의 BASIC/TRANSFORM/LOGIC 등 이름은 참고만 하고, 구현은 SHAPE·ROTATE·CUT·FLOW·COLOR 고정.)
- 각 항목: **아이콘 + 라벨** 가로 카드, 드래그 가능.
- (선택) 하단 Quick access / 즐겨찾기 영역.

**우: 캔버스 워크스페이스**

- **배경 그리드** 및 기존 pan/zoom 동작 유지.
- 캔버스 **상단 툴바**: Grid 토글, (가능 시) Snap, Zoom % / ± / **Fit to screen** 등 — 기존 `graph_viewport`와 연동해 단계 도입.
- **미니맵**: 캔버스 우상단 오버레이(작은 전체 맵); 구현 난이도상 **Phase 후순위**로 두되, 레이아웃에는 **자리(플레이스홀더)** 확보 가능.

### 2.3 하단 — 인스펙터 / 상태 패널 (전폭)

목업과 같이 **한 줄 또는 접을 수 있는 스트립**으로 다음 블록을 배치한다.

| 블록 | 역할 |
|------|------|
| Node Info | 선택 노드 이름·종류·짧은 설명·프리뷰(가능 시). |
| Properties | 노드별 편집(드롭다운·숫자 등) — 기존 편집 모달 내용을 단계적으로 이전. |
| Validation | 재계산/검증 메시지, 성공·경고·오류. |
| Stats | 노드 수, 엣지 수, (선택) 경고/오류 개수 등. |
| Notes | 사용자 메모(선택, 레시피 필드와 연동 여부는 별도 결정). |

### 2.4 최하단 — 액션 바

- **Recompute (dry-run)**, **Recompute & save graph**.
- 상태 한 줄: 마지막 재계산 시간·유효 여부 등.
- **Add node / Add operation / Delete selected** 등 — 기존 CRUD 툴바와 통합.

### 2.5 구현 시 파일 (예상)

- 템플릿: [`django_apps/web/templates/web/macro_pattern_graph.html`](../../../../django_apps/web/templates/web/macro_pattern_graph.html) — 그리드 셸·영역 id.
- 스크립트: [`django_apps/web/static/web/js/macro_pattern_graph_editor.js`](../../../../django_apps/web/static/web/js/macro_pattern_graph_editor.js) — 거대 `innerHTML`을 섹션별 빌더로 분해.
- 스타일: Tailwind 유지; 필요 시 `web/static/web/css` 소량 보조 또는 템플릿 내 scoped 블록.

---

## 4. 팔레트에 노출할 연산 (엔진 일치)

목업에 그려진 Logic·Utility 등은 **이번 단계에서 제외**.

- **SHAPE**: Base shape  
- **ROTATE**: `rotate_cw`, `rotate_ccw`, `rotate_180`  
- **CUT**: `cutter`, `cutter_full`, `half_destroyer`, `splitter`  
- **FLOW**: `stacker`, `swapper`, `pin_pusher`  
- **COLOR**: `painter`, `color_mixer`  

아이콘은 기존 [`catalog_operations_payload`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py)의 정적 URL 사용.

---

## 5. 도메인 · 검증 (Phase 1)

- 서버: `validate_graph_document` 이후 **토폴로지 검증** 추가(출력 엣지의 `to`가 intermediate shape인지, 입력이 shape에서만 오는지 등).
- 클라이언트: `recipeWireConnect`에서 동일 규칙으로 **연결 거부** + 메시지.
- 단위 테스트: 허용/거부 케이스.

---

## 6. Color Mixer (Phase 3)

- [`color_mix_semantics.py`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py) 확장 및 `ColorMode` placeholder.
- 인스펙터 Properties에 허용 조합 반영(드롭다운/경고).

---

## 7. 캔버스 고급 UX (Phase 4)

- 노드 role별 시각 차별화([`graph_markup.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js)).
- 위반 엣지 스타일(점선/색) — 서버 검증 결과 또는 클라이언트 추정.
- 미니맵·와이어 색 단계 — 우선순위별.

---

## 8. 문서·승인·검증

- 본 계획은 `documents/` 한국어 본문 규칙을 따른다.
- 구현 전 승인 게이트는 프로젝트 [protocols/README.md](../../../../protocols/README.md)에 따른다.
- 검증: `pytest`(unit·integration), 변경 구간 린트.

---

## 9. 이 계획에서의 우선순위

1. **레이아웃 전면 리디자인(§2)** — 사용자 요청 반영, 목업과 동일한 구역 분리.  
2. **토폴로지 검증(§5)** — 잘못된 그래프 방지.  
3. Color Mixer·인스펙터 상세.  
4. 미니맵·Fit·Notes 영구 저장 등 부가 기능.
