# boundary-m-repack — Layer 03 outer-rim M extractor greedy redesign (PR-B)

**Status:** SUPERSEDED — see [`../2026-05-31-layer-03-algorithm-reset/`](../2026-05-31-layer-03-algorithm-reset/README.md) (2026-05-31). Historical PR-B reference only.
**Date:** 2026-05-30
**Type:** algorithm enhancement (`contract change` + `implementation change`)
**Design (SoT):** [`../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md)
**Unblocks:** [`PR-CLI-2e`](../2026-05-30-asteroid-lab-cli-first/pr-cli-2e-l3-gated-move.md) (gated on PR-B merged + green)
**Closing rule:** No commit / push / PR / merge / `CLOSED` without explicit user request ([`AGENTS.md`](../../../../AGENTS.md)).

---

## Goal

Maximize mining yield by placing the highest-yield canonical bundle **`m3e_01` (miner + 3 extensions)**
along the outer rim, degrading 3→2→1 where the inward field is shallow, while keeping all M/E
equipment on the field and using exterior void only for the output stub + transport route.

## Scope

- Generalize `layout_seed_at_anchor` to place a miner + up to N inward extensions (straight chain),
  with in-layout degradation and clean reject at 0.
- Make `m3e_01` the default greedy seed.
- Wire `greedy_pass1` / `greedy_pass2` to pass `seed.extension_count` to the layout.
- Ensure committed multi-extension placements surface through append / overlay / summary / replay.
- Fix replay extension rotation for chained extensions.

## Non-goals

- No PR-CLI-2e / core relocation (BA-3 holds).
- No Layer 4 re-enable (stays disabled).
- No `route_domain` re-ownership, no replay/metrics used as solver input.
- No seed rank/score convention unification (documented follow-up).

## Behavior contract

See design spec [Behavior contract](../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md#behavior-contract-normative)
(C1…C8). Summary:

```text
- PR-B is an algorithm enhancement
- default greedy seed = m3e_01
- layout = miner depth0 + extensions depth1..3 inward chain
- degrade = 3 -> 2 -> 1 (in-layout)
- actual extension_count = len(extension_cells)
- M/E equipment ⊆ field
- output stub + route may use external void
- route does not require a preinstalled belt; field traversal is costed higher than void
- Layer 4 remains disabled
- no PR-CLI-2e / core relocation
```

## Forbidden behavior

- M/E equipment in exterior void.
- Route failure solely due to missing preinstalled belt.
- Algorithm edits inside PR-CLI-2e relocation.
- Using replay/summary/smoke output as algorithm input.

## Verification (status)

- **Gate A (Lab gate):** `python -m pytest tests/unit/asteroid_lab/layers/ -v` — passed.
- **Additional replay regression:** `python -m pytest tests/unit/asteroid_lab/replay/ -v` — passed.
- **Combined local:** `python -m pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/replay/` — 173 passed, 2 warnings.
- **ruff / black:** changed modules clean.
- **mypy:** changed L3 + replay modules — Success, 13 files (repo-wide mypy not claimed).
- **Gate C smoke:** manual DB smoke recorded **not reproducible** (no deterministic project fixture
  slug; project seeding out of scope). Gate-C-equivalent deterministic evidence: `pytest
  tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py test_run_solver_management_command.py
  test_lab_replay_timeline_layer03_runtime.py` — 7 passed (full run-solver L3 path with m3e default).
  See [checklist Phase 6](checklist.md).

## Risks / follow-up

- `uncertain:` seed rank/score convention mismatch — no behavioral impact (single default seed); unify
  in a separate PR.
- Branched canonical topology would invalidate the straight-chain assumption (excluded by audit).
