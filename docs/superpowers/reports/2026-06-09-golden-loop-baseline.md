# Golden Loop Baseline Report (2026-06-09)

Canonical baseline for the Golden Fixture Optimization Loop after MVP PR-1 through PR-6.
No solver behavior was changed for this report.

## Run context

| Field | Value |
| --- | --- |
| Branch | `feat/l4-1-greedy-inner-fill` |
| Commit | `d13e8401e950482d35223a9301c90d79b3f420e6` |
| Command | `python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy` |
| Config grid | `throughput_target_percent=80`, `budget_ms=60000`, `speed_tier=1` |
| Run timestamp (UTC) | `2026-06-09T14:22:57.567321+00:00` |

## Fixture identity (oracle only)

| Fixture | Contract |
| --- | --- |
| `tests/fixtures/asteroid_golden/empty.shapez.txt` | 578 entries, all `Layout_ShapeMinerExtension` |
| `tests/fixtures/asteroid_golden/golden.shapez.txt` | 1275 entries: 155 miners, 346 extensions, 774 belts |
| `tests/fixtures/asteroid_golden/golden_summary.json` | Pinned summary; bbox `[-16, 16, -20, 21]` |
| `genetic_sample_seeds.json` | Frozen PR-2 seed catalog (36 entries at export time) |
| `game_data_snapshot_min.json` | Frozen PR-2 minimal game-data rules snapshot |

Golden map is **eval oracle only**. It is not solver input.

## Output files generated

| Path | Generated | Notes |
| --- | --- | --- |
| `var/experiments/golden_loop/runs.jsonl` | Yes | 1 JSONL row for the single config |
| `var/experiments/golden_loop/best_config.json` | Yes | Best record (invalid run; score 0) |
| `var/experiments/golden_loop/diagnostics.json` | Yes | Aggregated failure patterns |
| `var/experiments/golden_loop/best_result.shapez.txt` | **No** | Expected: no valid run → no best valid artifacts to export |

`--write-best-copy` only writes `best_result.shapez.txt` when a **valid** run exists.
This baseline had `valid=false`, so export skip is contract-correct.

## Score breakdown

| Metric | Value | Notes |
| --- | --- | --- |
| `valid` | `false` | Hard gate failed |
| `score` | `0.0` | Invalid runs score 0 |
| `miner_count` | `76` | L3 committed placements |
| `belt_count` | `95` | L5 route cells |
| `routed_throughput` | `2160.0` | L5-confirmed throughput (partial routing) |
| `anchor_f1_direct` | `0.095` | In MVP score |
| `anchor_f1_normalized` | `0.658` | Diagnostic only |
| `golden_belt_similarity` | `0.022` | Jaccard on belt edges |
| `route_island_count` | `0` | Not the bottleneck |
| `orphan_count` | `0` | Not the bottleneck |

## Validity and diagnostics

**Why `valid=false`:** `l5_failed_sources:60`

From `diagnostics.json`:

```json
{
  "best_valid": false,
  "best_score": null,
  "failure_patterns": { "l5_failed_sources:60": 1 },
  "run_count": 1
}
```

Hard validity requires L5 `failed_source_count == 0` and all sources routed.
This run committed some routes (`routed_throughput > 0`) but **60 L5 sources failed**.

## Interpretation

### L3 vs L5

- L3 placed **76 miners** — rim greedy is producing candidates.
- L5 routed throughput is **non-zero** (2160/min) — partial routing succeeds.
- Final stack is still **invalid** because a large failed-source tail remains.

### Anchor F1: direct vs normalized

| Metric | Value | Reading |
| --- | --- | --- |
| `anchor_f1_direct` | 0.095 | Low coordinate match vs golden extractor anchors |
| `anchor_f1_normalized` | 0.658 | Higher shape/relative layout similarity |

Gap suggests **pattern/relative placement is closer than absolute grid alignment**.
Tuning should not assume “move everything to golden coordinates”; focus on why L5 cannot commit routes for 60 sources.

### Route topology

`route_island_count=0` and `orphan_count=0` mean the problem is **not** disconnected belt islands or orphan cells.
The bottleneck is **source-level L5 route commit failure**, not post-route connectivity cleanup.

## Top failure (PR-8 target)

```text
l5_failed_sources:60
```

Before changing L5 costs or heuristics, PR-8 should instrument **per-failed-source reason codes**, for example:

- output stub / `m_output_stub` placement
- nearest L2 connector or L5 root distance
- `failure_reason` from `Layer05Failure`
- interior / equipment blocking cells
- route probe length vs committed path
- ordering conflict with earlier routes

Hypothesis buckets to validate in PR-8:

1. Wrong source output stub
2. L4 inner fill blocking corridor
3. Poor L5 root / target selection
4. Route budget or capacity limit
5. Source ordering blocking later sources
6. Transport kind / connector mapping mismatch

## Recommended next PRs

| PR | Scope | Purpose |
| --- | --- | --- |
| **PR-8** | L5 failed-source diagnostics expansion | Decompose `l5_failed_sources:60` into reason histogram |
| PR-9+ | Single-knob solver tuning | Only after PR-8 identifies dominant failure class |

Do **not** start with broad L5 cost tuning or L3 bundle priority changes until PR-8 data exists.

## MVP closure checklist

```text
PR-1  canonical fixture + loader
PR-2  frozen seeds + game data
PR-3  solver artifact capture
PR-4  artifact-level eval
PR-5  loop script
PR-6  blueprint export (opt-in)
```

Golden Fixture Loop MVP: **CLOSED** at commit `d13e8401`.

## Regenerating this baseline

```powershell
git checkout feat/l4-1-greedy-inner-fill
python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy
python scripts/summarize_golden_loop_diagnostics.py
```

Re-run `pytest tests/unit/asteroid_lab/experiments/ -q` after any infra change.
Update this report only when the canonical command or fixture contract changes.
