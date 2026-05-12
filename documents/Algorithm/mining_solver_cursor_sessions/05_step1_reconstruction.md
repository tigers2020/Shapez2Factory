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

---

### 6.3 중요한 정정 사항

다음 로직은 **재배치 중에 수행하면 안 된다.**

```text
내부 void를 나중에 inferred mining field로 변환한다.
```

올바른 기준:

```text
- mineable field 추론은 decode/reconstruction 단계에서만 한다.
- Pass1/Pass2/Pass3/Reclaim loop는 이미 확정된 mineable field 위에서 placement와 routing을 최적화한다.
```

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

