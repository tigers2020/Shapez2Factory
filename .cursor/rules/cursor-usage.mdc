# Cursor Usage

## Plan first

- For complex work, divide scope and owners in a `[Simon]` briefing before implementation.
- When the user asks for "plan only", do not modify code; present the plan only.
- For large changes that need a spec, leave research/plan documents in `documents/` first.
- Minimum order before implementation: research doc → plan MD → human approval → implementation. See the canonical 10-stage pipeline in [protocols/README.md](mdc:protocols/README.md).

## @ References

- Check character roles in `@persona/README.md` and each card.
- For UI work, also read `@persona/gina-gui.md`.
- For architecture decisions, prioritize `@.cursor/rules/architecture.mdc`.

## Memo

- Reflect recurring mistakes, project decisions, and next tasks in `documents/CURSOR_MEMO.md` when the user requests it.
- When updating the memo, leave a date and a short reason.

## Multiple chats

- Maintain layer boundaries even when conversations are split by area.
- When applying conclusions from another chat, re-verify against the files.

## Bugbot

- Follow [bugbot-policy.mdc](mdc:.cursor/rules/bugbot-policy.mdc): not on every PR — only when high-risk, large diff, user asks, or similar; no default checklist item.

## Completion report

- Briefly report changed files, validation commands, and reasons for anything not run.
- If validation fails, clearly note the failing command, reason, and next responsible character.
- If validation could not be run, note commands not executed, reason, and remaining risk.
- If `black .` changes files, note format changes separately from whether validation passed.
