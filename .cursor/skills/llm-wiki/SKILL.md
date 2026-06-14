---
name: llm-wiki
description: Persists AI conversation insights into repo Markdown knowledge layers (raw ingest, wiki synthesis, dream-sequence maintenance). Use when the user says "위키 구조 만들어", "저장해줘", "ingest", "dream sequence", "드림 시퀀스", or wants to capture links/files into documents/knowledge/.
disable-model-invocation: true
metadata:
  owner: project
  risk: low
  requires_validation: false
---

# LLM Wiki

## Position · Authority · Acceptance

| | |
|---|---|
| **Position** | Knowledge persistence layer — not solver canon, not contract spec |
| **Authority** | `AGENTS.md` stays canon. Spec/ADR/canon docs beat wiki pages. Wiki is working memory + research, not runtime input |
| **Acceptance** | Bootstrap creates folder tree + templates; ingest updates wiki without duplicating processed raw; dream sequence produces Log entry + Index delta |

## Repo mapping (no claw.md)

Karpathy-style LLM Wiki mapped to existing governance — **do not** add `claw.md` or a second command OS.

```text
documents/knowledge/raw/              # immutable raw inputs (append-only)
documents/knowledge/wiki/             # synthesized, linked knowledge
documents/knowledge/wiki/Index.md     # content map
documents/knowledge/wiki/Log.md       # append-only chronological log
documents/knowledge/wiki/Processed.md # source id/hash/path → wiki trace
documents/knowledge/outputs/          # deliverables
documents/agent-workflows/dream-sequence.md  # maintenance routine (detail lives here)
.cursor/skills/llm-wiki/SKILL.md      # workflow logic
AGENTS.md                             # 1–2 line link only
```

Hard rules:

- `.cursor/rules/*.mdc` stay thin routers — no LLM Wiki detail in rules.
- **Raw immutable:** append-only after capture. Do not rewrite raw files; create a new dated raw file when source content changes.
- Dream Sequence: **manual command first**; no cron/automation until user asks.
- Ingestion must check `Processed.md` (Source ID + SHA256/URL) before re-processing.
- Wiki content must not become solver/replay/metrics input unless promoted to canon via normal doc workflow (`doc-update` skill).

## Trigger routing

| User says | Action |
|---|---|
| `위키 구조 만들어` | Bootstrap (§ Bootstrap) |
| `저장해줘`, link/file + save intent | Ingest (§ Ingest) |
| `드림 시퀀스`, `dream sequence` | Maintenance (§ Dream Sequence) |
| wiki search / "what do we know about X" | Read `Index.md` → linked wiki pages; cite paths |

## Bootstrap

When `documents/knowledge/` is missing or user requests setup:

1. Create directory tree (see mapping above).
2. Write wiki templates from [references/bootstrap-templates.md](references/bootstrap-templates.md).
3. Write `documents/agent-workflows/dream-sequence.md` from [references/dream-sequence-routine.md](references/dream-sequence-routine.md).
4. Add to `AGENTS.md` (Tool Routing section):

   ```markdown
   - **LLM Wiki (persistent knowledge):** raw → `documents/knowledge/`; maintenance via `documents/agent-workflows/dream-sequence.md`. Skill: `/llm-wiki`.
   ```

5. Register skill in `.cursor/skills/README.md` if not already listed.
6. Run `powershell -File scripts/check_governance.ps1` — fix hard failures only.

Do not expand `AGENTS.md` beyond the link line.

## Ingest

Given a URL, pasted text, or file path:

1. Read `documents/knowledge/wiki/Processed.md` — skip if Source ID or SHA256/URL already processed (re-ingest only on explicit request → new Source ID + new raw file).
2. Save raw artifact under `documents/knowledge/raw/` with stable name: `YYYY-MM-DD-slug.md` or original filename. **Never edit an existing raw file.**
3. Compute SHA256 for file content; record URL if web source.
4. Assign Source ID: `src-YYYYMMDD-slug` (unique in `Processed.md`).
5. Synthesize one wiki page under `documents/knowledge/wiki/` (topic slug, not raw filename).
6. Update `Index.md`: concept, entities, source row with Source ID + SHA256/URL.
7. Append `Processed.md` row: Source ID | Raw path | SHA256/URL | Wiki page(s) | Processed date | Notes.
8. Append `Log.md` heading block (see template in references).

Prefer updating an existing wiki page over creating duplicates. Merge related topics; link bidirectionally in markdown.

## Dream Sequence

Manual maintenance pass — full routine in `documents/agent-workflows/dream-sequence.md`.

Quick checklist:

1. Scan `raw/` for unprocessed files (cross-check `Processed.md` by Source ID and SHA256/URL).
2. Ingest pending raw items.
3. Scan wiki for contradictions, stale claims, duplicate pages — merge or flag in `Log.md`.
4. Refresh `Index.md` structure (concepts, entities, sources).
5. Append `Log.md` dream-sequence heading block.

Output block:

```text
Summary:
Raw ingested:
Wiki updated:
Contradictions resolved:
Index changes:
Log entry:
```

## Output format

All wiki operations end with:

```text
Summary:
Files changed:
Wiki pages touched:
Processed entries:
Next: (ingest more | dream sequence | promote to canon via doc-update)
```

## Failure handling

- `documents/knowledge/` missing → run Bootstrap first.
- Raw source ambiguous → ask one clarifying question (topic slug).
- Conflict with canon spec/ADR → wiki page notes "superseded by \<path\>"; do not overwrite canon.
- `BLOCKED:` when user wants wiki content as solver contract without spec/acceptance path.

## References

- Bootstrap file templates: [references/bootstrap-templates.md](references/bootstrap-templates.md)
- Dream sequence routine (copied to docs on bootstrap): [references/dream-sequence-routine.md](references/dream-sequence-routine.md)
- Canon doc sync after promotion: `/doc-update`
