# Asteroid Game-Data Transport & Sprite Projection — Design Spec

**Status:** Phase A implemented (2026-05-25); §1–4 approved; Phase B+ pending  
**Owner:** asteroid-lab + game_data integration  
**Track:** Contract change (D) — single asteroid-facing identity chain backed by imported game_data  
**Decision:** **D** — all RTTP / Lab surfaces consume **game_data-backed projection**, not hardcoded island catalogs or `*InternalVariant*` factory transport.

**Related:**

- [`2026-05-26-rttp-confirmed-placement-footprint-design.md`](2026-05-26-rttp-confirmed-placement-footprint-design.md) — overlay `tile_type` (PR-1); must align with this projection
- [`documents/game_data_analysis/_implementation/02_import_pipeline_report.md`](../../../documents/game_data_analysis/_implementation/02_import_pipeline_report.md)
- [`documents/game_data_analysis/belts_pipes_transport/06_import_pipeline.md`](../../../documents/game_data_analysis/belts_pipes_transport/06_import_pipeline.md)
- `django_apps/web/services/asteroid_game_data_snapshot.py` — snapshot sole construction site

**Out of scope (follow-up tracks):**

- Full nested island blueprint export (PR-2 materializer)
- Dump authoring for missing `SpaceBelt_*` / `SpacePipe_*` building rows (game_data export extension — tracked as projection unblock)
- Solver algorithm changes (field-kind-aware candidate generation)

---

## §1 — Problem & SoT (approved)

### Symptom

Catalog-native RTTP paths emit IDs such as `cat_variant_BeltDefaultForwardInternalVariant_E:shape_belt`. Lab replay/audit show **factory-internal** belt variants while map normalization and overlay projection already use **`SpaceBelt_*` / `SpacePipe_*`** `tile_type` strings.

### Root cause

1. `documents/game_data/belts_pipes_transport.json` maps `ForwardBelt` → `BeltDefaultForwardInternalVariant` (mini_miner internal belt).
2. `canonical_ids_for_transport_kind(SHAPE_BELT)` allowlists every registry row with `transport_category=belt`, so `build_catalog_placement_specs` treats the 1×1 internal belt as the **bundle placement spec**.
3. `SpaceBelt_*` logical names appear in copy strings, Lab classifiers, and overlay code but are **not** present as `building_variants.json` / `sprites.json` rows in the current dump (grep-verified 2026-05-26).

### Global SoT (canonical)

```text
documents/game_data/*.json
  → manage.py import_game_data
  → game_data DB (GameContentAsset, AssetMetaReference, BuildingVariant, TransportBuildingRegistry, …)
  → AsteroidGameDataSnapshot + BuildingCatalogSlice (allowlist extract)
  → Asteroid *projection* modules (runtime view — NOT SoT)
  → RTTP candidates / overlay / replay / Lab UI
```

### Asteroid runtime rule

| Layer | Role |
|-------|------|
| **game_data DB** | Canonical facts: variants, connectors, transport registry, sprites, meta refs |
| **Asteroid projection** | Select/filter/resolve asteroid-facing `layout_t`, `canonical_id`, sprite refs for space transport + miners |
| **Temporary compat adapter** | Fills gaps when dump+DB lack a direct row; **`source_kind ≠ canonical`**; must surface in audit/summary |

### Forbidden

- Using `*InternalVariant*` building variants as **asteroid placement specs** (candidates, validation geometry, commit proxy bundles).
- Treating hardcoded `SpaceBelt_*` / `SpacePipe_*` tables as permanent SoT.
- Hardcoding sprite filesystem paths in JS/HTML templates.
- Using replay/audit `tile_type` as solver algorithm input.

### Allowed

- Documented compatibility fallback when projection cannot resolve from DB (`source_kind = TEMPORARY_COMPAT` or `CANON_MANUAL`).
- Fail-closed when projection is empty and no fallback policy applies.

---

## §2 — Architecture

### Pipeline (target)

