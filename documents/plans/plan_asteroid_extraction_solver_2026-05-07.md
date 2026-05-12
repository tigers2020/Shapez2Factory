# 소행성 추출 솔버 — 실행 플랜 스냅샷 (2026-05-07)

원본 Cursor 플랜과 [리서치 문서](../research/research_shapez2_asteroid_extraction_2026-05-07.md)를 구현·검증 단위로 옮긴 것이다.

## 완료 기준 (요약)

1. **Decode job** 결과에 `decoded` JSON이 포함되어 Solve가 블루프린트를 읽을 수 있다.
2. **STEP1** 순수 함수: 재구성 → `placeable` / `full_barrier` / 패치 내부.
3. **STEP2** 도형·유체 순차 배치(동일 마스크, 도형 먼저 점유 제거 후 유체), Beam + 상한 가지치기 + 저비용 fragmentation 프록시.
4. **STEP3** expanded bbox 내 A* (MVP 단일 싱크: bbox 경계 중 한 모서리 근처), `RouteEdge` 스키마 포함(용량 0 채움 허용).
5. **STEP4** 자리: `improve` 훅 존재, 기본은 no-op (플래그로 확장).
6. **잡/UI**: `partial`은 best-only; Solve 완료 시 맵에 솔버 오버레이 갱신.
7. **테스트**: 단위 + 기존 잡 통합 갱신; ruff / mypy / black.

## DTO (JSON 호환 dict)

- `partial`: `schema_version`, `best_yield`, `extractor_count`, `extension_count`, `placements` (짧은 리스트), `shape_summary` / `fluid_summary` (선택), `stage_detail`.
- `result`: `ok`, `stub: false`, `metrics`, `tracks: { shape: {...}, fluid: {...} }`, `routes` (엣지 리스트), `reconstruction_summary`.
- `RouteEdge`: `a`, `b` (좌표 튜플 JSON은 `[x,y]`), `used_capacity`, `max_capacity`, `kind`.

## Beam 가지치기

- **상한**: 남은 자유 셀 수 × 트랙당 셀당 이론 최대 처리량 ≤ 현재 best면 가지 제한.
- **fragmentation**: 남은 자유 영역에서 4이웃 차수 0인 격자점 비율이 임계 초과 시 확장 우선순위 하향(또는 폐기 옵션).

## `full_lane_bonus` (옵션)

- 배치 스코어에 `(slots % 4 == 0) * bonus` 형태로 저비용 가산 가능. 기본 0.

## 검증 명령

`python -m pytest tests/unit/shapez_asteroid/ -q` → `ruff check .` → `mypy .` → `black --check .`
