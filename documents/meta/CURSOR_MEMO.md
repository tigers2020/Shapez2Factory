# CURSOR_MEMO

## 2026-04-17

- Created the `documents/` folder as the live artifact store during video-based multi-stage pipeline documentation alignment.
- Current canonical source is `protocols/README.md`; `AGENTS.md` / `.cursor/rules/*` / `persona/*` summarize and reference it.
- Persona Dialogue 3-stage applies only at pipeline stage 6 (implementation).
- Reviewer (7) / QA (8) / harness (9) must always be handled separately.

## 2026-05-03

- For repeated patterns, separate pattern definitions from template definitions in `prebuilt_pattern_registry`, but extend solver results as nodes inside existing `SolvedRecipe`.

## 2026-05-06

- Added Cursor token/context manual (`documents/ai/manuals/cursor_usage.md`) and linked routing in `AGENTS.md` and `cursor-usage.mdc`.

## 2026-05-18

- Context trim: consolidated alwaysApply into a single [`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc). `AGENTS.md` is routing hub only. Removed `root.mdc`, `cursor-usage.mdc`, `karpathy-guidelines.mdc`. `persona-dialogue`, `mcp`, `caveman-output` are on-demand/stub. Cloud VM: `cursor_usage.md` §Cloud VM.

## 2026-05-19

- Harness slim pass 2: `AGENTS.md` ~246 lines → ~90-line routing hub. Removed stub files `caveman-output.mdc`, `cursor-usage.mdc`, `mcp.mdc`. Skills 16 → 5 active (`bug-fix`, `write-tests`, `doc-update`, `shapez2-workflow`, `git-workflow`) + `_archive/`. `shapez2-workflow` merges `shapez2-harness` + `cursor-shapez2-harness`. Added `cursor_slim_setup.md` + `mcp.json.example`. Added persona stage-5-only policy to `shapez2-core.mdc`.