```text
documents/game_data/
  sprites.json, prefabs.json, asset_references.json
  building_variants.json, buildings.json
  belts_pipes_transport.json, toolbar_entries.json
        ↓
game_data DB
  GameContentAsset, AssetMetaReference
  BuildingVariant, BuildingGroup, TransportBuildingRegistry, ToolbarElement
        ↓
build_asteroid_game_data_snapshot_with_provenance()
  AsteroidGameDataSnapshot + BuildingCatalogSlice + provenance hash
        ↓
catalog/asteroid_*_projection.py   ← adapter/view only
  asteroid_equipment_projection
  asteroid_transport_projection
  asteroid_sprite_projection
        ↓
Consumers (read projection DTOs only)
  catalog_candidate_placements, catalog_transport_policy
  placement_overlay_projection, catalog_placement_audit
  Lab replay compose + sprite resolver API
```

### Module layout (recommended)

| Module | Responsibility |
|--------|----------------|
| `django_apps/asteroid_lab/catalog/asteroid_transport_projection.py` | Asteroid-facing transport identities: `layout_t`, stub footprint, registry wire keys; excludes factory-internal variants |
| `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py` | Miner/extension placement specs (`Layout_ShapeMiner`, `Layout_FluidMiner`, …) from DB + island copy provenance where needed |
| `django_apps/asteroid_lab/catalog/asteroid_sprite_projection.py` | `layout_t` / `canonical_id` → `sprite_path` via `GameContentAsset` + `AssetMetaReference` |
| `django_apps/asteroid_lab/catalog/projection_source.py` | Shared `ProjectionSourceKind` enum + `ProjectedIdentity` DTO |

Optional thin barrel: `asteroid_runtime_projection.py` re-exports the three modules; **no business logic** in the barrel.

### Projection DTO (contract)

```python
class ProjectionSourceKind(StrEnum):
    GAME_DATA_CANON = "game_data_canon"       # resolved from import batch rows
    TEMPORARY_COMPAT = "temporary_compat"     # documented gap-fill; removal tracked
    CANON_MANUAL = "canon_manual"             # island copy / approved manual table

@dataclass(frozen=True)
class ProjectedTransportTile:
    layout_t: str                             # e.g. SpaceBelt_Forward
    transport_kind: TransportKind               # shape_belt | fluid_pipe
    canonical_id: str | None                  # DB variant when present
    footprint_cells: tuple[BuildingFootprintCell, ...]
    display_rotation_q: int                     # overlay quarter-turns (PR-1b consumer)
    source_kind: ProjectionSourceKind
    source_detail: str                          # stable audit string (batch id, rule id, compat key)

@dataclass(frozen=True)
class ProjectedSpriteRef:
    layout_t: str
    sprite_path: str                          # display path; DB lookup uses logical_path / content_path
    canonical_id: str | None
    source_kind: ProjectionSourceKind
    source_detail: str

@dataclass(frozen=True)
class ProjectedEquipmentSpec:
    layout_t: str
    canonical_id: str
    pattern_id: str
    occupied_offsets: tuple[Coord, ...]
    output_stub_offset: Coord
    output_dir: CardinalDirection
    rotation: CardinalDirection               # placement rotation
    throughput_factor: int  # 4 / 8 / 12 / 16 — matches catalog_candidate contract
    source_kind: ProjectionSourceKind
    source_detail: str
```

### Resolution rules — transport

1. **Query** `TransportBuildingRegistry` + `BuildingVariant` for the pinned import batch (via snapshot/slice inputs — projection receives `BuildingCatalogSlice` + optional `batch_id` for sprite joins).
2. **Exclude** variants whose `internal_name` ends with `InternalVariant` **or** whose registry `transport_kind` is factory-inner-only (`ForwardBelt` → internal belt) from asteroid **placement** allowlist.
3. **Prefer** variants/toolbar/meta refs whose logical id or `layout_t` matches `SpaceBelt` / `SpacePipe` prefixes when present in DB.
4. **Compat fallback** (current dump gap): map route segment role → `SpaceBelt_Forward|LeftTurn|RightTurn` (and pipe equivalents) with `source_kind=TEMPORARY_COMPAT`; record `compat_rule_id` in `source_detail`.
5. **Wire keys** (`transport_kind` registry strings) remain usable for `resolve_cell_transport_kind`; they must not imply internal variant geometry for candidates.

### Resolution rules — equipment

