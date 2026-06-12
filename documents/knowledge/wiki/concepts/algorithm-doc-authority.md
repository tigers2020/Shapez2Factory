---
title: Algorithm Document Authority (Redirect Hub)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [asteroid-lab, governance]
sources:
  - documents/knowledge/raw/algorithm/authority-redirect.md
  - documents/knowledge/raw/algorithm/README.md
confidence: high
---

# Algorithm Document Authority

> **Raw ledger:** [`authority-redirect.md`](../../raw/algorithm/authority-redirect.md).  
> **Term map:** [`docs/ubiquitous-language.md`](../../../../docs/ubiquitous-language.md).

## Problem (source)

Many files still link to `documents/Algorithm/asteroid_lab_*.md`. Those paths are **absent** in the current worktree. Deleted archive is not implementation authority per [`raw/algorithm/README.md`](../../raw/algorithm/README.md).

## Use this order

1. **Code + tests** for behavior truth
2. **`docs/superpowers/specs/`** for artifact/replay contracts
3. **Wiki concepts** ([[asteroid-lab-algorithm]], [[island-mechanics]], [[asteroid-lab-wire-typing]])
4. **Raw redirect ledger** for stale link recovery
5. **Ubiquitous language** for naming (Candidate, Commit, SolverRun disambiguation)

## Active algorithm raw

| File | Status |
|---|---|
| `asteroid_lab_11_future_execution_plan_post_sequence.md` | `ACTIVE` — only current algorithm doc in `raw/algorithm/` |

## Cross-References

- [[asteroid-lab-algorithm]]: L2–L5 layer stack
- [[island-mechanics]]: copy JSON vs world map (replaces `asteroid_lab_01` for coordinates)
- [[asteroid-lab-wire-typing]]: replay semantic vs wire
- [[transport-capacity]]: throughput planning lens
- [[algorithm-doc-authority]]: this page

## Open questions

_None — redirect ledger, invariants router, and `RouteDomainSnapshotBuilder` implementation aligned 2026-06-12._
