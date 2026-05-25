# RTTP v1 MacroBundleT3 — Historical Tombstone

**Status:** `PAUSED / DO NOT EXECUTE`  
**Original date:** 2026-05-23  
**Cleanup:** 2026-05-25 roadmap drift cleanup

This plan is intentionally reduced to a tombstone. The original checklist said `Plan status: Ready for execution`, but the active roadmap/current-plan state now holds MacroBundle T3 under **PAUSE**.

Do not restore or execute the removed PR-A → PR-H checklist without a new approved macro-unpause spec and an explicit `documents/ai/current_plan.md` ACTIVE row.

## Current authority

- Queue authority: [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)
- Roadmap: [`../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`](../2026-05-24-asteroid-lab-catalog-rttp-roadmap.md)

## Preserved macro constraints

```text
macro_only_mode=False remains the default runtime path.
macro_only runtime remains gated.
Macro tests may not be unskipped merely because this historical plan exists.
Macro PR-B follow-up requires a dedicated macro child-pool fixture spec.
Do not weaken FOT guards to make macro candidates appear.
```

## Forbidden from this retired plan

- Starting macro DTO/compiler/selector/commit work from this file.
- Adding or unskipping macro E2E tests without a dedicated fixture spec.
- Mixing singleton `BundleCandidate` and `MacroBundleCandidate` genome slots by implication.
- Promoting MacroBundle T3 into the v0.1 11-step core roadmap.
- Treating macro replay/debug payload as algorithm input.

## Reason

`current_plan.md` currently allows only v0.1 next-track selection: GA, macro unpause, or capacity C-GATE. Macro unpause is itself a track-selection candidate, not an implementation authorization.
