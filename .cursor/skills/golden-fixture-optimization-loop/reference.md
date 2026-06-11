# Golden Fixture Optimization Loop — Reference

## Diagnosis taxonomy

Use exactly **one dominant bucket** per cycle.

| Bucket | Signals / diagnostics |
| --- | --- |
| invalidity gate failure | `valid=false` without a clear sub-bucket |
| failed source count | `l5_failed_sources:N` |
| route commit failure | `stack_failed_layer:layer_06_commit_validate` |
| route island / orphan | `route_island_count>0`, `orphan_count>0` |
| transport kind mismatch | `transport_kind_mismatch` |
| output stub mismatch | stub kind / placement diagnostics |
| connector / root selection | L4/L5 connector or root choice |
| source ordering conflict | priority / tie-break collisions |
| corridor blocked by L4/L5 | `l4_capacity:*`, routeable gap, inner fill |
| budget / time limit | timeout, `skipped_budget`, `TIMEOUT_FAIL_CLOSED` |
| scorer / evaluator issue | threshold or metric definition change needed |
| artifact / export issue | missing export when `valid=true` |

### `l5_failed_sources` priority

When this pattern dominates `diagnostics.json` → `failure_patterns`:

1. Instrument per-failed-source **reason code** (do not tune heuristics yet).
2. Publish reason histogram in cycle report.
3. Next cycle picks **one** reason bucket to fix.

Historical canon: PR-7/PR-8 moved from undifferentiated `l5_failed_sources:60` ([`2026-06-09-golden-loop-baseline.md`](../../../docs/superpowers/reports/2026-06-09-golden-loop-baseline.md), `valid=false`) to `capacity_overflow` bucket before PR-9 routing fix. Later [`2026-06-09-golden-loop-valid-baseline.md`](../../../docs/superpowers/reports/2026-06-09-golden-loop-valid-baseline.md) documents the first `valid=true` closure.

---

## Metric regression annotations

These are **not** dominant diagnosis buckets. Record them in the **Decision** section after selecting the true root-cause bucket.

| Annotation | Meaning |
| --- | --- |
| score improved but validity regressed | score ↑, `valid` ↓ — usually **FAILED** unless observability improved |
| validity fixed but score regressed | `valid=true`, score ↓ — **SUCCESS** only if regression is understood and accepted; otherwise **PARTIAL** / next hypothesis |

---

## Artifact archive layout

```text
var/experiments/golden_loop/archive/
  cycle-N-before/
    runs.jsonl
    best_config.json
    diagnostics.json
    best_result.shapez.txt   # if present
  cycle-N-after/
    (same files after verification run)
```

Never overwrite an existing archive directory. Bump `N` or add a timestamp suffix.

---

## PARTIAL — PR and merge rules

**May open PR when:**

- dominant failure count decreased, **or**
- diagnostics became strictly more specific, **or**
- observability improved without solver behavior regression

**Must not merge when:**

- only behavior changed and validity/diagnostics did not improve
- CI red
- merge gates in SKILL.md not satisfied

---

## Metric comparison

Compare before/after baseline runs:

| Field | Source |
| --- | --- |
| `valid` | `best_config.json` → `result.valid` |
| `score` | `best_config.json` → `result.score` |
| `miner_count` | result |
| `belt_count` | result |
| `routed_throughput` | result |
| `routed_source_count` | L05 metrics (when in diagnostics) |
| `failed_source_count` | L05 metrics |
| `route_island_count` | result |
| `orphan_count` | result |
| `anchor_f1_direct` | result |
| `anchor_f1_normalized` | result (diagnostic) |
| `golden_belt_similarity` | result |
| `failure_patterns` | `diagnostics.json` histogram |
| L4 capacity | `l4_capacity:*` diagnostics when present |

---

## Cycle report template

Path: `docs/superpowers/reports/YYYY-MM-DD-golden-loop-cycle-N.md`

```markdown
# Golden Loop Cycle N

## Baseline
- branch:
- commit:
- command:
- config grid:
- previous best score / validity:

## Diagnosis
- top failure:
- reason histogram:
- dominant bucket:
- hypothesis:

## Change
- files changed:
- behavior changed:
- tests added:

## Verification
- pytest:
- golden loop command:
- diagnostics diff:
- score diff:
- validity diff:

## Decision
- SUCCESS | PARTIAL | FAILED | REVERTED
- PR:
- merge SHA:
- next hypothesis:
```

---

## Fixture identity (frozen)

| Fixture | Role |
| --- | --- |
| `tests/fixtures/asteroid_golden/empty.shapez.txt` | Solver input |
| `tests/fixtures/asteroid_golden/genetic_sample_seeds.json` | Solver input (L3 catalog) |
| `tests/fixtures/asteroid_golden/game_data_snapshot_min.json` | Solver input |
| `tests/fixtures/asteroid_golden/golden.shapez.txt` | **Eval oracle only** |
| `tests/fixtures/asteroid_golden/golden_summary.json` | **Eval oracle only** |

---

## Success / failure criteria (expanded)

**SUCCESS (closure) if:**

- pytest targets pass
- golden loop command completes
- `valid=true`
- no hard regression in existing valid metrics
- PR diff matches stated hypothesis

Dominant failure count decrease **without** `valid=true` is **never** SUCCESS — use **PARTIAL**.

**PARTIAL if:**

- `valid=false` **and** dominant failure count decreases, **or**
- `valid=false` **and** diagnostics became strictly more specific than previous cycle, **or**
- observability improved without solver behavior regression

**Failure if:**

- command fails
- diagnostics missing
- validity regresses without compensating observability
- score improves only by changing evaluator thresholds in the same PR as solver behavior change
- `best_result.shapez.txt` missing when `valid=true` and copy export requested
- unrelated files changed

**Not failure by itself:**

- diagnostic-only fields in the same PR as solver behavior, when they are non-scoring
- non-scoring metrics added for reporting / observability
