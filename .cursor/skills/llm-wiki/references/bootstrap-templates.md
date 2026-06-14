# Bootstrap templates

Copy these verbatim when creating `documents/knowledge/` for the first time.

## documents/knowledge/raw/.gitkeep

(empty file — keeps directory in git)

## documents/knowledge/outputs/.gitkeep

(empty file)

## documents/knowledge/wiki/Index.md

```markdown
# Knowledge Index

> Map of synthesized knowledge. Raw sources live in `../raw/` (immutable). Maintenance: `documents/agent-workflows/dream-sequence.md`.

## Concepts

| Concept | Summary | Wiki page |
|---------|---------|-----------|
| _(none yet)_ | | |

## Entities

| Entity | Type | Wiki page |
|--------|------|-----------|
| _(none yet)_ | | |

## Sources

| Source ID | Raw path | SHA256 / URL | Wiki page(s) |
|-----------|----------|--------------|--------------|
| _(none yet)_ | | | |
```

## documents/knowledge/wiki/Log.md

```markdown
# Knowledge Log

Append-only chronological record. Newest entries at the bottom.

## [YYYY-MM-DD] bootstrap | Initial knowledge layer

- Created `documents/knowledge/` (raw / wiki / outputs)
- Added `Index.md`, `Processed.md`, append-only `Log.md`
- Added `documents/agent-workflows/dream-sequence.md`
- Linked from `AGENTS.md`; workflow in `.cursor/skills/llm-wiki/`
```

## documents/knowledge/wiki/Processed.md

```markdown
# Processed Raw Index

Prevents duplicate ingestion. One row per raw artifact. Match on Source ID or SHA256/URL before re-ingesting.

| Source ID | Raw path | SHA256 / URL | Wiki page(s) | Processed date | Notes |
|-----------|----------|--------------|--------------|----------------|-------|
| _(none yet)_ | | | | | |
```

## documents/knowledge/README.md

```markdown
# Knowledge layer (LLM Wiki)

Persistent research and conversation insights — **not** solver canon.

| Path | Role |
|------|------|
| `raw/` | Immutable, append-only raw inputs (links, dumps, files). Do not rewrite after capture |
| `wiki/` | Summarized, linked knowledge (`Index.md`, `Log.md`, `Processed.md`) |
| `outputs/` | Deliverables produced from wiki context |

**Hard rules**

- Raw artifacts are append-only / immutable after capture. Content changed → new dated raw file.
- Wiki is working memory; spec/ADR/canon docs beat wiki pages.
- Promote to canon via `/doc-update`, not by editing wiki alone.

Maintenance: `documents/agent-workflows/dream-sequence.md` · Skill: `.cursor/skills/llm-wiki/`
```

## Log entry template (ingest / dream-sequence)

Append to bottom of `Log.md`:

```markdown
## [YYYY-MM-DD] ingest | topic-slug

- Source ID: src-YYYYMMDD-slug
- Raw: documents/knowledge/raw/YYYY-MM-DD-slug.md
- Wiki: documents/knowledge/wiki/topic-slug.md
```

```markdown
## [YYYY-MM-DD] dream-sequence | raw:N ingested, pages merged:M, contradictions:K

- (bullet details)
```
