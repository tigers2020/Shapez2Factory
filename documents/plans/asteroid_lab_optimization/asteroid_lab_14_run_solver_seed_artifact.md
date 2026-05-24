# Asteroid Lab — Sequence 14: Run Solver Seed Artifact Boundary


> **Plans snapshot:** Not mirrored in `documents/Algorithm/`. For live contracts see [`documents/Algorithm/`](../../Algorithm/). **PR-F (2026-05):** dense server coords removed from product code.

> **Status:** ACTIVE (implement after human approval). Lab single `ReplayTrack`·append authority follows `rollback_baseline_lab_replay_timeline.md` and `asteroid_lab_00_overview.md` §1b.

## 1. Role (Architecture Reviewer consensus)

Endpoints (`create-project` vs `run-solver`) are already separated, but **inside Run Solver** the pipeline equivalent to inspection prep runs again.

```text
copy string decode (decode_copy_string) → not done in Run Solver (current).
decoded_json → snapshot → cleanup → reconstruction → optimization input prep → re-executed every Run Solver (problem).
```

Precise answer to **“does it run the same code?”** is above. Splitting buttons **has meaning**, but fully satisfying UI contract “append on saved baseline” requires changing Run Solver internals.

## 2. Core problem: mixing two authorities

Currently `run_lab_solver_optimization_for_map_input` roughly uses both:

```text
baseline full_map
  ← extracted from last ReplayFrame on ReplayTrack

optimization input (cleanup / reconstruction / OptimizationInput / route seed)
  ← snapshot rebuilt from AsteroidMapInput.decoded_json and recomputed
```

Weak guarantee these always yield identical results. Coordinate·flatten·reconstruction boundary issues **recur in Run Solver**.

## 3. Target long-term structure

```text
Save/Open Project (only baseline·seed creation segment)
  → copy_code stored
  → decoded_json stored
  → cleanup / reconstruction run (inspection path)
  → canonical inspection ReplayTrack created
  → OptimizationSeedArtifact stored (optimizer-only authority)

Run Solver
  → map_input_id·canonical inspection ReplayTrack validation
  → load OptimizationSeedArtifact
  → run optimizer only
  → append optimization_* frames after same ReplayTrack
```

**Forbidden (Run Solver):**

```text
Re-run cleanup / reconstruction from AsteroidMapInput.decoded_json to build optimization input.
```

## 4. Implementation option comparison

### Option A — Optimization seed persistence (recommended)

**Role:** persisted artifact for **optimizer input only**, not `ReplayFrame`.

Storage timing example: immediately after `build_initial_replay_for_map_input` success (or explicit same-transaction policy).

Storage location candidates:

```text
(1) AsteroidMapInput.optimization_seed_json  — simple, one migration column
(2) AsteroidOptimizationSeed (separate model) — map_input_id, replay_track_id, version, JSON fields separated
```

Example fields (names adjusted at implementation):

```text
map_input_id
replay_track_id (canonical inspection; which track seed is valid with)
schema_version
cleanup_snapshot_json (or serialized CleanupResult)
reconstruction_summary_json (optional)
optimization_input_json
route_domain_seed_json (optional; if builder restores only from seed)
created_at
```

**Pros:** create-project vs run-solver contract separation, remove coord/flatten re-entry in run-solver, simpler append debugging.

**Cons:** seed schema·version management, migration·invalidation policy (regenerate trigger on code change) needed.

### Option B — ReplayTrack specific frame as canonical source

Example: use `full_map` of specific `frame_key` as optimization input source.

**Cons:** replays algorithm input, conflicts with `asteroid_lab_00_overview.md` §1 “Replay-driven algorithm forbidden” philosophy. **Not recommended.**

### Option C — keep recompute + strict equivalence tests

Save/Open output and Run Solver recompute must pass byte/structural equality.

**Cons:** contract never clarifies as “append on baseline”; same-class bugs repeat. **Temporary workaround.**

## 5. Recommended: Option A

Example names: `OptimizationSeedArtifact` / `AsteroidOptimizationSeed` (unify one in implementation).

```text
ReplayFrame = output-only (existing principle)
OptimizationSeedArtifact = canonical optimizer input (new authority)
```

## 6. Key contract wording for plan (EN)

```text
Save/Open Project is the only endpoint allowed to decode, cleanup, and reconstruct a map input.

Run Solver must not regenerate cleanup or reconstruction from AsteroidMapInput.decoded_json.
Run Solver consumes a persisted OptimizationSeedArtifact produced by the canonical inspection build.

ReplayFrame remains output-only.
OptimizationSeedArtifact is the canonical optimizer input.
```

One-line summary:

```text
Save/Open creates the canonical baseline and optimization seed.
Run Solver only optimizes against that seed and appends frames.
```

## 7. Implementation order (after approval)

```text
1. Review approval of this doc·schema draft
2. Decide model or JSON column + schema_version
3. Create·store OptimizationSeedArtifact after inspection success on Save/Open path
4. Remove snapshot→cleanup→reconstruction path in Run Solver; load seed only
5. integration test:
   - seed exists after Save/Open
   - Run Solver reads seed only (assert no decoded_json-based reconstruction calls)
   - frame count increases on same replay_track
6. static boundary (if possible): web `asteroid_lab_optimization_run` does not depend directly on cleanup/reconstruction builders — move to seed loader·deserialization module
```

## 8. Existing code anchors (reference)

- Save/Open·inspection: `django_apps/web/views/public_pages.py` — `asteroid_miner_layout_create_project`, `build_initial_replay_for_map_input`
- Run Solver: `django_apps/web/views/public_pages.py` — `asteroid_miner_layout_run_solver`; `django_apps/web/services/asteroid_lab_optimization_run.py` — `run_lab_solver_optimization_for_map_input`
- Snapshot load: `django_apps/asteroid_lab/services/cell_snapshot_service.py` — `build_decoded_blueprint_snapshot_from_input`

## 9. Approval gate

- Confirm seed field scope in this doc (minimum: is `optimization_input_json` alone sufficient, or route seed needed too)
- Decide migration·existing projects without seed Run Solver behavior (400 + “re-save inspection only” vs automatic backfill)

---

**Next action:** implement from step 2 above after human approval. Do not change recompute path in `asteroid_lab_optimization_run.py` before implementation.
