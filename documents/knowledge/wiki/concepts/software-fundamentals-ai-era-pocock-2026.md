---
title: Software Fundamentals in the AI Era (Pocock 2026)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [agentic, architecture, governance]
sources:
  - documents/knowledge/raw/Software Fundamentals Matter More Tha nEver.md
  - documents/knowledge/raw/AI 코드 망치는 6가지와 해결법. md
confidence: medium
---

# Software Fundamentals in the AI Era

> **Authority:** working research wiki — not project canon.  
> **Speaker:** Matt Pocock — *Software Fundamentals Matter More Than Ever* (AI Engineer conf, Apr 2026).  
> **Raw:** English transcript + Korean commentary — Source ID `src-20260612-pocock-fundamentals`

## Core claim (source)

Bad code is **more expensive** in the AI era, not cheaper. Specs-to-code that **divests from design** fails; fundamentals (modules, tests, language, interfaces) matter **more**.

> **AI gets lost in mazes it built** — shallow modules become unreadable graphs even for the agent that wrote them.

## Six traps → prescriptions (source)

| # | Trap | Prescription |
|---|------|--------------|
| 1 | AI builds the wrong thing (no shared design concept) | **Grill Me** — interview until shared understanding (`/grill-me` skill pattern) |
| 2 | No shared vocabulary (verbose / inconsistent terms) | **Ubiquitous language** — extract terms from codebase into shared markdown dictionary |
| 3 | Code looks right but doesn't run; feedback too late | **TDD** — tests force small steps; don't outrun headlights (Pragmatic Programmer) |
| 4 | Shallow modules — maze the AI can't navigate | **Deep modules** (Ousterhout) — simple interface, rich interior; consolidate related code |
| 5 | Code volume explodes; human can't track | **Grey-box strategy** — human designs interface; delegate interior; verify at boundary |
| 6 | Specs-to-code skips design investment | **Invest in system design daily** (Kent Beck) — strategist vs field sergeant |

## Specs-to-code critique (source)

Compiler-from-spec assumes code is disposable. Pocock: when code is cheap to generate but expensive to wrong, **design and boundaries** become the bottleneck — aligns with this repo's contract-first `AGENTS.md` workflow (inference).

## Related raw (deferred)

- `raw/2018-John Ousterhout-A Philosophy of Software Design.pdf` — deep/shallow module primary source; not ingested to wiki yet (PDF).

## Cross-References

- [[agent-loop-design]]: loops vs prompt tuning
- [[vibe-coding-agentic-engineering-2026]]: risk-tiered rigor
- [[asteroid-lab-wire-typing]]: boundary typing as grey-box interface work
- [[graphify-architecture-map]]: architecture navigation vs shallow-module maze
