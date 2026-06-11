# Raw: 2026 Vibe Coding + Agentic Engineering + MCP (web research)

Captured: 2026-06-11  
Source type: web synthesis (multiple articles)  
Agent: Cursor ingest for llm-wiki

## Sources consulted

| URL | Topic |
|-----|-------|
| https://sureprompts.com/blog/vibe-coding-the-complete-guide-2026 | Vibe coding definition, prompt patterns, spec-then-vibing |
| https://definable.ai/blog/is-vibe-coding-dead-what-actually-replaced-it-in-2026/ | Agentic engineering habits |
| https://theagentpractice.com/method | Agent tool surface, audit trail, human review gates |
| https://domino.ai/blog/agentic-engineering-practitioners-playbook | Ralph loop, spec-first 8-step workflow |
| https://zoer.ai/posts/zoer/vibe-coding-workflow-step-by-step | 5-phase vibe workflow |
| https://developers.redhat.com/articles/2026/03/30/vibes-specs-skills-agents-ai-coding | Four pillars: vibes, specs, skills, agents |
| https://testcollab.com/blog/from-vibe-coding-to-spec-driven-development | SDD steps, GitHub Spec Kit, CLAUDE.md |
| https://ai.plainenglish.io/stop-just-vibe-coding-the-karpathy-teardown-of-ai-agents-4168577c3570 | Karpathy 4 rules |
| https://github.com/mbeijen/andrej-karpathy-skills-cursor-vscode | Karpathy rules as .cursor/rules |
| https://www.datacamp.com/tutorial/cursor-rules | Cursor .mdc activation modes |
| https://www.nxcode.io/resources/news/cursor-mcp-servers-complete-guide-2026 | MCP overview, top servers, 40-tool limit |
| https://www.agensi.io/learn/best-mcp-servers-2026 | MCP stack recommendations, 5-7 server bloat warning |
| https://toolradar.com/blog/best-mcp-servers-cursor | 12 servers tier list, Context7, Linear, Jan 2026 dynamic context |
| https://www.truefoundry.com/blog/best-mcp-servers-for-cursor-ai | MCP workflow categories |
| https://www.rapidevelopers.com/mcp-tutorial/how-to-configure-mcp-in-cursor-settings | mcp.json setup, global vs project |

## Vibe coding (source claims)

- Term: Andrej Karpathy, early 2025 — describe intent, accept agent output, iterate (SurePrompts, TestCollab).
- Good for: prototypes, throwaway scripts, exploration where wrong answer cost is low (SurePrompts).
- Breaks on: production, auth/money, team-maintained code (SurePrompts).
- Prompt patterns (SurePrompts): name success criterion, autonomy ceiling, plan before code, minimum diff, rollback path.

## Agentic engineering (source + inference)

- 2026 industry shift: vibe → agentic engineering with specs, tests, review, governance (Definable, Domino, Red Hat).
- Habits (Definable): spec before task; read every diff; tests before done.
- Agent Practice: design tool surface (read/write/approval gates) before prompts; audit trail; human review on high-damage actions only.
- Domino Ralph loop phases cited: audit → plan → critique → test → implement → validate → review (8 steps; code gen is one phase).
- Zoer 5-phase vibe workflow: requirements → architecture → incremental codegen → structured debug → iteration.

## Four pillars (Red Hat)

vibes + specs + skills + agents — specs authoritative; skills as SKILL.md directories; agents execute with explicit spec/skill references.

## Karpathy-style rules (multiple sources)

1. Think before coding — state assumptions  
2. Simplicity first — minimum code  
3. Surgical changes — one scope per diff  
4. Goal-driven — success criteria + verification loop  

Implementation: CLAUDE.md, .cursor/rules/*.mdc, agentskills.io SKILL.md format.

## MCP servers 2026 (source claims)

Common recommendations:
- Tier 0 daily: GitHub, Filesystem, DB (PostgreSQL/SQLite), Context7 (docs), Brave Search
- Stack-specific: Playwright (browser), Linear (issues), Docker, Sentry, Figma, Vercel, Slack, Notion, Firecrawl

Cursor config: `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global); Settings → MCP tab; restart after change.

Limits / warnings:
- NxCode: 40 tools max aggregate in Cursor
- Agensi/others: 5-7 servers practical before tool-selection bloat
- Toolradar Jan 2026: dynamic context reduced multi-MCP token overhead ~47%

Open protocol: same MCP servers portable across Cursor, Claude Code, Windsurf (NxCode).

## Uncertainty / stale-risk

- Exact Cursor tool limits may change per version — verify in Settings UI.
- Marketplace one-click install (Toolradar Feb 2026) — verify cursor.com/marketplace.
- "Vibe coding dead" is editorial framing, not consensus — term still used for lightweight mode (SurePrompts).
