# MCP Servers for Cursor (2026)

> **Authority:** working research wiki — not project canon.  
> **Sources:** [[../raw/2026-06-11-vibe-coding-mcp-web-research.md]] · Source ID `src-20260611-vibe-mcp`

## What MCP does

[Model Context Protocol](https://modelcontextprotocol.io/) lets the IDE agent call **tools** on external systems (GitHub, DB, browser, search) with structured schemas instead of copy-paste.

Cursor: `.cursor/mcp.json` (project) merges with `~/.cursor/mcp.json` (global). Monitor: **Settings → MCP**. Restart IDE after config change ([RapidDev tutorial](https://www.rapidevelopers.com/mcp-tutorial/how-to-configure-mcp-in-cursor-settings)).

**Inference:** MCP is portable — same server config often works in Claude Code / Windsurf with path tweaks ([NxCode guide](https://www.nxcode.io/resources/news/cursor-mcp-servers-complete-guide-2026)).

---

## How many servers?

| Source | Guidance |
|--------|----------|
| NxCode | Start 2–3; Cursor **~40 tools aggregate** cap cited |
| Agensi | **5–7 servers** max before tool-selection bloat |
| Toolradar (Jan 2026) | Dynamic context ↓ multi-MCP token cost ~47% — 5–6 servers more practical than before |

**Recommendation (inference):** enable **3–5** that match daily workflow; disable unused tools per server in Settings.

---

## Tier 1 — almost every dev team

| Server | Use | Notes |
|--------|-----|-------|
| **GitHub** | PR, issues, diff, review comments | Kills copy-paste loop |
| **Filesystem** | Scoped read/write beyond default | Often built-in; explicit server for sandboxes |
| **Context7** | Up-to-date library/framework docs | Reduces hallucinated APIs ([Toolradar](https://toolradar.com/blog/best-mcp-servers-cursor)) |
| **Brave Search** (or similar) | Live web facts | Research, version checks |

---

## Tier 2 — stack-dependent

| Server | When |
|--------|------|
| **PostgreSQL / SQLite** | App has DB; prefer **read-only** on prod |
| **Playwright** | UI E2E, rendered verification | This repo: `playwright.mdc`, `output/playwright/` |
| **Linear** | Issue tracker driving plan queue | This repo already uses Linear MCP |
| **Docker** | Container lifecycle, logs |
| **Sentry** | Error triage from prod/staging |
| **Slack / Discord** | Team context, alerts |

---

## Tier 3 — specialized

| Server | When |
|--------|------|
| **Figma** | Design → code handoff |
| **Vercel** | Deploy previews |
| **Firecrawl** | Structured site scrape |
| **Notion** | Docs hub outside repo |
| **Memory** | Cross-session agent memory (evaluate privacy) |

---

## Example project `mcp.json` (inference template)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>" }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

Use env vars / secrets manager — never commit tokens. Project-level config can be committed without secrets (env referenced only).

---

## Selection checklist

1. **Workflow first** — what do you paste into chat today? (SQL, PR links, docs URLs)  
2. **Read-only default** for prod DB and destructive ops  
3. **One server per concern** — don't duplicate GitHub + gh CLI + custom git MCP  
4. **Toggle tools** — disable noisy tools in MCP settings  
5. **Verify connection** — green in MCP tab before relying on agent  

---

## This repo (inference)

Already connected (workspace): GitHub, Linear, Playwright, Supabase, browser, agentmemory, Hermes, etc.

**Practical trim (inference):** disable servers not used in current task; align with AGENTS.md — no invented MCP behavior; graphify/playwright only when task needs them.

---

## Risks (source + inference)

| Risk | Mitigation |
|------|------------|
| Tool overload / wrong tool picked | Fewer servers; explicit user instruction |
| Secret leak in mcp.json | env only; gitignore tokens |
| Stale docs MCP | Cross-check Context7 with official docs for breaking changes |
| Autonomous destructive ops | human approval gates; read-only DB |

## Related

- [[vibe-coding-agentic-engineering-2026]] — workflow rigor  
- Cursor marketplace (Feb 2026 cited): cursor.com/marketplace — **unverified** install path
