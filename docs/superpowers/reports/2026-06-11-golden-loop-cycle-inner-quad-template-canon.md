# Golden Loop Cycle — inner quad template canon

## Baseline

- branch: `feat/inner-quad-template-canon` (from `origin/master`)
- commit: (see PR)
- command: N/A — docs + fixture cycle only
- hypothesis: freeze T1–T4 / Q1–Q4 as canon + decode regression before any L5 solver work

## Diagnosis

- dominant bucket: **artifact / contract** — placement templates existed only as chat paste, not repo canon
- prior solver risk: quad + reroute mixed with golden eval would break one-hypothesis cycles

## Change

- `documents/game_rules/shapez2_asteroid_inner_quad_templates.md`
- `tests/fixtures/asteroid_lab/inner_quad_templates/` (8 copies + manifest)
- `tests/unit/asteroid_lab/test_inner_quad_template_decode.py`

## Verification

- `pytest tests/unit/asteroid_lab/test_inner_quad_template_decode.py -q`

## Decision

- **SUCCESS** (closure for doc+fixture scope; no golden loop metric change expected)
- PR: (see GitHub)
- next hypothesis: L5 quad tile catalog + extension reroute (separate cycle)
