# 05 — STEP 1: Asteroid reconstruction (§6)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 04

---

## 6. STEP 1 — Asteroid Reconstruction

### 6.1 목표

기존 blueprint에서 소행성 채굴 가능 영역을 복원한다.

```text
full_barrier_cells        # 기존 건물/장애물 전체
extraction_shell_cells    # 소행성 shell / 외곽 채굴 영역
belt_cells                # 기존 belt
pipe_cells                # 기존 pipe
interior_patch_cells      # decode 후 추론된 내부 patch
mineable_placement_cells  # 실제 배치 후보 셀
```

---

### 6.2 핵심 로직

```text
1. blueprint에서 asteroid shell cell을 수집한다.
2. 기존 belt/pipe/extractor/extension을 분리한다.
3. 소행성 boundary를 기준으로 외부 flood fill을 수행한다.
4. 작은 gap 때문에 내부가 외부로 새는 문제를 막기 위해 Chebyshev 8-neighbor closing을 적용한다.
5. 외부가 아닌 빈 공간을 내부 채굴 후보 patch로 추론한다.
```

### 6.2.1 Blueprint X 격자 (CANON)

```text
decode·STEP1 ``mineable_placement_cells`` 매핑에는 **X==0 열 식별자가 존재하지 않는다**
(Shapez copy blueprint: X==0 비섭식, ``asteroid_reconstruction.py`` 참고).
이는 **라벨/섭식 규칙**이며, 인접 열 사이에 **물리적 void(빈 칸 열)**가 끼어 있다는 뜻이 아니다.
STEP2/3 placement는 전역 ``x<=0`` 가드가 아니라 mineable·``full_barrier_cells``·
belt/pipe로만 인접 셀 타당성을 판별한다.
```

---

### 6.3 중요한 정본 (필드 시맨틱)

```text
interior_patch_cells      ← STEP1에서만 추론되는 소행성 내부 채굴 격자(폐곡선 안의 빈 격자).
mineable_placement_cells  ← shell ∪ patch ∪ 장비 footprint 등으로 확정된 “정식 소행성 채굴 필드”.
```

의미 정리:

- 위 두 집합에 들어간 좌표는 **맵 밖 공기(off-map void)**가 아니라, blueprint 복원 결과로 **소행성 채굴 필드**다. Preview/UI·스프라이트 계층에서는 ``asteroid_field`` / ``role=mineable``로 취급하고(§6.3.1), Pass3 ``RouteZone.INTERNAL_VOID`` 같은 “내부 빈 공간” 비용 존과 **동일시하지 않는다**.
- **mineable 집합과 interior patch 추론**은 **decode / reconstruction(STEP1)에서만** 수행한다.
- Pass1/Pass2/Pass3/Reclaim은 그 이후 **이미 확정된** ``mineable_placement_cells`` 위에서 배치·라우팅만 하며, reconstruction이 확정한 셀을 **void로 바꾸거나 mineable 정의를 덮어쓰지 않는다**.

### 6.3.1 Preview / UI: ``inferred`` → ``mineable`` (출력 계층)

복원 결과에서 ``interior_patch_cells ⊆ mineable_placement_cells``로 확정된 셀은 **추론 void(``role=inferred``)**가 아니라 **채굴 가능 소행성 필드**로 표시되어야 한다.

- ``preview_reconstruction_timeline._apply_mineable_highlights``는 ``mineable_placement_cells``에 포함된 inferred 행에 대해 ``role=mineable``·``layout_kind=asteroid_field``를 부여한다.
- 프론트 ``map_sprite_resolver.js``는 ``layout_kind === "asteroid_field"``를 ``role === "inferred"``보다 먼저 해석해, 구 리플레이 행(``inferred``+``asteroid_field``)도 mineable 스프라이트로 그린다.

---

### 6.4 Existing layout analysis와의 경계

```text
decoded island layout ≠ asteroid mineable field
```

**`ExistingLayoutAnalysis`는 `mineable_placement_cells`를 생성·대체하지 않는다.**

`existing_fluid_layout` 또는 `existing_shape_layout` 등 **기존 배치** `source_kind`는 분석 결과일 뿐이며, reconstruction 단계의 **shell·patch·mineable 후보** 정본과 혼동하면 안 된다.

다만 STEP 0.5에서 수집한 **기존 miner / extension / transport 좌표**는 다음 용도로만 사용한다.

```text
1. 기존 배치 제거 전 original snapshot
2. 기존 transport trunk 후보 추출(§9.2·[`03_data_schema_dto.md`](./03_data_schema_dto.md) `ExistingLayoutSolverHints`)
3. orphan transport cleanup 후보 추출
4. replay / debug layer 생성
5. Pass3 / recovery hint (정책 구현은 별도; 계약은 DTO에 선행 고정)
```

**금지**: orphan pipe component·고립 transport 덩어리를 asteroid shell 또는 `mineable_placement_cells`의 **대체 정의**로 취급하는 것.

---

