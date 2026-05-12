# 04 — STEP 0: Copy code decode (§5)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 03

---

## 5. STEP 0 — Shapez2 Copy Code Decode

### 5.1 목표

Shapez2 copy string을 내부 solver가 사용할 수 있는 JSON/DTO 형태로 변환한다.

```text
SHAPEZ2-4-
→ Base64 decode
→ gzip decompress
→ JSON parse
→ blueprint entities 추출
```

---

### 5.2 역할

```text
- 기존 건물 좌표 추출
- belt / pipe / extractor / extension / asteroid shell 구분
- solver grid coordinate 생성
- 이후 reconstruction 단계의 입력 데이터 생성
```

---

### 5.3 진행 상태

| 항목                 |       상태 |
| ------------------ | -------: |
| copy string decode |      구현됨 |
| gzip/base64 처리     |      구현됨 |
| JSON parse         |      구현됨 |
| solver DTO 정규화     |    부분 구현 |
| DB 저장 및 SVG 연동     | 추가 개발 필요 |

---

### 5.4 Existing layout analysis (STEP 0.5)

Shapez2 디코드 JSON이 **raw asteroid field**가 아닐 수 있다. 이미 배치된 **island blueprint**(예: top-level `Layout_FluidMiner` / `Layout_FluidMinerExtension` / `SpacePipe_*`)만 담긴 경우가 있다.

이 경우 **decode 직후·reconstruction 이전**에 다음 중간 모델을 생성한다(배치 변경 없음).

```text
- ExistingLayoutAnalysis
- DecodedExistingLayoutContext
- source_kind
- transport_components (요약)
- equipment_attachment
- layout_issues
- ExistingLayoutSolverHints (파생 trunk seed / cleanup 후보)
```

**목적**: 기존 blueprint의 transport·equipment 구조를 정규화하고, Reconstruction / Routing / Pass3 / Validation / Replay가 공통으로 사용할 **읽기 전용 context**를 만든다.

**정본 DTO**: [`03_data_schema_dto.md`](./03_data_schema_dto.md) §E.

#### `source_kind` (요약)

```text
- raw_asteroid_field
- existing_fluid_layout
- existing_shape_layout
- mixed_existing_layout
- unknown
```

**설계 문장**:

```text
Decoded existing layout은 reconstruction 전용 입력이 아니라 solver context다.
```

---

