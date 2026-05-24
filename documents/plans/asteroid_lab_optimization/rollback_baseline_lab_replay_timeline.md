# Rollback Baseline — Lab Replay Timeline Refactor Agent Boundary


> **Plans snapshot:** Not mirrored in `documents/Algorithm/`. For live contracts see [`documents/Algorithm/`](../../Algorithm/). **PR-F (2026-05):** dense server coords removed from product code.

## Purpose

This document fixes the **boundary (authority)** that agents and humans must follow during **unified Lab replay refactor** work.

After intentionally rolling back to the state before a separate Optimization replay **front/runtime track** was introduced, optimization-stage replay is rebuilt **only by appending frames to the existing Lab replay timeline**.

**Sequence 3B-R (unified RTTP append):** [`docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md`](../../docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md)

## Baseline

Authoritative baseline commit (parent of the commit immediately before rollback):

```text
10b3b966081496c3d67394d87780dc17e801c512^
```

The **current local checkout** aligned to this baseline is the implementation authority. Remote latest `HEAD` or file content from later commits is not authority.

## Agent boundary (required)

Agents work **only against the current local checkout**.

Forbidden:

```text
- Opening GitHub remote HEAD to reference implementation details
- Searching newer commits to find optimization replay code
- Copying files/functions from commits after 10b3b966081496c3d67394d87780dc17e801c512
- Recreating prior separate Optimization replay implementation from memory/inference
```

Files·functions·classes·tests·docs that do not exist in this checkout must **not be reproduced by looking at later commits.**

## Forbidden: separate Optimization replay symbols

The following are regression signals toward removed **dual-track** implementation. Stop and remove if they appear in runtime/front replay paths (exception: explicitly kept for historical documentation only).

```text
optimization_replay_frames
optimization_replay_payload_for_project
optimization-replay-json
optimizationReplayTrack
optimizationReplayFrameIndex
renderOptimizationReplayHud
replaceOptimizationReplayPayload
optimization_replay_attach
dual-track optimization replay
no implicit sync policy
```

### Exception (visual only): optimization overlay on unified timeline

The following are allowed as **output-only visual layers** stacked only on the Lab base grid inside a single `lab_replay_frames_json`·single `currentFrameIndex` — **not dual-track**.

```text
projectOptimizationReplayFrameToLabOverlay   # single timeline frame → overlay instruction
lab-optimization-overlay-layer               # DOM layer above #lab-replay-grid
```

Prohibitions remain: separate optimization replay JSON script, a **second index** like `optimizationReplayFrameIndex`, two-timeline sync, exposing separate payload via `optimization_replay_attach`.

## Target architecture

Only **one timeline** exists for replay.

```text
ReplayTrack / ReplayFrame
lab_replay_frames_json
currentFrameIndex
#lab-replay-grid
```

Optimization-stage events are **appended at the end** of the existing Lab replay frame sequence.

Not allowed: second optimization replay payload, second replay index, sync layer between two timelines.

## Required behavior (acceptance example)

If inspection/reconstruction replay has 67 frames and optimization emits 15 replay events:

```text
final lab_replay_frames_json frame count = 82
appended frame_index = 67..81 (continuous from 0)
```

Appended optimization frames are selected·rendered **only via the existing Lab scrubber·grid path**.

## Implementation rules

**Do not salvage the prior separate Optimization replay implementation.**

Unified replay extension is designed·implemented **only on top of the rollback baseline**.

Allowed:

```text
Optimization algorithm emits internal debug/event objects
Those objects are immediately adapted to Lab ReplayFrame-compatible frames
```

Forbidden:

```text
Storing/exposing optimization replay as a separate UI/runtime track
```

## Preflight

### Bash

```bash
git rev-parse HEAD
git merge-base --is-ancestor 10b3b966081496c3d67394d87780dc17e801c512^ HEAD
git status --short
git grep -n "optimization_replay\|optimization-replay-json\|optimizationReplayTrack\|optimizationReplayFrameIndex" || true
```

If `git merge-base --is-ancestor` is non-zero (fails): current `HEAD` does not include the baseline as ancestor.

Exit code `1` from `git grep` (no matches) is **normal**. `2` or above is treated as error.

### PowerShell

```powershell
git rev-parse HEAD
git merge-base --is-ancestor 10b3b966081496c3d67394d87780dc17e801c512^ HEAD
if ($LASTEXITCODE -ne 0) { throw "HEAD is not based on rollback baseline" }

git status --short

git grep -n "optimization_replay\|optimization-replay-json\|optimizationReplayTrack\|optimizationReplayFrameIndex"
if ($LASTEXITCODE -gt 1) { throw "git grep failed" }
```

Exit code `1` from `git grep` (no matches) is allowed. `0` means matches exist (stop/investigate per policy).

## Acceptance tests (verification perspective)

```text
- Run Solver JSON response exposes only one lab_replay_frames_json timeline.
- Optimization-stage frames are appended to the same list.
- frame_index is continuous from 0 through final_count - 1.
- Rendered project HTML contains no `optimization-replay-json` / `optimizationReplayTrack` / `optimizationReplayFrameIndex` strings.
- (Exception) `#lab-optimization-overlay-layer` and `data-lab-optimization-overlay-enabled` are allowed as **single-timeline visual layer**.
- Existing Lab scrubber can select appended optimization frames.
- Replay is output-only and not used as solver input.
```

## Verification commands

```bash
python -m pytest
python -m ruff check .
python -m mypy .
python -m black --check .
```

Quick single-directory view (example):

```bash
python -m pytest tests/unit/asteroid_lab/
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py
```

## Recommended next steps

1. Include this document in save/approval workflow.
2. Clean working tree (stash·commit·discard policy agreed).
3. Create new branch from baseline:

```bash
git checkout -b refactor/unified-lab-replay-from-baseline 10b3b966081496c3d67394d87780dc17e801c512^
```

4. Put the following at the start of agent session prompts:

```text
Read and obey documents/plans/asteroid_lab_optimization/rollback_baseline_lab_replay_timeline.md before editing code.
```

## Related plan documents (legacy narrative alignment)

If the files below **do not yet exist** or past drafts treated **Lab / Optimization dual-track·independent `optimizationReplayFrameIndex`** as invariant, implementation·doc authority follows **this rollback doc + `asteroid_lab_00_overview.md` §1b·1c**. Phase 9·10 plan bodies have *Unified Lab Replay Timeline* superseded notes at top.

```text
documents/plans/asteroid_lab_optimization/asteroid_lab_09_replay_debug.md
documents/plans/asteroid_lab_optimization/asteroid_lab_10_development_sequence.md
(planned) asteroid_lab_12_runtime_replay_wiring.md
(planned) asteroid_lab_13_replay_payload_scalability.md
```

## Note on Git's role

```text
1. Git is only a device to fix the work baseline.
2. Agent memory·search·latest-pattern regeneration is blocked by this doc·prompt·grep gates.
```
