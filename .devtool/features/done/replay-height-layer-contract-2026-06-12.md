---
title: Replay height layer belt contract (L=0 floor default)
status: done
modified: 2026-06-12
---

## Scope

Fix `map_height_layer` / `lab_replay_height_layer.js` inference: floor belts and shape transport default to **L=0**; L=1/L=2 only via Lift1/Lift2 tiles or explicit layer wire.

## Acceptance

- [x] `space_belt` + `SpaceBelt_Forward` → L=0
- [x] `SpaceBelt_Lift1*` / `SpaceBelt_Lift2*` (any `Lift*`) → L=1
- [x] `route_probe_path` shape → L=0
- [x] JS mirror parity cases updated
- [x] Canvas map-Z filter tests use floor vs lift2 fixtures
- [x] pytest replay height/paint subset green (220 replay tests)

## Progress

- 2026-06-12 — **implement** — rewrite `resolve_replay_height_layer`; sync JS; update tests.
- 2026-06-12 — **implement** — Lift* tiles infer L=1 (Lift2 from L1 void plane); L=2 explicit wire only.
