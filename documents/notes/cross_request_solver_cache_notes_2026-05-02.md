# Cross-request solver cache (notes)

## Context

`SolveContext` holds a per-solve `memo: dict[str, SolvedRecipe]` used during one `PlannerService.solve_shape` recursion tree. Each HTTP request still constructs a new `SolveContext()`, so **sub-shapes solved in an earlier request are not reused** from that memo.

## Why the default is reasonable

- **Isolation**: No accidental sharing of mutable planner state across users or requests.
- **Thread safety**: A global dict without careful locking would be unsafe under concurrent workers.

## If we add cross-request caching later

- **Key**: `canonical_code` (or a versioned tuple if planner rules change).
- **Value**: Immutable or frozen `SolvedRecipe` snapshot, or a cheap serializable summary—**not** live `SolveContext` instances shared across threads.
- **Eviction**: Bounded LRU or TTL to cap memory; consider explicit **version** in the cache key when planner rules or game data YAML change.
- **Invalidation**: On deploy, process restart clears in-memory caches; document whether Redis (or similar) is required for multi-worker sharing.

**Status (2026-05-02):** No process-wide LRU implemented; this file records tradeoffs for a future scoped change.
