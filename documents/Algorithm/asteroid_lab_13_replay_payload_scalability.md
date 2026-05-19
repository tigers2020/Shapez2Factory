# Sequence 13 — Replay Payload Scalability Roadmap

**역할:** **Unified replay payload** 스케일링 트랙의 **정본 로드맵**이다 (제품은 단일 timeline; Lab/optimization 귀속 명칭은 13A·13B 계측 시 historical 라벨).  
**범위:** 문서 고정만. **13C 이후 코드·응답 계약·JS 로딩 변경은 명시적 승인 후** 별도 구현 단계에서 수행한다.

**관련 정본·근거:**

- 계측·현장 수치·13A·13B 상세: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) (역사) · 제품 replay 정본: [`asteroid_lab_09_unified_step_replay.md`](asteroid_lab_09_unified_step_replay.md)
- 개발 순서 문맥: [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md)
- 포스트 시퀀스 우선순위: [`asteroid_lab_11_future_execution_plan_post_sequence.md`](asteroid_lab_11_future_execution_plan_post_sequence.md)

---

## 목적 (Purpose)

Sequence 13은 **unified replay timeline**의 프레임 페이로드가 커져 **POST JSON**과 **DevTools 관측성**(response body 캐시 eviction 등)을 망가뜨리는 문제를 해결하기 위한 **스케일링 트랙**이다.

- **replay semantics(리플레이 의미)**는 유지한다.
- **replay / debug artifact**는 계속 **output-only**이다.

---

## 현장 증거 (Current Evidence)

- **HAR 기준** 단일 POST 응답 JSON이 **약 22.6MB**까지 증가한 사례가 관측되었다.
- Chrome DevTools 등에서 **response body eviction**(inspector cache에서 본문 제거)이 발생할 수 있다.

**13A:** 최상위 JSON **섹션별 크기 귀속(attribution)** 계측을 도입했다.  
**13B:** **Lab replay 전용** 귀속, `largest_lab_frames`, **redundancy(중복)** 측정을 추가했다.

---

## 완료 작업 (Completed Work)

| 단계 | 내용 |
|------|------|
| **13A** | 결정적 JSON 섹션 계측(`measure_json_sections` 등), optimization replay **하드 캡** 회귀 검증, HAR·증거 문서화 |
| **13B** | Lab replay 귀속, `full_map` / 셀 수 / redundancy 분석, 상위 프레임 랭킹, **13B 계측 시점:** Lab replay는 optimization 상한(`MAX_OPTIMIZATION_*`)으로 캡되지 않음 — **historical 관측**. 제품 상한: Lab `MAX_UNIFIED_LAB_*`, optimization `MAX_OPTIMIZATION_*` ([`replay_limits.py`](../../django_apps/asteroid_lab/replay/replay_limits.py), [`asteroid_lab_09_unified_step_replay`](asteroid_lab_09_unified_step_replay.md)) |

**구현으로의 전환:** 위는 **계측·설계·회귀 키**까지이며, **POST 본문 축소·lazy-load·delta 등 런타임 동작 변경은 13C 이후**이며 **별도 승인**이 필요하다.

---

## 전략 역할 구분 (inline / lazy-load / delta / interning / compression)

아래는 **서로 대체 관계가 아니라** 책임이 다르다.

| 전략 | 역할 | 시맨틱 |
|------|------|--------|
| **Inline full replay** | 현행: Lab 전체 프레임이 POST 응답에 포함 | 기준선(baseline); 변경 시 동등성 증명 필요 |
| **Lazy-load endpoint (13C)** | POST는 **요약·프리뷰·fetch 핸들**만; 전체 Lab replay는 **온디맨드 GET** 등 | 프레임 **내용 동일**을 목표; 전송 경로만 분리 |
| **Delta replay (13E)** | 직렬화 **표현**만 줄임; 클라이언트/서버 **재구성 규칙** 명문화 | **serialization optimization**이지 **의미 변경**이 아님 |
| **Cell interning / dictionary encoding (13F)** | 반복 셀 페이로드 **참조·사전 인코딩** | 셀 상세 조회·프레임 렌더링 **동등성** 유지 |
| **HTTP compression (13G)** | gzip/Brotli 등 **전송 계층** | 본문 JSON 의미 동일; **시맨틱 페이로드 작업을 대체하지 않음** |

---

## 불가침 불변 조건 (Non-negotiable Invariants)

