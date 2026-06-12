---
title: Transport Capacity Planning
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [transport, solver]
sources:
  - documents/knowledge/raw/analysis/belts_pipes_transport/00_summary.md
  - documents/knowledge/wiki/concepts/transport-system.md
confidence: high
---

# Transport Capacity Planning

> **Detail tables:** see [[transport-system]]. This page is the **solver-facing** capacity lens.

## Bottleneck rates (source)

| Transport | Base | Max (×16) | Role |
|-----------|------|-----------|------|
| Shape miner | 30 /min | 480 | Shape source |
| Fluid pump | 300 L/min | 4.8 kL | Fluid source |
| Space belt | **5,760** shapes/min | — | Shape corridor cap |
| Space pipeline | **345.6 kL/min** | — | Fluid corridor cap |

## Planning implications (inference)

- Rim / L2 exterior planning uses **terrain upper bound** and connector counts vs [[asteroid-lab-algorithm]]
- Belt vs pipe: `SpaceBelt_*` → `space_belt`; `SpacePipe_*` → `space_pipe` — mixed transport invalid on same cell kind
- Lift1/Lift2 layouts affect multi-level rim routing (see [[transport-system]])

## Cross-References

- [[building-definitions]]: corridor buildings reference transport layouts
- [[building-variants]]: per-layout connector geometry
- [[island-mechanics]]: separate from throughput — coordinate frame only
