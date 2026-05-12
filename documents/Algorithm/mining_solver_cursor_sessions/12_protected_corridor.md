# 12 — Protected transport corridor (§14)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 08, 09

---

## 14. Protected Transport Corridor

### 14.1 필요성

Pass2 / Pass3 / recovery 사이에서 이미 검증된 route가 다음 pass에서 파괴되면 연결성이 다시 깨진다.

따라서 다음 개념이 필요하다.

```text
protected_transport_corridors
```

output stub·외부 trunk merge·경로 비용 용어는 [`01_project_overview.md`](./01_project_overview.md) §3.5와 맞춘다.

---

### 14.2 보호 등급

| 등급                 | 의미                                             | Pass3에서 변경 가능? |
| ------------------ | ---------------------------------------------- | -------------: |
| hard_protected     | output stub, 외부 연결을 유지하는 필수 trunk, 대체 route 없음 |            아니오 |
| soft_protected     | 현재는 유효하지만 대체 route가 있으면 교체 가능한 route/corridor  |         조건부 가능 |
| candidate_corridor | probe 결과 또는 아직 commit 전 corridor               |             가능 |

#### 14.2.1 candidate_corridor 생명주기

```text
생성: routing probe / shadow 경로 계산 시 corridor 후보로 표시될 때.
승격 soft_protected: 해당 경로가 replacement 검증(§14.3 조건)까지 통과해 commit되면.
승격 hard_protected: 대체 route가 없고 trunk 불가결 조건으로 고정될 때(정책적으로 드묾).
폐기: probe 실패, 더 나은 candidate로 대체, 또는 부모 placement rollback으로 무효화될 때.
```

동일 공간에 candidate가 중복되면 최신 검증 통과 경로가 우선하고 나머지는 폐기한다.

#### 14.2.2 `hard_protected` 판정 시점(정본)

```text
- soft_protected 승격과 동일하게, **STEP 4에서 해당 trunk/route가 commit될 때** 기본 분류를 한다.
- “대체 route 없음 + trunk 불가결” 판정은 **commit 직후 증명**으로 hard로 승격할 수 있다. **candidate exhaust(정본)**: 대체·우회 route 존재를 부정하기 위해 **§10.6·구현 합의 검색 예산**(`MAX_EXPANDED_NODES_PER_ROUTE`, `MAX_ROUTE_SEARCH_MS` 등)을 소진했거나, 동일 예산·동일 tie-break 하에 **feasible 후보가 더 없음**이 결정론적으로 판정된 상태(frontier empty, goal unreachable, 또는 정책상 허용 split 후보 소진)를 뜻한다. trace에는 `replacement_search_exhausted: true`, 사용한 예산 키, 마지막 frontier 크기 등을 남긴다.
- Pass3 시작 전: STEP 4 완료 시점의 hard/soft 집합이 Pass3 허용 변경 범위의 기준이다.
- Pass3·recovery가 진행되며 교체가 일어나면 **교체 성공 시점**에 protected 집합을 갱신한다.
- Final validation은 사후 검증만 하며, 이때 새로 hard를 “발명”하지 않는다(불일치면 버그 또는 validation_recovery).
```

#### 14.2.3 `ExistingLayoutAnalysis` 기반 초기 보호 등급(읽기 전용 힌트)

STEP 0.5에서 온 transport component를 **디코드 직후** 곧바로 `hard_protected`로 올리지 않는다.

```text
existing pipe/belt ≠ protected corridor
```

| Existing component status | 초기 보호 등급(힌트) |
| --- | --- |
| `main_trunk_candidate` | `candidate_corridor` 또는 **soft_protected 후보**(정책명: `soft_protected_candidate`) — STEP 4 commit 전까지 확정 아님 |
| `orphan_component` | `cleanup_candidate` |
| `single_cell_artifact` | `cleanup_candidate` |
| STEP 4에서 route commit 후·대체 불가가 증명된 trunk | `soft_protected` → 필요 시 `hard_protected` (위 §14.2.2) |

**승격**: output stub·대체 불가 trunk 증명은 **STEP 4 routing commit 이후**에만 `hard_protected`로 올린다.

---

### 14.3 보호 해제 조건

soft protected corridor는 다음 조건을 모두 만족할 때만 해제할 수 있다.

```text
[ ] replacement route가 먼저 계산됨
[ ] replacement route가 connected true
[ ] replacement route가 capacity safe
[ ] output stub 전체가 여전히 외부와 연결됨
[ ] route score가 기존보다 개선됨 또는 recovery context에서 연결성 회복에 필요함
```

즉, Pass3는 hard_protected corridor를 건드리지 않고, soft_protected corridor만 **atomic replace** 방식으로 교체한다.

**Recovery routing(§11.4 ratio 완화) 추가 규칙**: 연결성 회복을 위해 긴 우회를 허용하더라도, soft corridor를 바꿀 때는 위 조건의 **replacement 선계산·atomic replace**를 완화하지 않는다. “회복에 필요함”은 새 경로가 commit된 뒤에야 기존 soft 구간을 제거할 수 있음을 뜻한다. 기존 통로만 남기고 새 우회가 그 통로에 의존하는 줄기를 **reachable에서 제외**시키는 형태는 금지한다.

---

### 14.4 trace에 필요한 필드

```text
before_return_validate:
- extractor_count
- extension_count
- baseline_after_pass2_extensions
- protected_corridor_pool_len
- hard_protected_count
- soft_protected_count
- transport_connected
```

§14.3 soft replace summary는 누적 count와 마지막 session trace를 구분한다.

```text
p4_soft_replace_attempt_count = soft replace session count
p4_soft_replace_commit_count = committed soft replace session count
p4_soft_replace_jobs_attempted = routing job probe count inside last session
p4_soft_replace_selected_job_index = selected routing job index inside last session, or null
```

---
