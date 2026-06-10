---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional pytest contract for app.css rebuild drift

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

CI will gate `app.css` drift (mid plan), but developers may want fast local feedback via pytest without pushing. Existing `test_asteroid_lab_ui_strings.py` only checks substring presence for a few lab classes — not a full rebuild gate.

## Scope

Add an optional pytest (or extend existing UI string test module) that runs `npm run build:css` and asserts no diff on `django_apps/web/static/web/css/app.css`, skipped when Node is unavailable.

## Non-goals

- Replacing the CI job (mid plan is authoritative).
- Testing every CSS class in templates.

## Implementation Plan

1. Review mid plan CI gate is merged or in progress.
2. Add `tests/unit/web/test_app_css_drift.py` (or extend asteroid lab UI tests):

```python
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
APP_CSS = ROOT / "django_apps/web/static/web/css/app.css"

@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_committed_app_css_matches_tailwind_build() -> None:
    before = APP_CSS.read_bytes()
    subprocess.run(["npm", "run", "build:css"], cwd=ROOT, check=True)
    after = APP_CSS.read_bytes()
    assert before == after, "app.css drift: run npm run build:css and commit"
```

3. Mark test as slow/integration if test-fast should skip it — check `scripts/test_fast.ps1` filters.
4. Document in `DESIGN.md` that both CI and optional pytest enforce drift.
5. Run targeted pytest locally with Node present.

## Files / Areas Likely Affected

- `tests/unit/web/test_app_css_drift.py` (new)
- `DESIGN.md` (optional note)
- `scripts/test_fast.ps1` (only if skip marker needed)

## Validation Plan

- tests: `pytest tests/unit/web/test_app_css_drift.py -v` (with Node)
- manual verification: test fails after editing `input.css` without rebuild

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional; CI gate alone may suffice.
- CI runners always have Node; local pytest skip is acceptable.
