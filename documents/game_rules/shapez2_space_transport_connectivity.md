---
status: CANON
owner: asteroid-lab
last_reviewed: 2026-06-11
authority: user-confirmed + aligned with in-repo Space Lift / transport tile inventory
related_docs:
  - documents/game_data/space_transport_identifiers.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - documents/ai/manuals/game_logic.md
---

# Shapez 2 Island Space Belt / Pipe Connectivity (Basic Rules)

Normative **topology** rules for island `SpaceBelt_*` / `SpacePipe_*` and miner attachment.
Throughput values live in [`shapez2_asteroid_space_transport_throughput.md`](shapez2_asteroid_space_transport_throughput.md).
Tile id inventory: [`space_transport_identifiers.md`](../game_data/space_transport_identifiers.md).

**Terminology:** In-game UI/wiki often calls vertical connectors **Rift**; this repo uses **Space Lift** (`SpaceBelt_Lift*`, `SpacePipe_Lift*`). Same contract unless a future dump proves otherwise.

**Rotation:** Copy-string field `R` is quarter-turns clockwise (`R0`…`R3`). Examples below use `Miner(R0)` = miner placed at rotation 0.

---

## 1. Miners may share one belt segment (serial chain)

Multiple extractors/pumps may attach to the **same belt line** in series. Each miner output stub feeds the belt; the belt carries flow to the next miner or toward the exterior connector.

```text
Miner(R0) — Belt(R1) — Miner(R3) — … — connector
```

| Rule | Detail |
| ---- | ------ |
| Sharing allowed | One belt cell/graph edge may sit **between** two miners (or between miner and merger/splitter) |
| Not required | Every miner does **not** need a dedicated belt-only path to the connector |
| Solver implication | Route planning may **reuse trunk segments**; saturation is shared-lane pressure, not per-miner belt count |

This is distinct from **parallel merge**: two miners feeding one merger onto one trunk is also valid, but §1 covers **serial** reuse of one belt run.

---

## 2. Field / void horizontal transport (non-Rift tiles)

On a single horizontal layer (`z=0` field plane or `z=1` void shell), forward/turn/merge/split tiles obey cardinal **in/out** ports per rotation.

### 2.1 Straight and turn

| Tile family | Typical IO |
| ----------- | ---------- |
| `SpaceBelt_Forward`, `SpacePipe_Forward` | 1 in, 1 out (opposite ends) |
| `SpaceBelt_LeftTurn`, `SpaceBelt_RightTurn`, pipe analogs | 1 in, 1 out (90° bend) |

### 2.2 Merger and splitter (1:1 … 3:1)

Belts and pipes support **multi-port** hubs on the **same z layer**:

| Pattern | Example tile ids | Port ratio (informal) |
| ------- | ---------------- | --------------------- |
| Forward merge/split | `*LeftFwdMerger`, `*RightFwdMerger`, `*LeftFwdSplitter`, `*RightFwdSplitter` | 2:1 or 1:2 along forward axis |
| Y merge/split | `*YMerger`, `*YSplitter` | 2:1 or 1:2 (Y junction) |
| Triple merge/split | `*TripleMerger`, `*TripleSplitter` | up to **3:1** merge or **1:3** split |

| Rule | Detail |
| ---- | ------ |
| Directions | All four cardinals may participate **according to tile type and `R`** |
| Hub allowed | Merger/splitter/Y/triple tiles are valid attachment points |
| Catalog | Exact ESWN masks per tile are imported in `space_transport_catalog` (see SHA-61 for merger/splitter IO signatures) |

**Forbidden on Rift/Lift tiles:** merger, splitter, Y, and triple variants (§3).

---

## 3. Rift / Space Lift (vertical `z` connector)

`SpaceBelt_Lift1*`, `SpaceBelt_Lift2*`, `SpacePipe_Lift1*`, `SpacePipe_Lift2*` connect **field (`z=0`) ↔ void (`z=1`)** (and lift2 where applicable). These are **Rift** connectors in player terms.

| Rule | Rift / Space Lift | Horizontal belt/pipe |
| ---- | ----------------- | -------------------- |
| Input ports | **Exactly 1** | Per-tile (1 on straight; >1 on merge/split hubs) |
| Output ports | **Exactly 1** | Per-tile |
| Cross-layer | **1:1** only (one stream up or down) | N/A |
| Merger / splitter / Y / triple | **Forbidden** | Allowed (§2.2) |
| Multi-input attachment | **Forbidden** — do not treat lift cell as merge node | Allowed at hubs |

### 3.1 Rifted `z = n` layer — single flow along `R`

On the **rifted** horizontal slice at height `z = n` (void shell after lift), a Rift tile admits **only one** input and emits **only one** output. That crossing is aligned with the tile's **placement rotation `R`** (one cardinal direction for the vertical link, not a multi-way hub).

```text
z=0 field  ──(1 input)──▶  Lift(R=k)  ──(1 output along R)──▶  z=1 void belt network
```

| Rule | Detail |
| ---- | ------ |
| Single input | At most **one** incoming edge into the lift input port |
| Single output on void side | At most **one** outgoing edge from the lift output port on `z=1` |
| Direction | Output egress on the void layer follows the lift tile's **`R`** facing (solver: pick one void cell per stub — see `space_lift_routing.py`) |
| No merge at lift | Do not attach merger/splitter logic to lift cells |

**Asteroid Lab solver (PR-16+):** Inner field miners blocked by the rim ring must use **one** lift egress per inner group stub into the `z=1` void network, then route void-only to L2 connectors.

---

## 4. Layer summary

| Layer | `z` | Transport role |
| ----- | --- | -------------- |
| Asteroid field | `0` | Miners, extensions, interior fill; optional field-plane belts where walkable |
| Exterior void | `1` | Primary `SpaceBelt_*` / `SpacePipe_*` graph to connectors |
| Rift / Lift | `0 ↔ 1` | **1:1** vertical link only |

---

## 5. Implementation pointers (non-normative)

| Concern | Location |
| ------- | -------- |
| Lift egress stub → void cell | `layer_04_transport_routing/space_lift_routing.py` |
| Void vs field walkable domain | `layer_04_transport_routing/route_domain.py` |
| Transport tile ids | `documents/game_data/space_transport_identifiers.md` |
| IO signatures (merge/split projection) | `space_transport_catalog_import.py`, SHA-61 plans |
| Throughput / saturation | `shapez2_asteroid_space_transport_throughput.md` |

---

## Change history

| Date | Change |
| ---- | ------ |
| 2026-06-11 | Initial CANON: miner belt sharing, horizontal merge/split, Rift 1:1 and z-layer `R` egress |
