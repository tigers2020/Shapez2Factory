---
title: Agent Loop Design (Prompt vs Loop)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [agentic, governance, workflow]
sources: [documents/knowledge/raw/no more prompt but loop design.md]
confidence: medium
---

# Agent Loop Design

> **Authority:** working research wiki — not project canon.  
> **Source:** Lance Martin essay / video transcript — `raw/no more prompt but loop design.md` (Source ID `src-20260612-loop-design`)

## TL;DR (source)

**Prompt = driving interference.** **Loop = destination input.**

Loop needs three legs:

1. **Destination** — explicit done criteria (tests, gates, rubric)
2. **Position** — honest feedback (logs, scores, diff, CI)
3. **Reroute** — self-correction when off-path (retry, fix, re-run)

## Self-correction loop (source)

Anthropic pattern: human sets goal + rubric → model runs → scores → fixes → repeats until pass. Parameter-golf experiment: newer models change structure (not just hyperparams) when environment gives clear scoring + stop condition.

## Verifier separation (source, inference)

Self-grading traps the model in its own reasoning. **Separate verifier agent** with rubric only — same principle as editor vs author, or Bugbot vs implementer. Maps to this repo: contract + acceptance tests + CI gates, not "looks good."

## Memory loop — five steps (source)

For cross-session learning:

```text
fail → investigate → verify → distill rule → reference on next task
```

Weak models stop at fail or verify; strong loops turn failures into reusable rules (Continue Learning Bench).

## Project mapping (inference)

| Loop leg | This repo |
|----------|-----------|
| Destination | `AGENTS.md` acceptance, contract brief, `check_typing_debt.py` baseline |
| Feedback | `scripts/test_fast.ps1`, CI, `run_golden_loop.py` diagnostics |
| Reroute | Babysit PR, typing-zero loop, golden loop cycles |
| Verifier split | Regression tests, mypy/ruff gates — not agent self-claim |

## Cross-References

- [[vibe-coding-agentic-engineering-2026]]: when to use loops vs vibe
- [[software-fundamentals-ai-era-pocock-2026]]: TDD as headlight-speed limit
- [[asteroid-lab-wire-typing]]: typing-zero loop as bounded reroute campaign
