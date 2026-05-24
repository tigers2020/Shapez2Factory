# Protected Corridor Drift

## canonical baseline

- `12_protected_corridor.md`
- `08_step4_routing.md`
- `09_step5_pass3_transport.md`

## live finding

The live `django_apps/asteroid_lab` tree has no runtime state, DTO, validation, or replay layer for protected corridor lifecycle. Related strings, enums, modules, and test surfaces are all absent.

The issue is not “misimplemented corridor” but “canonical core system absent from live tree entirely.”

## Impact

| Area | Live status | Risk | Severity | Confidence | Action |
|---|---|---|---|---|---|
| routing core | no corresponding module | cannot perform canonical routing refactor in current tree | `P1` | High | `freeze` |
| replay layer | no hard/soft corridor overlay | UI contract cannot carry future corridor state | `P1` | High | `migrate` |
| validation layer | no corridor invariant | field naming collision risk when final validation expands | `P1` | High | `migrate` |
| tests | no corridor lifecycle tests | no regression baseline for follow-up implementation | `P2` | High | `test-only` |

## early-phase guidance

- Do not force corridor concepts into `asteroid_lab`.
- Redefine canonical/live boundary first.
- Introduce corridor in a separate namespace after solver runtime package actually exists.

## freeze note

In early refactor phases, do not reinterpret `reconstruction/*`, `existing_layout_inspection.py`, or web replay UI as corridor placeholders. That conflates canonical protected corridor with simple inspection overlay.
