# Golden Loop Valid Baseline Report (2026-06-09)

Canonical **valid** baseline for the Golden Fixture Optimization Loop after PR-7 through PR-10.
**No solver behavior was changed for this report** — evidence refresh only.

Supersedes the invalid MVP baseline in
[`2026-06-09-golden-loop-baseline.md`](2026-06-09-golden-loop-baseline.md) (`d13e8401`).

## Evidence chain (PR-7 → PR-10)

| PR | Scope | Outcome |
| --- | --- | --- |
| PR-7 | Diagnostics baseline + summarize script | Top failure `l5_failed_sources:60` |
| PR-8 | L5 failed-source instrumentation | 60/60 `capacity_overflow` bucket |
| PR-9 | Lane M-unit capacity accounting fix | `routed=76`, `failed=0`, throughput 30960 |
| PR-10 | Transport kind hard-validity normalization | `valid=true`, `transport_kind_mismatch` absent |

## Run context

| Field | Value |
| --- | --- |
| Branch | `feat/l4-1-greedy-inner-fill` |
| Commit | `1b6f3219b31282f09c8ba8d92ca67771da80e5e4` |
| Command | `python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy` |
| Config grid | `throughput_target_percent=80`, `budget_ms=60000`, `speed_tier=1` |
| Run timestamp (UTC) | `2026-06-09T17:14:48.078362+00:00` |

## Fixture identity (unchanged)

| Fixture | Contract |
| --- | --- |
| `tests/fixtures/asteroid_golden/empty.shapez.txt` | 578 entries, all `Layout_ShapeMinerExtension` |
| `tests/fixtures/asteroid_golden/golden.shapez.txt` | 1275 entries: 155 miners, 346 extensions, 774 belts |
| `tests/fixtures/asteroid_golden/golden_summary.json` | Pinned summary; bbox `[-16, 16, -20, 21]` |
| `genetic_sample_seeds.json` | Frozen PR-2 seed catalog |
| `game_data_snapshot_min.json` | Frozen PR-2 minimal game-data rules snapshot |

Golden map is **eval oracle only**. It is not solver input.

## Score breakdown

| Metric | Value | Notes |
| --- | --- | --- |
| `valid` | `true` | Hard validity passed |
| `best_valid` | `true` | Best config is valid |
| `score` | `310671085.2693799` | Valid-run formula |
| `miner_count` / `source_count` | `76` | L3 committed placements |
| `routed_source_count` | `76` | All sources routed (no L5 failures) |
| `failed_source_count` | `0` | No L5 failure diagnostics |
| `belt_count` | `246` | L5 route cells |
| `routed_throughput` | `30960.0` | L5-confirmed throughput |
| `anchor_f1_direct` | `0.095` | In score |
| `anchor_f1_normalized` | `0.658` | Diagnostic only |
| `golden_belt_similarity` | `0.043` | Jaccard on belt edges |
| `route_island_count` | `0` | Clean |
| `orphan_count` | `0` | Clean |

## Validity and diagnostics

From `diagnostics.json`:

```json
{
  "best_valid": true,
  "best_score": 310671085.2693799,
  "best_any_score": 310671085.2693799,
  "failure_patterns": {},
  "run_count": 1
}
```

- `transport_kind_mismatch`: **absent**
- L5 failure bucket / reason histogram: **none** (no failed sources)
- Run diagnostics: **none**

## Export artifact (`--write-best-copy`)

| Field | Value |
| --- | --- |
| `best_result.shapez.txt` | **present** (not committed; under `var/`) |
| Path | `var/experiments/golden_loop/best_result.shapez.txt` |
| Size (bytes) | `1852` |
| SHA-256 | `0f38593c73d5e4d047d298c6f4124fd56cc072291afd49f4c8e34fc04456d3aa` |

Artifact is a **generated local export**. This report pins presence, command, metrics, and hash — not the file in git.

## Historical contrast (invalid MVP baseline)

| Metric | MVP baseline (`d13e8401`) | This baseline (`1b6f3219`) |
| --- | --- | --- |
| `valid` | `false` | `true` |
| `score` | `0.0` | `310671085.27` |
| `routed_throughput` | `2160.0` | `30960.0` |
| `routed_source_count` | `16` | `76` |
| `failed_source_count` | `60` | `0` |
| Top failure | `l5_failed_sources:60` | _(none)_ |
| `best_result.shapez.txt` | absent | present |

Root causes addressed in PR-9 (lane M-unit load) and PR-10 (transport kind family compare).

## Verification

```text
pytest tests/unit/asteroid_lab/experiments/ -q  → 40 passed
```

Recorded on branch `pr-11-golden-valid-baseline-refresh` at commit `1b6f3219`.

## Regenerating this baseline

```powershell
git checkout feat/l4-1-greedy-inner-fill
python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy
python scripts/summarize_golden_loop_diagnostics.py
pytest tests/unit/asteroid_lab/experiments/ -q
```

Update this report only when the canonical command, fixture contract, or post-PR-10 validity gates change.
