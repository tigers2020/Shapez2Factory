# Research: video-based multi-stage development structure documentation

- Date: 2026-04-17
- Purpose: map video flow `Director → planning duo → development → review → QA → harness → wiki` onto current documentation system

## Current documents reviewed

- `AGENTS.md`
- `protocols/README.md`
- `.cursor/rules/root.mdc`
- `.cursor/rules/cursor-usage.mdc`
- `.cursor/rules/persona-dialogue.mdc`
- `persona/README.md`
- `persona/simon.md`
- `persona/dominic.md`
- `persona/yuri.md`
- `persona/tess.md`
- `persona/rex.md`
- `persona/ada.md`
- `persona/gina-gui.md`

## Findings

Current repo core docs already reflect:

1. `protocols/README.md` serves as 10-stage canonical role.
2. `AGENTS.md` summarizes same flow briefly.
3. `persona-dialogue.mdc` limits Persona Dialogue 3-stage to pipeline step 6 (implementation) only.
4. `persona/*` maps existing characters to video role groups.
5. Reviewer (7), QA (8), harness (9) axes are already separated.

## Remaining gap

Documentation rules require research/plan/CURSOR_MEMO under `documents/` but folders/files did not exist.

Operating rules were declared but gate artifacts were not persisted.

## Reflection policy

1. Preserve existing body structure.
2. Create research and plan documents for this change under `documents/`.
3. Create `documents/CURSOR_MEMO.md` referenced by rule files.
4. Do not add new personas.

## Mapping memo

| Video role | Repo mapping |
|---|---|
| Director | Simon |
| Planning duo | Dominic + Yuri |
| Development team | Dominic + Yuri + Ada + Gina |
| Reviewer | Yuri lead, Simon assist |
| QA | Tess |
| Harness | Rex |
| Wiki/doc sync | Simon closing + `documents/` |
