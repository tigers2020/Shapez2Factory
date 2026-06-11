# PR-RENDER-0 — Spec + Perf Baseline

**Type:** documentation change · test scaffold
**Depends on:** —
**Enables:** PR-RENDER-1 (and all later PRs)
**Branch (suggested):** `feat/lab-renderer-perf-baseline`

---

## Goal

Lock the renderer perf contract and a reproducible measurement before any production JS changes. Produce
recorded baseline numbers (LOCK-1) so every later PR has a comparison point, and add the static test
skeleton that pins the "rAF stops when paused" invariant (Guard R5).

## Behavior contract

- No production renderer behavior changes in this PR.
- `perf-baseline.md` budgets are the acceptance oracle for RENDER-1..6.
- `baseline-notes.md` holds recorded numbers; RENDER-0 is **not done** while any field is empty (LOCK-1).
- Guard R5 (rAF does not run while paused) is asserted by a static source test.

## Non-goals

- No token-diff, layout split, canvas, or data-shape work (later PRs).
- No renderer rewrite.

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Create | [`perf-baseline.md`](perf-baseline.md) | budgets + DevTools capture procedure + lab_perf fields |
| Create | [`baseline-notes.md`](baseline-notes.md) | LOCK-1 recorded numbers (filled in Step 5) |
| Modify | [`README.md`](README.md) | Guard R1–R6 + LOCK-1..3 (done at folder creation) |
| Create | `tests/unit/asteroid_lab/test_lab_playback_stops_raf_on_pause.py` | Guard R5 static contract |
| Create | `tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py` | reserve `data-lab-perf-debug` hook name |

---

## Tasks

- [ ] **Step 1 — Write `perf-baseline.md`.** Budgets table, reference fixtures, DevTools capture procedure,
  `lab_perf.jsonl` field mapping. (Done at folder creation; confirm budgets match this PR.)

- [ ] **Step 2 — Confirm README guards.** Guard R1–R6 and LOCK-1..3 present in `README.md`. (Done at
  folder creation.)

- [ ] **Step 3 (static contract) — `test_lab_playback_stops_raf_on_pause.py`.**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_set_playing_false_stops_raf_scheduler() -> None:
    src = JS.read_text(encoding="utf-8")
    # setPlaying must cancel the rAF scheduler; rAF must not keep running while paused.
    assert "function stopPlaybackScheduler()" in src
    assert "cancelAnimationFrame" in src
    idx = src.find("function setPlaying(")
    assert idx >= 0
    body = src[idx : idx + 800]
    assert "stopPlaybackScheduler()" in body


def test_tick_playback_returns_when_not_playing() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function tickPlayback(")
    assert idx >= 0
    body = src[idx : idx + 200]
    assert "if (!isPlaying)" in body
```

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_playback_stops_raf_on_pause.py -v`
Expected: PASS against current source (these invariants already hold; this pins them).

- [ ] **Step 4 (skeleton) — `test_lab_renderer_perf_debug_flag.py`.** Reserve the debug-flag hook name so
  RENDER-1/RENDER-3 wire the touched-cell counter consistently. Start as an `xfail`/skeleton that becomes
  green when RENDER-1 lands the flag.

```python
import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


@pytest.mark.xfail(reason="data-lab-perf-debug counter lands in PR-RENDER-1", strict=False)
def test_renderer_perf_debug_flag_reserved() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "data-lab-perf-debug" in src
```

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py -v`
Expected: XFAIL now; flips to XPASS/green when RENDER-1 adds the flag (RENDER-1 removes the xfail).

- [ ] **Step 5 (LOCK-1) — Record baselines.** Run the DevTools procedure for the RTTP 88-frame reference
  and one small `copy-import-*` run. Fill both run blocks in `baseline-notes.md` — no empty fields.

- [ ] **Step 6 — Verify + lint.**

Run:
```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_playback_stops_raf_on_pause.py tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py -v
python -m ruff check tests/unit/asteroid_lab
```

---

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_playback_stops_raf_on_pause.py -v
python -m pytest tests/unit/asteroid_lab/test_lab_renderer_perf_debug_flag.py -v
```

DevTools manual baseline per [`perf-baseline.md`](perf-baseline.md); numbers in `baseline-notes.md`.

## Risks

- `assumption:` reference run id is reproducible; if not, record whatever current heavy run exists and note it.
- `uncertain:` p95 extraction from DevTools is manual; acceptable for baseline, automated in RENDER-3+.

## Done criteria

- `perf-baseline.md` budgets finalized; `baseline-notes.md` has ≥1 fully-filled reference block + 1 small
  run, no empty fields (LOCK-1); Guard R5 static tests green; perf-debug flag skeleton present.
