# Knowledge layer (LLM Wiki)

Persistent research and conversation insights — **not** solver canon.

| Path | Role |
|------|------|
| `raw/` | Immutable, append-only raw inputs (links, dumps, files). Do not rewrite after capture |
| `wiki/` | Synthesized, linked knowledge (`Index.md`, `Log.md`, `Processed.md`) |
| `outputs/` | Deliverables produced from wiki context |

**Hard rules**

- Raw artifacts are append-only / immutable after capture. Content changed → new dated raw file.
- Wiki is working memory; spec/ADR/canon docs beat wiki pages.
- Promote to canon via `/doc-update`, not by editing wiki alone.

Maintenance: `docs/agent-workflows/dream-sequence.md` · Skill: `.cursor/skills/llm-wiki/`
