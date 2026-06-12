# Knowledge Index

> Map of synthesized knowledge. Raw sources live in `../raw/` (immutable). Maintenance: `docs/agent-workflows/dream-sequence.md`.
> Last updated: 2026-06-12 | Total pages: 17

## Concepts

| Concept | Summary | Wiki page |
|---------|---------|-----------|
| Vibe / Agentic Engineering 2026 | Vibe vs SDD spectrum, Karpathy rules, four pillars, agent habits | [[vibe-coding-agentic-engineering-2026]] |
| MCP Servers (Cursor 2026) | Tiered MCP picks, limits, mcp.json, stack-specific servers | [[mcp-servers-cursor-2026]] |
| Shape Data Model | 1,170 shape recipes, 4-quadrant×4-layer 구조, Hash=Primary key | [[shape-data-model]] |
| Building Definitions | 67 building groups, factory I/O + transport adapters | [[building-definitions]] |
| Building Groups | Group taxonomy from game_data analysis | [[building-groups]] |
| Prefabs Registry | 764 prefab records, Wire* transport visuals | [[prefabs]] |
| Game Data Manifest | Dump metadata, file_hashes integrity | [[game-data-manifest]] |
| Transport System | 54 layout ID (SpaceBelt/SpacePipe), capacity bottleneck | [[transport-system]] |
| Fluid Data Model | 9 fluid 정의, RGB 원색, Mixer 2차색 | [[fluid-data-model]] |
| Materials Data Model | C/R/S/W/c/P/- quadrant codes | [[materials-data-model]] |
| Item Data Model | shapes.json gameplay subset (70 items) | [[item-data-model]] |
| Research Unlocks | Island progression tree, ShapeHash catalog | [[research-unlocks]] |
| Asteroid Lab Layers | L2–L5 solver stack, replay projection boundary | [[asteroid-lab-algorithm]] |
| Wire Typing (Any Boundary) | TypedDict wire contracts; typing-zero complete @597cdaf2 | [[asteroid-lab-wire-typing]] |
| Graphify Map | graph.json scope, stale check, module-level granularity | [[graphify-architecture-map]] |
| Agent Loop Design | Destination + feedback + reroute; verifier split; memory 5-step | [[agent-loop-design]] |
| Software Fundamentals (AI Era) | Pocock six traps; deep modules; grey-box; anti specs-to-code divest | [[software-fundamentals-ai-era-pocock-2026]] |

## Entities

| Entity | Type | Wiki page |
|--------|------|-----------|
| _(none yet)_ | | |

## Comparisons

| Comparison | Summary | Wiki page |
|------------|---------|-----------|
| _(none yet)_ | | |

## Queries

| Query | Summary | Wiki page |
|-------|---------|-----------|
| How to vibe code vs agentic in 2026? | Risk-based rigor; spec + tests + diff review for production | [[vibe-coding-agentic-engineering-2026]] |
| Which MCP servers for Cursor? | GitHub + Context7 + search baseline; 3–5 servers max | [[mcp-servers-cursor-2026]] |
| Where is replay wire typing authority? | frozen dataclass + named TypedDict + converters | [[asteroid-lab-wire-typing]] |
| When to run graphify vs grep? | graphify first when graph fresh; scoped replay updates | [[graphify-architecture-map]] |
| Prompt vs loop for agents? | Set done criteria + feedback loop; separate verifier | [[agent-loop-design]] |
| Why fundamentals still matter with AI? | Shallow-module mazes; design interfaces; TDD headlight limit | [[software-fundamentals-ai-era-pocock-2026]] |

## Sources (external research)

| Source ID | Topic | Raw |
|-----------|-------|-----|
| src-20260611-vibe-mcp | 2026 vibe coding, agentic workflow, MCP | `raw/2026-06-11-vibe-coding-mcp-web-research.md` |

## Sources (project canon — wiki synthesis only)

| Source ID | Topic | Canon path |
|-----------|-------|------------|
| src-20260611-typing-stack | Any boundary typing phases 0/1/4 | `documents/ai/manuals/typing_contracts.md`, `docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md` |
| src-20260611-graphify-ops | Graphify operating scope | `.cursor/rules/graphify.mdc`, `graphify-out/graph.json` |

## Open questions

| Topic | Notes |
|-------|-------|
| `building-variants` | Referenced in raw analysis; no wiki page yet |
| `island-mechanics` | Referenced in raw analysis; no wiki page yet |
| `transport-capacity` | Could merge into [[transport-system]] or standalone later |
