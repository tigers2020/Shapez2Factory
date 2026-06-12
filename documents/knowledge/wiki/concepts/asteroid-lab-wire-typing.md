---
title: Asteroid Lab Wire Typing (Any Boundary)
created: 2026-06-11
updated: 2026-06-12
type: concept
tags: [asteroid-lab, governance, architecture]
sources: [documents/ai/manuals/typing_contracts.md, docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md]
confidence: high
---

# Asteroid Lab Wire Typing

**Canon:** `documents/ai/manuals/typing_contracts.md` (process authority: `AGENTS.md`). Wiki page is retrieval summary only.

## Problem (source)

Was ~1,454 `typing.Any` uses — mostly `dict[str, Any]` in `django_apps` replay/UI/import, not solver core. **Campaign complete:** `any_token_total=0` on `master@597cdaf2` (PR #284 slice-1 + PR #285 slices 2–37). Guard: `scripts/check_typing_debt.py`.

## Core invariants

```text
Semantic authority → frozen dataclass
Wire authority      → named TypedDict
Raw dict[str, Any]  → decode/import boundaries only
Converters          → only legal dataclass ↔ wire path
```

Shared aliases: `django_apps/asteroid_lab/typing_boundary.py` (`RawJsonObject`, `JsonValue`).

## Module pattern

| Role | Pattern | Example |
|------|---------|---------|
| Semantic | `*_dtos.py` | `ReplayOverlayCell` |
| Wire | `*_wire.py` | `ReplayOverlayCellWire` |
| Converter | `*_serialization.py`, `overlay_wire_contract.py` | `overlay_cell_to_wire()` |

TypedDict: `total=True` default; optional keys via `NotRequired`. No hand-built wire dicts at call sites.

## Authority map (replay)

| Module | Owns |
|--------|------|
| `timeline_dtos.py` | Semantic frame types |
| `timeline_serialization.py` | Wire + deserialize validation |
| `overlay_wire_contract.py` | Overlay occupancy vs `output_transport_kind` |
| `effective_cell_view.py` | UI merged cell read model |
| `lab_timeline_adapter.py` | Assembler projection |

Runtime wire **forbidden** as placement/routing/validation input.

## Rollout status (source + inference)

| Phase | Scope | Status |
|-------|-------|--------|
| 0 | `typing_boundary.py`, ban-test inventory | **merged** `master@223eabc5` (PR #280) |
| 1 | Replay wire TypedDict + converters | **merged** #280 |
| 4 | Remove `EffectiveCellView.to_wire()`; strict mypy on `django_apps/asteroid_lab/replay/`; CI gate `mypy src django_apps/asteroid_lab/replay` | **merged** `master@cc33840a` (PR #283) |
| 5 | Repo-wide `typing.Any` elimination; `wire_coerce.py` JSON narrowing; `dict[str, object]` repair | **merged** `master@597cdaf2` (PR #285) |
| 2+ | Service DTOs, full `django_apps` strict beyond replay | **deferred** — design spec |

## Cross-References

- [[asteroid-lab-algorithm]]: layer stack vs replay projection
- [[transport-system]]: `space_belt` / `space_pipe` cell kinds on wire
- [[game-data-manifest]]: raw JSON import boundaries