```text
Replay is output-only.
One unified product replay timeline (dual-track policy deprecated 2026-05-19).
Every frame must remain 2D-renderable (map_view) when payload shape changes.
No solver / algorithm reads replay payload.
Replay semantic equivalence must be preserved.
No large golden JSON unless explicitly approved.
UI uses a single timeline controller unless a dedicated migration sequence opens.
```

**구현 승인 전 금지 (이 문서 단계 포함):**

- **코드 구현** (13C UI·엔드포인트·계약 변경 없음)
- **응답 계약(response contract) 선제 변경**
- **JS replay 로딩 선제 변경**
- **delta 압축·인코딩 본 구현**
- **solver / replay semantics 변경**
- **13C 구현** — **명시적 사람 승인** 없이 착수 금지

---

## Sequence 13C — Full Lab Replay Lazy-load Endpoint

**선호 1차 구현:** POST 응답 크기를 줄이면서 **replay frame semantics**는 바꾸지 않는다.

- POST 응답: **요약·프리뷰·fetch 핸들**(예: 토큰·URL·리소스 id — 구체 형식은 승인된 설계에서 확정).
- **전체 Lab replay**는 필요 시 **별도 요청**으로 fetch.
- **Full replay 엔드포인트**가 반환하는 프레임은, 과거 인라인 `lab_replay_frames_json`과 **시맨틱 동일**해야 한다.

**시맨틱 리스크:** fetch 경로·캐시·권한·CSRF·오류 시 **부분 로드**가 UI 상태를 오염시키지 않도록 할 것.

---

## Sequence 13D — UI Lazy-load Integration

- UI는 **replay controller가 전체 Lab replay가 필요할 때** 로드한다.
- **로딩 / 오류 상태**를 노출한다.
- **단일 unified timeline controller**를 유지한다 ([`asteroid_lab_09_unified_step_replay`](asteroid_lab_09_unified_step_replay.md); dual-track 폐기).
- 마이그레이션 기간 **인라인 모드 폴백**은 허용된다.

**시맨틱 리스크:** 두 소스(인라인 vs fetch)가 **동시에 “권위”**를 주장하면 드리프트; 하나의 명시적 소스 우선순위가 필요하다.

---

## Sequence 13E — Delta Replay Prototype

- **lazy-load로도 부족할 때** 이후에 탐색한다.
- **프레임 재구성 동등성** 테스트를 포함해야 한다.
- Delta 형식은 **직렬화 최적화**이며 **의미 변경 금지**.

**시맨틱 리스크:** 재구성 버그·프레임 순서·`full_map`/`diff` 해석 불일치.

---

## Sequence 13F — Cell Interning / Dictionary Encoding

- **redundancy 계측(13B)** 이 충분히 크다고 판단된 뒤 검토.
- **셀 상세 조회**와 **프레임 렌더링 동등성**을 유지한다.

**시맨틱 리스크:** intern 키 해석 실패 시 조용한 잘림·잘못된 셀 표시.

---

## Sequence 13G — Transport Compression / Server Response Policy

- **gzip / Brotli** 동작 및 응답 헤더를 검증한다.
- **전송 계층** 최적화이며, **13C–13F의 시맨틱 페이로드 설계를 대체하지 않는다.**

**시맨틱 리스크:** 낮음(바이트 동일 디코드 후 기존 JSON 파이프라인). **관측 리스크:** DevTools가 압축 본문을 다르게 표시할 수 있음.

---

## 보류 / 지금 안 함 (Deferred / Not Now)

다음은 **13C–13G로도 불충분할 때만** 재검토한다.

```text
Binary replay format
WebSocket streaming
Replay database chunking
Object-store artifact downloads
Full replay pagination (대형 단일 artifact 분할 등)
```

---

## 필수 테스트 전략 (Required Test Strategy)

구현 단계에서 고정할 검증(요지):

```text
full endpoint replay == previous inline replay (시맨틱 동등)
same frame_count
same frame_index order
same frame_key / event metadata
same full_map / diff semantics
cell detail lookup compatibility
no algorithm reads replay payload
lazy-load failure: explicit UI error, current replay state corrupted 금지
```

**권장 테스트 명령 (구현 후·회귀):**

```text
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k "payload or replay or json_size"
```

---

## Sequence 13 종료 조건 (Exit Criteria)

```text
POST response no longer carries unnecessary full Lab replay payload by default
full replay remains fetchable and semantically equivalent
large response DevTools eviction is avoided for normal Run Solver flow
replay / debug remains output-only
```

---

## 문서 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-17 | Sequence 13 로드맵 정본 최초 고정 (13A·13B 완료 요약, 13C–13G, 불변·금지·테스트·종료 조건) |
