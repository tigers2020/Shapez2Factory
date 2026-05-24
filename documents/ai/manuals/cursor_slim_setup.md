# Cursor Slim Setup Guide

Checklist for minimizing Cursor global settings when working on shapez2 Factory Planner to reduce context load.  
Repo rules (`shapez2-core.mdc` · `AGENTS.md`) apply automatically, so **focus global settings on removing duplication**.

## MCP servers — recommended setup

### Default ON (shapez2 daily development)

| MCP server | Purpose | Notes |
|----------|------|------|
| **context7** (one only) | Latest library · framework docs | If plugin · user versions duplicate, **disable one** |
| **github** | PR · issue lookup | OK to enable only when needed |
| **playwright** | UI · graph visual verification | For solver UI or frontend work |

### Default OFF recommended (enable only when needed)

| MCP server | Reason |
|----------|------|
| Linear | Burden only if issue tracking unused |
| Figma | Unnecessary without design work |
| Vercel | Unnecessary without deploy work |
| Google Developer Knowledge | Replaceable with local grep · context7 |
| sequential-thinking | Step reasoning sufficient from the model itself |
| GitLens MCP | Local `git` commands often enough |
| Serena | OFF if symbol search unused; if used, run `initial_instructions` first |
| duplicate context7 | Keep only one of plugin · user |

Settings location: **Cursor → Settings → MCP** or project `.cursor/mcp.json`.  
Minimal template: [`.cursor/mcp.json.example`](../../../.cursor/mcp.json.example)

## Plugins — Redis Development

This repo does not use Redis.  
→ **Disable or turn OFF** the `redis-development` plugin for **this workspace** in Cursor Settings → Extensions/Plugins.  
Reason: many Redis rules injected by the plugin load into context every turn.

## User Rules (global)

**Remove long rules that duplicate** `AGENTS.md` · `shapez2-core.mdc`.  
One line in global User Rules is enough for this repo:

```
shapez2Factory: Follow AGENTS.md + .cursor/rules/shapez2-core.mdc.
```

Putting long workflow · test · layer rules in User Rules double-loads them every conversation.

## Global Caveman skills

Global caveman skills such as `C:\Users\<user>\.agents\skills\caveman\` should  
not auto-trigger in this repo.  
Reason: project canonical source is `shapez2-core.mdc` Caveman 6 sections.  
Method: set `disable-model-invocation: true` on those skills or limit trigger keywords to project-specific ones.

## Context-saving habits

| Habit | Description |
|------|------|
| Separate threads per task unit | Start a new chat when the topic changes |
| Minimize `@` scope | Only needed files · folders; never whole codebase |
| Subagent separation | Run broad exploration in separate context; bring back results only |
| Restart long conversations | Reset session when behavior is off |

Details: [`cursor_usage.md`](cursor_usage.md) §4 · §6 · §14

## Related docs

- Standing rules: [shapez2-core.mdc](../../../.cursor/rules/shapez2-core.mdc)
- Operating contract: [AGENTS.md](../../../AGENTS.md)
- MCP schema check: `mcps/<server>/tools/` folder
- Dev commands: [dev_commands.md](../runbooks/dev_commands.md)
