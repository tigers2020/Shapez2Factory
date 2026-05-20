---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-18
authority: project-verified (in-game 기준 확정)
supersedes:
  - documents/research/research_shapez2_space_transport_throughput_2026-05-18.md
related_docs:
  - documents/Algorithm/asteroid_lab_02_pattern_library.md
  - documents/Algorithm/solver_runtime/phase_c_capacity_route_goals.md
---

# 소행성 Space Belt / Space Pipe 처리량 (절대값)

이 문서는 shapez2Solver에서 **Asteroid Lab·`throughput_factor`·포화 비율**에 쓰는 **절대 처리량 정본**이다. 위키·Reddit의 “48 belts / 288 launchers” 등 **상대 환산치는 본 문서보다 우선하지 않는다**.

---

## 공통 배수 (`throughput_factor`)

채굴기(Asteroid Miner)·펌프(Asteroid Pump) 모두 동일:

| 구성 | 배수 | `throughput_factor` |
|------|------|---------------------|
| 추출기/펌프 단독 | ×4 | 4 |
| +1 확장기(booster) | ×8 | 8 |
| +2 확장기 | ×12 | 12 |
| +3 확장기 (최대) | ×16 | 16 |

확장기 1대마다 **+×4** (기본 ×4에서 누적). 구현 계약: [`asteroid_lab_02_pattern_library.md`](../Algorithm/asteroid_lab_02_pattern_library.md).

---

## 도형 (Shape) — Asteroid Miner + Space Belt

### 단위 플랫폼

| 항목 | 값 |
|------|-----|
| 추출기 기준 속도 | **30 shapes/min** |
| 최대 배수 (3 확장) | ×16 |
| fully boosted 1플랫폼 | **480 shapes/min** (= 30 × 16) |

### Space Belt (full)

| 항목 | 값 |
|------|-----|
| 레인당 최대 | **480 shapes/min** |
| 레인 수 | **12** |
| 벨트 전체 최대 | **5,760 shapes/min** (= 480 × 12) |

### 포화 비율

```text
12 fully boosted miners (×16 each) = 1 saturated Space Belt
```

검산: 12 × 480 = 5,760 shapes/min.

---

## 액체 (Fluid) — Asteroid Pump + Space Pipe

### 단위 플랫폼

| 항목 | 값 |
|------|-----|
| 펌프 기준 속도 | **300 L/min** |
| 최대 배수 (3 확장) | ×16 |
| fully boosted 1플랫폼 | **4,800 L/min** (= 300 × 16) = **4.8 kL/min** |

### Space Pipe (full)

| 항목 | 값 |
|------|-----|
| 레인당 최대 | **28.8 kL/min** |
| 레인 수 | **12** |
| 파이프 전체 최대 | **345.6 kL/min** (= 28.8 × 12) |

### 포화 비율

```text
72 fully boosted pumps (×16 each) = 1 saturated Space Pipe
```

검산: 72 × 4,800 L/min = 345,600 L/min = 345.6 kL/min.

---

## 요약 표 (정본)

| 항목 | 절대값 |
|------|--------|
| Shape extractor base | 30 shapes/min |
| Fluid pump base | 300 L/min |
| Extension 배수 스텝 | ×4 per extension (max ×16) |
| 1 fully boosted shape platform | 480 shapes/min |
| 1 full Space Belt | 480 shapes/min × 12 lanes |
| Miners per full belt | 12 |
| 1 fully boosted fluid platform | 4,800 L/min (4.8 kL/min) |
| 1 full Space Pipe | 28.8 kL/min × 12 |
| Pumps per full pipe | 72 |

---

## 솔버·최적화 함의

1. **절대 처리량이 매우 큼** → 벨트/파이프 **개수**만 최소화하는 탐색은 종종 suboptimal.
2. 스코어·유전자 쪽은 **비율·`throughput_factor`·corridor survivability·shared trunk pressure** 가 절대값만큼 중요 ([`asteroid_lab_05_genome_fitness.md`](../Algorithm/asteroid_lab_05_genome_fitness.md), [`asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md)).
3. tier 업그레이드가 게임 전역 속도를 바꿔도 **본 문서 비율(12:1, 72:1, ×4 스텝)** 은 유지된다고 본다 — 절대 L/min·shapes/min만 스케일.

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-18 | 프로젝트 확정 절대값으로 CANON 승격 (커뮤니티 RESEARCH 대체) |
