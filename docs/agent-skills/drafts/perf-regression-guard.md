# Draft record — perf-regression-guard

> **Status:** DRAFT — not approved. Do not use as implementation guide until human review.
> **Hermes classification:** PARTIAL
> **Command:** `hermes -z "[PLAN_TO_SKILL_REQUEST]..." -s perf-regression-guard` (CWD: repo root)
> **Source:** local skill `C:\Users\hyper\AppData\Local\hermes\skills\perf-regression-guard\SKILL.md`

## Human review flags (Cursor)

- Hermes claimed `python manage.py run_solver` does not exist — **incorrect**. Command exists at `django_apps/asteroid_lab/management/commands/run_solver.py`; `AGENTS.md` § Validation references it.
- Draft proposes new `test_perf_regression_guard.py` — **not implemented**; runtime change is out of scope until approved.
- `.benchmarks/results.json` commit policy conflicts with prior empty `.benchmarks/` — needs explicit repo decision before baseline commit.
- `psutil` is not in `pyproject.toml` dev dependencies — verify before memory metrics.

## Research summary (Hermes)

- Local skill is Unix-biased (`time`, `wc`, `diff`, `pygount`); Windows-incompatible.
- `pytest-benchmark` not in repo; adding it is a dependency/policy change.
- Prefer Python-native timing (`time.perf_counter()`), artifact size invariants, optional `psutil` RSS.
- Baseline: normalized JSON stats only — not raw timestamp logs.

## Rejected alternatives (Hermes)

- `pytest-benchmark` plugin (no infra; global pytest impact)
- Shell `time` on Windows
- Committing raw `.benchmarks/*.log`
- CI benchmark without explicit user approval
- Patching local skill in place without repo draft

## Implementation checklist (Hermes — pending approval)

1. [ ] Decide entry point: `run_solver` mgmt command vs in-process test fixture
2. [ ] `.benchmarks/results.json` policy + gitignore review
3. [ ] `tests/unit/asteroid_lab/test_perf_regression_guard.py` with `@pytest.mark.perf` (excluded from `test_fast.ps1`)
4. [ ] Initial baseline run on fixed slug
5. [ ] No approved skill promotion without review

## Validation checklist (AGENTS.md § Validation)

- [ ] `python manage.py check`
- [ ] `powershell -File scripts/test_fast.ps1` (perf test excluded)
- [ ] `ruff check .`
- [ ] `mypy django_apps config src`
- [ ] `black --check .`

---

## SKILL.md draft (below — pending approval)

---
name: perf-regression-guard
description: >-
  Performance regression guard for core (src/shapez2_factory/) refactoring.
  Measures solver pipeline wall-time, process memory, and artifact size against a
  committed baseline. Runs as pytest tests, not shell scripts.
disable-model-invocation: false
metadata:
  owner: "project"
  risk: "low"
  requires_validation: true
  status: draft
  classification: partial
---

# Performance Regression Guard

## Purpose

After refactoring files inside `src/shapez2_factory/`, verify that solver
pipeline performance has not meaningfully regressed. Guards against structural
complexity increases (import chain bloat) and runtime slowdowns from Python
overhead changes.

## When to use

- After any PR that changes `src/shapez2_factory/` module boundaries, imports, or algorithms
- Before marking a core extraction refactor as complete
- NOT needed for Django app changes, UI changes, or test-only changes

## Inputs required

1. Asteroid slug — same slug before AND after refactoring
2. Baseline file: `.benchmarks/results.json` (created on first approved run)
3. `scripts/test_fast.ps1` passes first

## Metrics and thresholds

| Metric | Measurement | Threshold | Notes |
|---|---|---|---|
| solver wall-time ms | `time.perf_counter()` around pipeline call | +20% over baseline | Solver step only, not Django setup |
| process peak RSS MB | `psutil` if available | +500MB or +40% | Wall-time-only fallback if no psutil |
| artifact JSONL lines | line count of replay output | >5% deviation | Structural change signal |
| artifact total bytes | file size of replay output | >10% growth without spec change | Data bloat signal |
| core file/line count | `os.walk` over `src/shapez2_factory/` | sudden jump | Architectural smell |

## Execution procedure

### 1. Pre-condition

```powershell
powershell -File scripts/test_fast.ps1
```

### 2. Run perf guard (when implemented)

```powershell
python -m pytest tests/unit/asteroid_lab/test_perf_regression_guard.py -v --slug=<asteroid-slug>
```

Or interim manual check via existing CLI (review entry point before approval):

```powershell
python manage.py run_solver --slug <asteroid-slug>
```

### 3. On threshold breach

Use `cProfile` on the solver hot path; compare artifact line/byte counts; inspect import chain depth.

## Baseline artifact format

`.benchmarks/results.json` — rolling array (max 50 entries), normalized stats only:

```json
[
  {
    "date": "2026-06-08T12:00:00Z",
    "commit": "abc1234",
    "slug": "example_slug",
    "wall_ms": 1234,
    "rss_delta_mb": 156,
    "artifact_lines": 5000,
    "artifact_bytes": 250000,
    "core_files": 42,
    "core_lines": 3500
  }
]
```

Commit policy: **human review required** before first baseline lands in git.

## Anti-patterns

- Do NOT use Unix-only shell `time` / `wc` / process substitution on Windows
- Do NOT commit raw timing logs — only normalized JSON if policy allows
- Do NOT run perf guard on a failing test suite
- Do NOT treat absolute wall times as cross-machine signal — deltas vs baseline only
- Do NOT run with `pytest-xdist -n auto` for timing comparison

## File locations (proposed — not created until approved)

| File | Purpose |
|---|---|
| `.benchmarks/results.json` | Baseline (if policy approves commit) |
| `tests/unit/asteroid_lab/test_perf_regression_guard.py` | Perf guard test module |

## Risks

- Machine variance on Windows — warn on first-run vs committed baseline >10% delta
- `psutil` optional — memory guard inactive without it
- Baseline staleness without periodic runs
