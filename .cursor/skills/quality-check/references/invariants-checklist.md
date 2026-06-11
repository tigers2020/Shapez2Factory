# Invariant checklist (plan + diff review)

**CANON spec / ADR beats this table.**

## Governance

| Check | Source |
|---|---|
| Contract before production behavior | [AGENTS.md](../../../../AGENTS.md), [workflow.mdc](../../../rules/workflow.mdc) |
| One PR · one purpose | [workflow.mdc](../../../rules/workflow.mdc) |
| Stale docs ≠ authority | [START_HERE.md](../../../../documents/ai/START_HERE.md) |

## Asteroid Lab

| Topic | Flag if plan… |
|---|---|
| ReconstructionCompleteMap | Uses replay/artifact as solver terrain input |
| Layer 3/4 | Cites retired Layer 3/4 docs as authority |
| Decontamination | Revives RTTP/MEG or deleted paths |
| Coordinates | Server-coords bridge or wrong frame |
| Replay | Metrics/NDJSON as algorithm input |
| Route domain | Patches outside `RouteDomainSnapshotBuilder` |
| Validation | Repairs topology in validation |
| Enums | Free-form failure/event strings |

Rule: [asteroid-lab-invariants.mdc](../../../rules/asteroid-lab-invariants.mdc)

Algorithm index: `documents/Algorithm/asteroid_lab_*.md`

## Tests

| Check | Source |
|---|---|
| Repro on HEAD before fix | [AGENTS.md](../../../../AGENTS.md) |
| No pytest quiet flags | [testing.md](../../../../documents/ai/manuals/testing.md) |
