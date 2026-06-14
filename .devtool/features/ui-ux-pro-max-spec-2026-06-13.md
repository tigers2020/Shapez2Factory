---
status: verify
modified: 2026-06-13
---

# UI UX Pro Max — integration (S1 agent overlay)

## Scope

Slice S1 only: Cursor agent overlay — rule, prompt, skill index, root router. No CSS/themes (S2–S3 deferred).

## Acceptance (S1)

- [x] `.cursor/rules/ui-ux-pro-max-skill.mdc` exists (≤75 lines, glob-matched)
- [x] `.cursor/prompts/ui-design.md` exists with DESIGN.md tokens + workflow
- [x] `root.mdc` routes to ui-ux-pro-max-skill
- [x] `.cursor/skills/README.md` registers `ui-ux-pro-max`
- [x] Spec approved (`documents/superpowers/specs/2026-06-13-ui-ux-pro-max-integration.md`)
- [x] `search.py --design-system` local run succeeds

## Artifacts

- Spec: `documents/superpowers/specs/2026-06-13-ui-ux-pro-max-integration.md`
- Plan: `documents/superpowers/plans/2026-06-13-ui-ux-pro-max-integration.md`

## Progress

- 2026-06-13 — Spec light improve + user approval.
- 2026-06-13 — S1: created `ui-ux-pro-max-skill.mdc`, `ui-design.md`; updated root router + skills README; spec §8 APPROVED.

## Deferred (not S1)

- S2 theme mapping doc
- S3 `ui-ux-pro-max-themes.css` + `input.css` import
- S4 build/check + manual asteroid lab spot-check
