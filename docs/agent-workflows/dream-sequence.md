# Dream Sequence

Manual knowledge-base maintenance for `documents/knowledge/`. Run on user request (`드림 시퀀스 실행해줘`) — not scheduled until explicitly configured.

## Purpose

Health check for the wiki layer:

- Integrate new raw inputs
- Remove or merge duplicates
- Surface contradictions and stale claims
- Strengthen cross-links in `Index.md`

## When to run

- After several ingests without index refresh
- Before starting a large research or planning task
- When wiki pages feel inconsistent or outdated
- Weekly (manual) if actively accumulating knowledge

## Procedure

### 1. Inventory raw

List `documents/knowledge/raw/`. Compare against `wiki/Processed.md` (Source ID and SHA256/URL). Queue unprocessed files.

### 2. Ingest pending

For each unprocessed raw item, follow ingest rules in `.cursor/skills/llm-wiki/SKILL.md` § Ingest. Never modify existing raw files.

### 3. Contradiction scan

Read wiki pages linked from `Index.md`. Flag pairs where:

- Same entity has conflicting facts
- A claim is older than a newer raw source on the same topic
- Two pages cover the same concept under different names

Resolution: merge pages, add "superseded" note, or log open question in `Log.md`.

### 4. Dedup

Find wiki pages with overlapping scope. Merge into one canonical page; update links and `Processed.md` if raw mapping changes.

### 5. Refresh Index

Rebuild concept/entity/source tables in `Index.md`. Drop dead links. Add new connections discovered during scan.

### 6. Log

Append to `wiki/Log.md` (append-only heading):

```markdown
## [YYYY-MM-DD] dream-sequence | raw:N ingested, pages merged:M, contradictions:K

- (bullet details)
```

## Output

Agent reports:

```text
Summary:
Raw ingested: (count + paths)
Wiki updated: (pages)
Contradictions resolved: (list or "none")
Index changes: (brief)
Log entry: (heading added)
```

## Customization

User may change operating mode by instruction (no file edit required unless persisting):

- **Batch mode:** do not ingest on every save; only process raw during dream sequence
- **Eager mode:** ingest immediately on each "저장해줘" (default in skill)

To persist a mode change, add a `## Operating mode` section to this file.

## Boundaries

- Does not modify solver code, tests, or canon specs
- Does not run validation gates (doc-only)
- Promoting wiki insight to canon → use `/doc-update` and normal spec/ADR path
