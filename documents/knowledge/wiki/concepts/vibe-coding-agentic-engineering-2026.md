# Vibe Coding & Agentic Engineering (2026)

> **Authority:** working research wiki — not project canon. Promote via `doc-update` if adopted.  
> **Sources:** [[../raw/2026-06-11-vibe-coding-mcp-web-research.md]] · Source ID `src-20260611-vibe-mcp`

## TL;DR

| Mode | When | Core loop |
|------|------|-----------|
| **Vibe coding** | Prototype, throwaway, low blast radius | Prompt → run → next prompt; grade on output |
| **Spec-then-vibe** | Early product, internal tools | Short spec + acceptance → agent executes → accept on output |
| **Agentic / SDD** | Production, team-owned, solver/core | Spec → tests → minimal implement → review every diff → gates |

**Inference:** 2026 professional default is not "never vibe" — it is **match rigor to risk**. This repo's `AGENTS.md` already aligns with agentic/SDD (ICE, contract, validation tiers).

---

## Vibe coding (source)

Karpathy term (~2025): describe what you want; agent implements; you iterate on **results** more than line-by-line code ([SurePrompts 2026 guide](https://sureprompts.com/blog/vibe-coding-the-complete-guide-2026)).

**Works:** scripts, spikes, UI mock, exploration.  
**Fails:** auth, money, shared production, anything needing audit trail.

### Prompt hygiene (source: SurePrompts)

1. Name **success criterion** (how you know done)
2. Set **autonomy ceiling** (read-only vs edit vs commit)
3. **Plan before code** for non-trivial work
4. **Minimum diff** — no drive-by refactors
5. **Rollback path** — branch, revert, feature flag

### Five-phase vibe workflow (source: Zoer)

```text
Requirements (PRD/brief)
→ Architecture (models, APIs — human reviews structure)
→ Incremental codegen (one module at a time)
→ Structured debugging (full context, not "fix this error")
→ Iteration from real usage
```

---

## Agentic engineering (source)

Replacement narrative for production: AI as **component** in SDLC, not autopilot ([Definable](https://definable.ai/blog/is-vibe-coding-dead-what-actually-replaced-it-in-2026/), [Domino playbook](https://domino.ai/blog/agentic-engineering-practitioners-playbook)).

### Non-negotiable habits (synthesis from Definable + Domino + Agent Practice)

| # | Habit | Why |
|---|--------|-----|
| 1 | **Spec before agent task** — even bullets | Scope + review anchor |
| 2 | **Tests before "done"** — agent makes tests pass | Inverts green-by-guessing |
| 3 | **Read full diff** — explain before merge | Agent over-builds |
| 4 | **Tool surface design** — what agent can read/write/approve | Prompts disposable; permissions compound |
| 5 | **Audit trail** on agent runs | Debug without re-run |
| 6 | **Human review on damage line** — deletes, prod writes, customer-visible | Not every keystroke |

### Ralph-style loop (source: Domino)

Code generation is **one** step in a longer cycle:

```text
audit → plan → critique → test design → implement → validate → review
```

**Inference:** maps to this repo: `workflow.mdc` pipeline + `validation-routine.md` tiers.

---

## Four pillars (source: Red Hat Developer, Mar 2026)

| Pillar | Role |
|--------|------|
| **Vibes** | Fast exploration, conversational iteration |
| **Specs** | Authoritative behavior, constraints, acceptance |
| **Skills** | Packaged `SKILL.md` procedures (agentskills.io shape) |
| **Agents** | Cursor, Claude Code, etc. — must be **told** to load specs/skills in chat agents |

**Inference:** matches trimmed skill model — skills on demand, not always-on soup.

---

## Karpathy rules (source: multiple)

Hardcode as `.cursor/rules/*.mdc` or `CLAUDE.md`:

1. **Think before coding** — assumptions explicit; ask if ambiguous  
2. **Simplicity first** — no speculative features  
3. **Surgical changes** — one task, one diff scope  
4. **Goal-driven** — success criteria + verify (tests, exit codes)

Packaged for Cursor: [andrej-karpathy-skills-cursor-vscode](https://github.com/mbeijen/andrej-karpathy-skills-cursor-vscode).

### Cursor rules mechanics (source: DataCamp)

- `.cursor/rules/*.mdc` — `alwaysApply`, `globs`, or intelligent `description`  
- Keep routers **thin** (<500 lines each); detail in `docs/`  
- `@rule-name` for manual attach  

---

## Spectrum: pick your rigor

```text
Pure vibe ──► Spec-then-vibe ──► Full SDD/agentic
     ↑              ↑                    ↑
  spike only    feature slice      production / team
```

| Signal | Lean vibe | Lean agentic |
|--------|-----------|--------------|
| Blast radius | Low | High |
| Maintainer | You, this week | Team, 6+ months |
| Contract exists | No | Yes (spec/ADR) |
| Tests | Optional smoke | Required gates |

---

## Open questions (unverified)

- Optimal spec size before diminishing returns on agent quality  
- How much "plan mode" vs inline spec for Cursor Composer  
- Team policy: max autonomous commits per session  

## Related

- [[mcp-servers-cursor-2026]] — tooling layer  
- Repo canon: `AGENTS.md`, `workflow.mdc`, `validation-routine.md`
