---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-05-18
authority: project-verified (confirmed against in-game baseline)
supersedes:
  - documents/research/research_shapez2_space_transport_throughput_2026-05-18.md
related_docs:
  - documents/Algorithm/asteroid_lab_02_pattern_library.md
  - documents/Algorithm/solver_runtime/phase_c_capacity_route_goals.md
---

# Asteroid Space Belt / Space Pipe Throughput (Absolute Values)

This document is the **absolute throughput canonical source** for **Asteroid Lab, `throughput_factor`, and saturation ratios** in shapez2Solver. Wiki/Reddit relative figures such as "48 belts / 288 launchers" **do not override this document**.

---

## Common Multiplier (`throughput_factor`)

Asteroid Miner and Asteroid Pump share the same pattern:

| Configuration | Multiplier | `throughput_factor` |
|------|------|---------------------|
| Extractor/pump alone | ×4 | 4 |
| +1 booster | ×8 | 8 |
| +2 boosters | ×12 | 12 |
| +3 boosters (max) | ×16 | 16 |

Each booster adds **+×4** (cumulative from base ×4). Implementation contract: [`asteroid_lab_02_pattern_library.md`](../Algorithm/asteroid_lab_02_pattern_library.md).

---

## Shapes — Asteroid Miner + Space Belt

### Per Platform

| Item | Value |
|------|-----|
| Extractor base rate | **30 shapes/min** |
| Max multiplier (3 extensions) | ×16 |
| Fully boosted 1 platform | **480 shapes/min** (= 30 × 16) |

### Space Belt (full)

| Item | Value |
|------|-----|
| Max per lane | **480 shapes/min** |
| Lane count | **12** |
| Belt total max | **5,760 shapes/min** (= 480 × 12) |

### Saturation Ratio

```text
12 fully boosted miners (×16 each) = 1 saturated Space Belt
```

Check: 12 × 480 = 5,760 shapes/min.

---

## Fluid — Asteroid Pump + Space Pipe

### Per Platform

| Item | Value |
|------|-----|
| Pump base rate | **300 L/min** |
| Max multiplier (3 extensions) | ×16 |
| Fully boosted 1 platform | **4,800 L/min** (= 300 × 16) = **4.8 kL/min** |

### Space Pipe (full)

| Item | Value |
|------|-----|
| Max per lane | **28.8 kL/min** |
| Lane count | **12** |
| Pipe total max | **345.6 kL/min** (= 28.8 × 12) |

### Saturation Ratio

```text
72 fully boosted pumps (×16 each) = 1 saturated Space Pipe
```

Check: 72 × 4,800 L/min = 345,600 L/min = 345.6 kL/min.

---

## Summary Table (Canonical)

| Item | Absolute Value |
|------|--------|
| Shape extractor base | 30 shapes/min |
| Fluid pump base | 300 L/min |
| Extension multiplier step | ×4 per extension (max ×16) |
| 1 fully boosted shape platform | 480 shapes/min |
| 1 full Space Belt | 480 shapes/min × 12 lanes |
| Miners per full belt | 12 |
| 1 fully boosted fluid platform | 4,800 L/min (4.8 kL/min) |
| 1 full Space Pipe | 28.8 kL/min × 12 |
| Pumps per full pipe | 72 |

---

## Solver and Optimization Implications

1. **Absolute throughput is very large** → search that only minimizes belt/pipe **count** is often suboptimal.
2. Scoring and genes should weight **ratios, `throughput_factor`, corridor survivability, shared trunk pressure** as heavily as absolute values ([`asteroid_lab_05_genome_fitness.md`](../Algorithm/asteroid_lab_05_genome_fitness.md), [`asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md)).
3. Even if tier upgrades change global game speed, **ratios in this document (12:1, 72:1, ×4 steps)** are assumed stable — only absolute L/min and shapes/min scale.

---

## Change History

| Date | Change |
|------|------|
| 2026-05-18 | Promoted to CANON with project-confirmed absolute values (supersedes community RESEARCH) |