1. **Primary:** `BuildingCatalogSlice` variants filtered by asteroid equipment policy (miners/extensions), not belt registry rows.
2. **Island copy alignment:** `island_extractor_defaults` remains **provenance for Layout_* behavior** until DB rows fully describe nested blueprints; projection may emit `CANON_MANUAL` with link to copy hash — not a second SoT.
3. `build_catalog_placement_specs` **must call** `asteroid_equipment_projection.list_placement_specs(...)`, not `canonical_ids_for_transport_kind`.

### Resolution rules — sprites

```text
layout_t | canonical_id
  → asteroid_sprite_projection.resolve_sprite_ref(...)
  → GameContentAsset.logical_path | content_path (via AssetMetaReference.logical_path first)
  → compat: admin_lab_sprites / lab_sprite_identifier_service when DB row missing
  → Lab / admin API payload
```

No direct `inferTransportSpriteIdentifier` hardcoded path fallbacks except `TEMPORARY_COMPAT` with audit flag.

### Consumer wiring

| Consumer | Change |
|----------|--------|
| `catalog_candidate_placements.build_catalog_placement_specs` | Equipment specs from `asteroid_equipment_projection` only |
| `catalog_transport_policy.canonical_ids_for_transport_kind` | Deprecated for placement; replace with `asteroid_transport_projection.placement_canonical_ids` (may be empty → fail-closed or compat) |
| `placement_overlay_projection` | `tile_type` from `asteroid_transport_projection.resolve_route_tile(...)` |
| `catalog_placement_audit` | Assert `layout_t` not Internal*; emit `projection_source_kind` per row |
| `rttp_solver_summary` | Count `temporary_compat` usages in catalog step metrics |
| Lab JS | Consume backend resolver fields; remove temp static path assumptions |

### Layer boundaries

- **Projection modules:** read-only; no Django ORM in hot path if snapshot already materialized — prefer passing DTOs from `AsteroidGameDataSnapshot` / slice; ORM allowed at snapshot build time in `asteroid_sprite_projection` when batch pinned.
- **domain / optimization:** depend on projection **DTOs**, not `game_data.models` directly (hexagonal: asteroid_lab adapters own projection).
- **game_data importers:** unchanged in Phase A; dump extension is Phase B.

---

## §3 — Data, gaps, fallback removal

### Current dump gaps (2026-05-26)

| Need | Dump/DB today | Phase A behavior |
|------|----------------|------------------|
| `SpaceBelt_*` variant geometry | Not in `building_variants.json` | `TEMPORARY_COMPAT` stub 1×1 + connector policy from overlay table |
| `Layout_ShapeMiner` in slice | May be partial vs copy strings | Equipment projection + `CANON_MANUAL` island defaults |
| Sprite for `SpaceBelt_Forward` | Not in `sprites.json` grep | Compat static via `admin_lab_sprites` until meta ref exists |

### Phase plan

| Phase | Deliverable | Removes |
|-------|-------------|---------|
| **A** | Projection modules + consumer rewiring + tests + audit metrics | Direct InternalVariant candidate IDs |
| **B** | game_data export/import: Space transport variants + toolbar/meta refs | Most `TEMPORARY_COMPAT` transport tiles |
| **C** | Sprite DB resolver-only Lab path | JS hardcoded sprite paths |
| **D** | Delete compat tables; fail-closed if projection incomplete | `TEMPORARY_COMPAT` enum usage |

### Error handling

- `CatalogTransportUnresolvedError` when asteroid run requires DB-backed transport and projection returns empty **and** compat policy disabled.
- Audit step lists every `TEMPORARY_COMPAT` / `CANON_MANUAL` row with `source_detail`.
- Provenance: extend `GameDataSnapshotProvenance` optional field `projection_compat_count` (output-only).

### `island_extractor_defaults.py`

- **Not removed** in Phase A; demoted to **manual provenance input** for equipment projection until DB parity.
- **Must not** grow new hardcoded `SpaceBelt_*` tables — transport compat lives only in `asteroid_transport_projection` with explicit `TEMPORARY_COMPAT`.

---

## §4 — Verification

### Unit tests (pytest)

