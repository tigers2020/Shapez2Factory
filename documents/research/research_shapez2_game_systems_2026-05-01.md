# shapez 2 — Game Systems Analysis (Reference Document)

> Role: Game systems analyst  
> Date: 2026-05-01  
> Purpose: Domain and planning reference summary for the shapez2Solver project

[![shapez 2 | Factory & Strategy game | Available now on Steam](https://images.openai.com/static-rsc-4/njjhbA-CeZ0OlnmbbwrLDEF9NMFbL01HjYcb_21R8TuVVn4jI6Wr71H9pUh9ba_MvVjOda1HoOZlKVsoXI5Uha3Ob-mGZanAuustzVNws1636btUKagmLQ5lfk2XcLQAFGJ2fJQ8EQNPiMlp5WMoTX00-9S4iDB_ivviajaeBBI?purpose=inline)](https://shapez2.com/?utm_source=chatgpt.com)

## Sources / Reliability

| Source | Reliability | Reason for use |
| ----------------------------------- | --: | ---------------------------------------- |
| Official website | High | Verified game overview, core systems, and 1.0 release information |
| Steam Store / Steam FAQ / SteamDB patch notes | High | Verified release date, price, platform, system requirements, and 1.0 changes |
| PC Gamer article | Medium | Supplementary interpretation of the 1.0 update and the meaning of Manufacture Mode |

---

# shapez 2 Core Summary

**shapez 2** is a **3D factory automation / logistics optimization game** in which you mine, decompose, rotate, cut, paint, and stack geometric shapes in space to automatically produce target shapes. There are no enemies, combat, time limits, or resource depletion; the structure focuses purely on factory design and optimization. Accuracy: High. ([shapez 2][1])

## Basic Information

| Item | Details |
| --------------- | --------------------------------------------------------------- |
| Genre | Factory automation, simulation, strategy, puzzle, sandbox |
| Developer | tobspr Games |
| Publisher | tobspr Games, Gamirror Games |
| Platform | Windows, macOS, SteamOS/Linux |
| Mode | Single-player |
| Early Access release | August 15, 2024 |
| 1.0 full release | April 23, 2026 |
| Korean language | Korean interface supported per Steam Store |
| Current Steam features | Steam Achievements, Steam Workshop, Steam Cloud, Family Sharing |

Accuracy: High. The Steam Store lists the release date as **April 23, 2026**, the Early Access release date as **August 15, 2024**, and also specifies developer/publisher, languages, and Steam features. ([Steam Store][2])

---

# Gameplay Structure

## 1. Objective

Supply specific shapes in bulk to the central hub **Vortex** or related platforms to unlock research, buildings, upgrades, and new systems. Per the Steam description, players produce and deliver shapes to unlock technology and expand the factory. Accuracy: High. ([Steam Store][2])

## 2. Basic Production Flow

The typical flow is as follows.

```text
Mine source shapes
→ Transport via belt/train
→ Cut / rotate / paint / stack / combine
→ Complete target shape
→ Deliver to Vortex or Trade Station
→ Unlock research/upgrades/new objectives
```

The official site describes core operations as **cutting, rotating, stacking, painting**, and Steam also describes a process of decomposing, painting, stacking, and reassembling shapes. Accuracy: High. ([shapez 2][1])

---

# Differences from shapez 1

| Aspect | shapez 1 | shapez 2 |
| ----- | -------- | ------------------------ |
| View/space | 2D plane-centric | 3D space platforms |
| Build structure | Flat expansion | **Multi-layer factory based on 3 build layers** |
| Transport | Belt-centric | Belts + space belts + trains |
| Painting | Paint/color mixing | Includes fluid-based painting |
| Scale | Infinite flat expansion | Large-scale expansion via platforms, trains, and blueprints |
| Depth | Minimal automation | Research, mods, trains, multi-layer design, modding support |

According to the official FAQ, shapez 2 has a basic structure similar to shapez 1, but the 3D world adds build layers, and because of space platforms, "space itself" also becomes something to manage. Trains, fluids for painting, a flexible research system, new game modes, Hexagonal shapes, and animated buildings that show internal workings were also added. Accuracy: High. ([Steam Community][3])

---

# Core Systems

## 1. Multi-Layer 3D Factory

Factories and platforms can be designed across **three build layers**. Rather than simply expanding sideways, you connect upper and lower layers to improve space efficiency. Accuracy: High. ([Steam Store][2])

## 2. Space Train

Handles long-distance transport in large-scale factories. In the 1.0 patch, train throughput was also strengthened: package size increased from **180 → 360 shapes**, and fluids from **1,800 → 3,600 liters**. Accuracy: High. ([SteamDB][4])

## 3. Research / Upgrade

Delivering target shapes unlocks new buildings, mechanisms, and upgrades. The Steam description states that the research system opens new buildings, mechanisms, and upgrades, expanding how you design factories. Accuracy: High. ([Steam Store][2])

## 4. Blueprint Library

You can save, load, send, and share factory designs. This is a core feature when building large modular factories. Accuracy: High. ([Steam Store][2])

## 5. Make-Anything-Machine, MAM

In advanced stages, you can design a **Make-Anything-Machine** that automatically reconfigures production lines or processes shapes signal-based regardless of which target shape arrives. The official site explains that MAM can be built with an advanced wiring system. Accuracy: High. ([shapez 2][1])

---

# 1.0 Update Highlights

The biggest changes alongside the April 23, 2026 1.0 release are as follows.

| Item | Details |
| ------------------- | --------------------------------------- |
| Manufacture Mode | New game mode. Focused on permanent, large-scale factories |
| Classic Mode expansion | Existing experience reorganized as Classic Mode with additional milestones/shapes |
| Modding | Official modding support via Steam Workshop |
| Achievements | 83 achievements added |
| Visual Improvements | Visual improvements to pipes, trains, fluids, wires, shaders, etc. |
| New Tutorial | Tutorial rework |
| New Shapes | X, Y shapes added |
| Codex | In-game manual expanded to 150+ pages |
| QoL | Improvements to placement, preview, UI, statistics, upgrade screens |

Accuracy: High. The 1.0 patch notes on SteamDB specify Manufacture Mode, 83 achievements, Steam Workshop modding, Classic Mode expansion, visual improvements, new tutorial, X/Y shapes, expanded Codex, and more. ([SteamDB][4])

---

# Game Modes

## Certification

An introductory scenario of roughly one hour for first-time players. Designed so that after learning basic operations and core systems, you naturally transition to Classic. Accuracy: High. ([SteamDB][4])

## Classic Mode

A mode that organizes the existing shapez 2 experience from the Early Access period. A traditional progression mixing logistics, shape puzzles, and factory automation. Accuracy: High. ([SteamDB][4])

## Manufacture Mode

A new mode added in 1.0. Rather than a structure of making specific shapes and discarding them, it strengthens the direction of building **large-scale factories used permanently**. The goal is to exchange shapes via Trade Station and rebuild the Vortex Platform. Accuracy: High. ([SteamDB][4])

## Hexagonal Mode

An experimental high-difficulty mode using a 6-segment structure instead of the default 4-segment shapes. The official FAQ explains that Hexagonal mode provides 6 segments per layer. Accuracy: High. ([Steam Community][3])

---

# Difficulty and Play Feel

shapez 2 deals with factory automation like Factorio, Satisfactory, and Dyson Sphere Program, but there is almost no combat, power shortage, resource depletion, or survival pressure. Therefore it focuses more on "factory design puzzles" and "throughput optimization." The Steam description also explicitly states that all buildings are free, resources do not deplete, and there are no enemies or time limits. Accuracy: High. ([Steam Store][2])

Play feel can be roughly summarized as follows.

| Likely to enjoy | May not be a fit |
| ------------------ | ------------------ |
| Enjoy automation puzzles | Want combat/survival/story focus |
| Enjoy belt organization, throughput optimization | Want resource mining competition, cost management |
| Enjoy large-scale factory scaling | Want only campaigns with clear objectives |
| Enjoy MAM, circuits, logic design | Find repetitive delivery structure tedious |

---

# System Requirements

## Windows

| Category | Minimum | Recommended |
| ------- | ------------------- | ------------------- |
| OS | Windows 10 64-bit | Windows 11 64-bit |
| CPU | Intel Core i5-10400 | Intel Core i5-12600 |
| RAM | 8 GB | 16 GB |
| GPU | GTX 750 Ti | RTX 2060 |
| DirectX | 11 | 11 |
| Storage | 2 GB | 2 GB |

Accuracy: High. Based on Steam Store system requirements. ([Steam Store][2])

If the user's PC is RTX 4090-class, performance bottlenecks are more likely to come from CPU/memory for large-scale factory simulation rather than the GPU. The official FAQ explains that you can typically finish the game with around 40,000 buildings, very smoothly up to 100,000 buildings, and 500,000–1,000,000 buildings are playable depending on the system. Accuracy: Medium–High. ([Steam Community][3])

---

# Price / Purchase Information

Per the current Steam Store, the base edition is listed at **$29.99** regular price, **$23.99** at 20% off, with the sale ending **May 7**. Accuracy: High, though prices may vary by region, sale, and time. ([Steam Store][2])

Supporter Edition is a supporter-oriented edition that includes additional music and railroad decoration elements. The Steam FAQ also explains that Supporter Edition is basically for supporting the developer, with bonus additional music and rail twisters/train loops. Accuracy: High. ([Steam Community][3])

---

# Shape Layers and Pin Mechanics

> **Sources / reliability**: Among the rules below, pin pusher, layer cap, and relationship with the painter are closer to player community summaries and in-game behavior observation. They may not map 1:1 to official Codex wording, so treat them with **Medium** reliability, and align solver implementation with the column-based vertical model in `django_apps/shapez_solver/services/operation_engine.py`.

## Core Rules

### Support and Gravity

- **Pins are vertical supports** that hold up stacked layers above them.
- **They do not "connect" horizontally to other shape parts** — adjacent pins in neighboring quadrants alone cannot keep a part with empty space below from floating.
- **Shape parts with no support below (same column)** and only adjacent pins beside them **fall** (in-game physics; horizontal adjacency alone does not anchor them).

### Layer Cap (5th layer rule)

- A shape stack has a **maximum of 4 layers** (normal). **Insane mode** allows up to **5 layers**.
- Exceeding the cap **destroys the entire top layer** (top slice removed).

### Pin Pusher

- Pushes a full pin layer **below** an existing shape, with a visual effect equivalent to the entire shape shifting **up one layer**.
- shapez2Solver's `pin_pusher` operation models this the same way: **prepend a layer fully filled with `P-` at the bottom**.

### Color Neutrality

- Pins have **no color** and **cannot be painted** by the painter. Paint operations change only shape parts; pins remain as `P-`.

## Community Applications

- **Isolated pins / pin tower only**: By repeatedly pushing pins to fit the layer limit, the top shape portion can **"pop"** off per the cap rule and fall away, leaving only a pin column.
- **Falling pin trick**: When the base below has a **hole (empty quadrant)**, pins that were above that column **drop down to the support layer below or the ground** (vertical column basis).
- **Passing through painter**: Pins stay unchanged; only shape parts stacked above change color.

## shapez2Solver Implementation Limits (Explicit)

- The engine performs only **stable compaction** for **independent vertical columns per quadrant**, gathering non-empty parts downward through empty cells.
- **"Only adjacent pins beside, empty below"** falling, which requires a **2D support graph**, is not included in this model. Add separate rules in a follow-up if needed.

---

# Compatibility / Limitations

| Item | Status |
| -------------- | -------------------------- |
| Steam Deck | Works but not officially supported |
| Controller | No official console controller support currently |
| Console release | No plans currently |
| Multiplayer/co-op | No plans currently |
| 4K / Ultrawide | Supported |
| Pre-1.0 saves | Not compatible |
| Pre-1.0 blueprints | Compatible but with warning; support may be discontinued later |

Accuracy: High. Based on official FAQ and 1.0 patch notes. ([Steam Community][3])

---

# Recommended Onboarding Path

1. **Play Certification first**  
   For learning basic operations, layers, belts, and production flow.

2. **Progress with Classic Regular**  
   Good for understanding shapez 2's basic shape puzzles and logistics structure.

3. **Make blueprints a habit**  
   Since the game involves repeatedly expanding the same modules, saving small production blocks is important.

4. **Don't try to build a perfect factory from the start**  
   Free deletion/relocation/redesign is assumed in this game. Spaghetti → cleanup → modularization is the normal order.

5. **Use trains actively from mid-to-late game**  
   Belts for short distances; trains for long-distance/bulk transport keeps the structure clean.

---

# Related Research (Throughput / Asteroids)

- Asteroid Space Belt/Pipe absolute throughput: [`../game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) (`CANON`). Legacy community draft: [`research_shapez2_space_transport_throughput_2026-05-18.md`](research_shapez2_space_transport_throughput_2026-05-18.md) (`SUPERSEDED`)

---

# Conclusion

**shapez 2 is closer to a "combat-free Factorio-style shape automation puzzle."**  
The core fun is not mining resources, but **how you modularize shape production processes, increase throughput, and scale to a large factory**.

As of 1.0, content has expanded significantly, and especially **Manufacture Mode + Steam Workshop modding + 83 achievements + Classic expansion** make it more complete than during Early Access. It is a good fit if you enjoy automation, logic design, MAM, and large-scale system optimization.

---

## Reference Links

[1]: https://shapez2.com/ "shapez 2 | Factory & Strategy game | Available now on Steam | 1.0 Release out April 23rd"  
[2]: https://store.steampowered.com/app/2162800/shapez_2__Factory/ "Save 20% on shapez 2 - Factory on Steam"  
[3]: https://steamcommunity.com/app/2162800/discussions/0/806849231160779528/ "shapez 2 - 1.0 Release FAQ :: shapez 2 - Factory General Discussions"  
[4]: https://steamdb.info/patchnotes/22785032/ "shapez 2 - 1.0 is OUT NOW! · shapez 2 - Factory update for 23 April 2026 · SteamDB"
