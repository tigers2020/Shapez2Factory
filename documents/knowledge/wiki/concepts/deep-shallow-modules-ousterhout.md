---
title: Deep vs Shallow Modules (Ousterhout)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [architecture, agentic]
sources:
  - documents/knowledge/raw/2018-John Ousterhout-A Philosophy of Software Design.pdf
  - documents/knowledge/raw/AI 코드 망치는 6가지와 해결법. md
confidence: medium
---

# Deep vs Shallow Modules

> **Authority:** working research wiki — not project canon.  
> **Primary source:** John Ousterhout — *A Philosophy of Software Design* (2018).  
> **Source ID:** `src-20260612-ousterhout-pdf`

## Definitions (source)

| Kind | Interface | Interior | Effect |
|------|-----------|----------|--------|
| **Deep module** | Simple, small API | Rich functionality hidden | Complexity **pulled downward** |
| **Shallow module** | Wide / leaky API | Little hidden power | Many modules, maze-like navigation |

**Design goal (source):** maximize **power per interface complexity** — not minimize lines or maximize file count.

## Why it matters for AI coding (inference + Pocock raw)

Default LLM output tends toward **many shallow modules** (small files, repetitive wrappers). The agent that wrote the maze **cannot reliably navigate it** on the next pass — dependencies and roles blur. Prescription from [[software-fundamentals-ai-era-pocock-2026]]: consolidate related code behind a **simple boundary** (grey-box interfaces).

## Related Ousterhout themes (source, abbreviated)

- **Information hiding** — interface reveals *what*, not *how*
- **Layers** — each layer different abstraction; no pass-through leaks
- **General-purpose modules** — reuse via narrow powerful APIs
- **Define errors out of existence** — design so invalid states are unrepresentable

## Project mapping (inference)

| Pattern | This repo |
|---------|-----------|
| Deep boundary | `wire_coerce` + TypedDict converters at JSON edge |
| Shallow risk | scattered `dict[str, object]` without named wire types |
| Navigation aid | [[graphify-architecture-map]] when graph fresh — not a substitute for module depth |

## Cross-References

- [[software-fundamentals-ai-era-pocock-2026]]: trap #4 and improve-architecture skill pattern
- [[asteroid-lab-wire-typing]]: interface-first wire contracts
- [[building-variants]]: deep game-data graph vs normalized domain tables