| Test module | Assert |
|-------------|--------|
| `test_asteroid_transport_projection.py` | `BeltDefaultForwardInternalVariant` ∉ placement allowlist; compat tiles have `source_kind=TEMPORARY_COMPAT` |
| `test_asteroid_equipment_projection.py` | Specs use `Layout_*` / miner `canonical_id`; never Internal belt |
| `test_asteroid_sprite_projection.py` | Resolver returns `sprite_path` from meta ref when seeded; compat flagged |
| `test_catalog_candidate_placements.py` (update) | Generated `pattern_id` has no `InternalVariant` substring |
| `test_placement_overlay_projection.py` (update) | `tile_type` matches projection output |
| `test_catalog_placement_audit.py` (update) | Mismatch reports include `projection_source_kind` |

### Integration

- Pinned import batch fixture: snapshot build → projection → candidate ID sample snapshot.
- Lab smoke (manual): fluid field map → Run Solver → commit frame shows `Layout_FluidMiner` + `SpaceBelt_*` tiles; solver summary shows `temporary_compat_count` if gap-fill used.

### Regression guard

- Import boundary: projection modules must not be imported from `game_data.importers` or solver commit internals.
- Forbidden: weakening tests to accept `InternalVariant` in catalog-native candidate IDs.

---

## Decision record (closed 2026-05-26)

### Q1 — Equipment allowlist source of truth

**Decision:** Phase A uses **explicit projection allowlist config + DB validation**.

| Layer | Rule |
|-------|------|
| Primary filter | `ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST` in projection config (`Layout_ShapeMiner`, `Layout_FluidMiner`, …) |
| Validation | Each entry must resolve to a `BuildingVariant` row in the pinned import batch / `BuildingCatalogSlice` when geometry is required |
| Missing DB parity | Pass only with `ProjectionSourceKind.CANON_MANUAL` + `island_extractor_defaults` provenance |
| **Do not use** | Category-only or toolbar-only filters as sole gate |

### Q2 — Phase B dump work owner

**Decision:** Phase B is owned by the **game_data export/import pipeline**.

| Allowed | Forbidden |
|---------|-----------|
| Export pipeline adds `SpaceBelt_*` / `SpacePipe_*` variants + meta refs | Manual JSON patch as canonical SoT |
| Diagnostic fixtures only when explicitly approved for tests | Ad-hoc `documents/game_data/*.json` edits to “fix prod” |

Phase A unblocks via `TEMPORARY_COMPAT`; Phase B removes compat rows from transport projection.

### Q3 — PR-1b route turn synthesis location

**Decision:** Phase A moves turn/forward tile identity to **`asteroid_transport_projection.resolve_route_tile`**.

```text
placement_overlay_projection._route_rows
  → resolve_route_tile(segment_role, transport_kind, incoming_dir, outgoing_dir)
  → ProjectedTransportTile(layout_t, source_kind=TEMPORARY_COMPAT until Phase B)
```

Overlay remains a **consumer**; it must not own `SpaceBelt_LeftTurn` / `RightTurn` string tables.

### Phase A implementation premises (locked)

1. Equipment: explicit allowlist + DB validation; `CANON_MANUAL` for island copy gaps.
2. Transport: DB-first; `*InternalVariant*` excluded from placement; missing Space* → `TEMPORARY_COMPAT`.
3. Route tiles: `resolve_route_tile` owns PR-1b synthesis.
4. Sprites: `GameContentAsset` / `AssetMetaReference` first; static fallback only with compat audit.
5. Phase B: game_data export/import only (no manual canonical JSON).

**Plan:** [`docs/superpowers/plans/2026-05-26-asteroid-game-data-transport-projection-phase-a.md`](../plans/2026-05-26-asteroid-game-data-transport-projection-phase-a.md)

---

## Approval record

| Section | Status | Date |
|---------|--------|------|
| §1 SoT & problem | **Approved** (architect revision) | 2026-05-26 |
| §2 Architecture | **Approved** | 2026-05-26 |
| §3 Phases & gaps | **Approved** | 2026-05-26 |
| §4 Verification | **Approved** | 2026-05-26 |
| Open Q #1–#3 | **Closed** (decision record above) | 2026-05-26 |
| Phase A plan | **Implemented** (Tasks 0–9) | 2026-05-25 |
