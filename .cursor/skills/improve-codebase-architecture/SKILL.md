---
name: improve-codebase-architecture
description: >-
  Review-only architecture improvement: find scattered, shallow, temporally
  decomposed, overexposed, or conjoined code; propose deeper modules behind
  simpler interfaces (Ousterhout). Use for /improve-codebase-architecture,
  refactor opportunities, complexity reduction, or seam identification. No
  implementation without explicit user approval.
disable-model-invocation: false
metadata:
  owner: project
  risk: normal
  requires_validation: false
---

# `/improve-codebase-architecture`

Improve codebase architecture by finding related code that is scattered, duplicated, leaky, shallow, temporally decomposed, overexposed, conjoined, or hard to change, then proposing a small architecture improvement that wraps the related behavior behind a deeper module.

This skill is **review-only by default**.

Do **not** edit code, create files, rewrite modules, or open PRs unless the user explicitly approves implementation after reviewing the architecture report.

---

## Non-Negotiable Rules

1. **No implementation without approval.**

   * First run produces an architecture report only.
   * Implementation requires a separate explicit user request.

2. **Small strategic improvements only.**

   * Prefer narrow, reversible refactors.
   * Avoid broad rewrites, framework migrations, or speculative redesign.

3. **Evidence before design.**

   * Do not propose a new module from names alone.
   * Read real code, call sites, tests, and boundary contracts.

4. **A refactor must make a future change easier.**

   * If you cannot name the concrete future change that becomes easier, do not recommend the refactor yet.

5. **Deep module over shallow wrappers.**

   * The target is a smaller, clearer interface that hides related implementation complexity.
   * Do not create pass-through abstractions that simply rename existing calls.

6. **Prefer simple interfaces over simple implementations.**

   * It is acceptable for the proposed module implementation to become slightly more complex if the caller-facing interface becomes meaningfully simpler.
   * Pull complexity downward into the module when doing so reduces caller knowledge, repeated policy, or special-case handling.

---

## Purpose

Use this skill to repeatedly improve a codebase through small, reusable architecture reviews.

The goal is to reduce software complexity by:

* reducing change amplification
* reducing cognitive load
* eliminating unknown unknowns
* hiding implementation details behind clear interfaces
* centralizing scattered design decisions
* replacing shallow wrappers with deeper modules
* making common cases simple
* isolating or eliminating special cases
* clarifying module ownership
* reducing exception and error-handling burden
* making module boundaries follow information hiding rather than execution order

---

## When to Use

Use this skill when the user asks for:

* `/improve-codebase-architecture`
* architecture cleanup
* codebase design improvement
* refactor opportunities
* reducing complexity
* finding seams for deeper modules
* identifying bad abstractions
* wrapping related code into a module
* simplifying future changes

Do **not** use this skill for:

* simple bug fixes
* one-file tactical cleanup
* formatting-only changes
* performance tuning without architecture symptoms
* large rewrites without a narrow target
* dependency upgrades
* pure documentation edits

---

## Core Evaluation Model

A useful architecture improvement should improve at least one of these:

| Complexity Symptom                                 | Architecture Target                                                |
| -------------------------------------------------- | ------------------------------------------------------------------ |
| A simple change requires edits in many places      | Centralize the design decision                                     |
| Callers must know too much                         | Pull complexity downward                                           |
| Important dependency is hidden                     | Make the dependency explicit or encapsulated                       |
| Related logic is scattered by execution phase      | Replace temporal decomposition with information hiding             |
| Interface mirrors implementation                   | Create a deeper abstraction                                        |
| Many tiny wrappers exist                           | Remove pass-through layers                                         |
| Two methods cannot be understood independently     | Merge, split differently, or introduce a shared deeper abstraction |
| Common usage requires rare-feature knowledge       | Reduce overexposure                                                |
| Special cases leak everywhere                      | Define the special case out of existence or isolate it             |
| Error handling dominates call sites                | Define errors out of existence, mask them, or aggregate them       |
| Data shape is manually repeated                    | Introduce a boundary contract or converter                         |
| General-purpose and special-purpose code are mixed | Separate reusable mechanism from domain-specific policy            |

---

## Project Navigation Rule

Use the repository's own navigation system first.

Examples of project-native navigation tools:

* Graphify
* language server references
* repo-specific architecture docs
* dependency graph tools
* code index tools
* existing `AGENTS.md` / `.cursor/rules` / skill routing docs

If a project-native tool exists, use it before generic grep or semantic search.

For example, if Graphify exists:

```bash
graphify query "<architecture question or suspected area>"
graphify explain "<central concept or module>"
graphify path "<source module>" "<target module>"
```

If no project-native tool exists, fall back to normal code search:

```bash
rg "<domain term>"
rg "<function_or_type_name>"
rg "<wire field>"
rg "<magic string>"
rg "<shared error message>"
```

---

## Red Flag Checklist

Use this checklist during exploration. A red flag is not automatically a refactor request; it is evidence that a design alternative should be considered.

Record only the red flags that actually apply. Do not force every finding into every category.

### Deep Module Problems

* **Shallow module:** interface is not much simpler than implementation.
* **Pass-through method:** method mostly forwards arguments to another method with a similar signature.
* **Conjoined methods:** two methods or code regions are so dependent that one cannot be understood without understanding the other.
* **Classitis / wrapper sprawl:** many small classes or helpers add interfaces without hiding meaningful complexity.
* **Hard to describe:** a precise interface comment would need to be long or full of caveats.

### Information Hiding Problems

* **Information leakage:** one design decision appears in multiple modules.
* **Repeated policy:** same rule, enum, wire field, validation, default, or lifecycle step appears in several places.
* **Unknown unknown:** important dependency exists but is not discoverable from the interface.
* **Cross-module comments:** comments explain requirements that the code does not enforce.

### Temporal Decomposition Problems

* code is split by execution order rather than by ownership of knowledge
* "read then parse," "build then validate," "compose then patch," or similar phases duplicate the same domain knowledge
* multiple phases must understand the same file format, wire shape, protocol, or lifecycle invariant
* changing one design decision requires edits in several temporal steps

Temporal decomposition is only acceptable when each stage truly owns different knowledge.

### Overexposure Problems

* common callers must pass rarely changed options
* common callers must understand optional features to perform the default operation
* constructors or APIs require low-level parameters that almost always have the same value
* caller must explicitly request behavior that should be the default
* rare overrides are mixed into the common path instead of isolated behind a separate method or options object

### Error and Special-Case Problems

* many call sites handle the same exception
* caller must check for a condition that the module could handle internally
* special cases create repeated `if` branches
* "none," "missing," "empty," or "not found" states are represented in a way that forces special handling everywhere
* error policy is inconsistent across call sites

### Special-General Mixture Problems

* special-purpose policy is mixed into a general-purpose utility
* a high-level policy is duplicated in low-level helpers
* general-purpose code imports domain-specific concepts
* a reusable helper exposes options needed by only one special case
* **Same abstraction in adjacent layers:** neighboring layers expose nearly identical concepts instead of different abstractions (Ousterhout Principle 9)

---

## Procedure

### Phase 0 — Safety and Scope Gate

Run:

```bash
git status --short
```

If the worktree is dirty, report it. Do not overwrite unrelated work.

Define the review scope.

Bad scope:

```text
Improve the whole replay system.
```

Good scope:

```text
Improve replay overlay wire serialization boundary.
```

Capture:

```text
Scope:
Repository state:
User-approved limits:
Implementation allowed: no
```

Stop immediately if the user requested a broad redesign but did not provide a target area. Ask for a narrower area or propose 2–3 candidate areas to inspect.

---

### Phase 1 — Build the Current Architecture Map

Identify the current shape of the selected area.

Record:

```text
Domain:
Current entry points:
Core data types:
Main call chain:
External boundaries:
Public interfaces:
Tests:
Docs / ADRs:
```

Read real code for:

* public interfaces
* main call sites
* data flow
* error handling
* serialization / deserialization
* persistence boundaries
* UI/API contracts
* tests
* existing docs
* recent TODOs or comments

Do not infer ownership from filenames alone.

---

### Phase 2 — Find Scattered Knowledge and Classify Complexity

Search for related logic, duplicated policy, repeated contracts, non-obvious dependencies, temporal decomposition, overexposure, conjoined methods, and error-policy leakage.

Useful search targets:

```bash
rg "<domain enum>"
rg "<wire field>"
rg "<magic string>"
rg "<validation rule>"
rg "<same error message>"
rg "<same data shape>"
rg "<lifecycle step>"
rg "<default value>"
rg "<exception type>"
rg "<optional parameter>"
```

For each finding, record only what applies. Use inline labels — do not use multi-line category blocks that invite empty "N/A" filler.

```text
Finding: serialization shape repeated in router.py, worker.py, queue.py
Red flags: Information leakage, Temporal decomposition
Future change hardened: adding a new field requires edits in 3 files
```

Add complexity symptoms only when they apply, on the same line or as a short second line:

```text
Finding: three call sites repeat the same empty-state guard before wire build
Red flags: Error / special-case leakage, Repeated policy
Complexity: Change amplification (3 sites), Cognitive load (callers must know wire invariants)
Future change hardened: changing empty-state policy requires coordinated edits across callers
```

Do not enumerate every red-flag category per finding. Name only the flags that actually apply.

Use this table once per review (not per finding):

| Question                                                           | Answer |
| ------------------------------------------------------------------ | ------ |
| What simple future change is currently hard?                       |        |
| How many places must change?                                       |        |
| What must callers know?                                            |        |
| What is implicit or undocumented?                                  |        |
| Which dependency is non-obvious?                                   |        |
| Is code organized by execution order rather than hidden knowledge? |        |
| Does the common path expose rare features?                         |        |
| Are two methods or regions hard to understand independently?       |        |
| Are errors or special cases repeated across callers?               |        |
| Which module should own the design decision?                       |        |

If the evidence does not show meaningful complexity, stop and report that no refactor is justified yet.

---

### Phase 3 — Decide Better Together vs Better Apart

Before proposing a new module, decide whether the related code should be joined, separated, or left alone.

#### Bring together when:

* pieces share private knowledge
* pieces change together
* pieces duplicate the same policy
* pieces form one lifecycle
* separation forces pass-through parameters
* separation creates temporal ordering bugs
* callers must manually coordinate the pieces
* temporal phases repeat the same format, protocol, or domain rules
* bringing pieces together would simplify the common interface
* conjoined methods can be replaced by a clearer single abstraction

#### Keep apart when:

* one part is general-purpose and reusable
* one part is special-case policy
* combining them would expose irrelevant options
* the combined interface would become larger for common users
* the pieces have unrelated reasons to change
* joining them would create a manager/god object
* the execution stages use genuinely different knowledge
* adjacent layers would end up exposing the same abstraction

Decision format:

```text
Decision:
- Better together:
- Better apart:
- Chosen boundary:
- Reason:
```

The chosen boundary becomes the candidate module boundary.

---

### Phase 4 — Design the Deep Module Candidate

A good deep module hides more than it exposes.

The design goal is not to make the module implementation small. The design goal is to make the caller-facing interface simple, obvious, and hard to misuse, even if that requires pulling complexity downward into the module.

Define the module contract:

```text
Proposed module:
Owns:
Hides:
Exposes:
Does not expose:
Caller responsibilities:
Module responsibilities:
Invariants:
Default behavior:
Error policy:
Special-case policy:
Migration path:
```

Use an interface comment draft as a design probe before finalizing the interface:

```text
Interface comment draft:
<Describe what the module does, what callers must know, what it guarantees, and how common callers use it. Do not describe private implementation details.>
```

Use the comment as a design test:

* If the comment mostly repeats the code, the abstraction may be shallow.
* If the comment exposes implementation details, the interface may leak information.
* If the comment is long because of many exceptions, the error policy may be wrong.
* If the comment is hard to write precisely, the boundary or name may be wrong.
* If common usage needs several caveats, the interface is probably overexposed.

Interface sketch:

```text
Name:
Inputs:
Outputs:
Errors:
Common case:
Rare override path:
```

#### Error Policy Review

Before exposing an error or exception, ask:

| Question                                                        | Design Direction                  |
| --------------------------------------------------------------- | --------------------------------- |
| Can the module choose a safe default?                           | define the error out of existence |
| Can the module make the operation idempotent?                   | remove caller-side pre-checks     |
| Can an empty value represent the special case?                  | eliminate repeated `none` checks  |
| Can several low-level exceptions become one high-level failure? | aggregate exceptions              |
| Can the module recover or mask the error?                       | hide low-level details            |
| Is the condition unrecoverable for this application?            | fail fast with a clear message    |
| Does the caller genuinely need to decide?                       | expose the error deliberately     |

Prefer interfaces like:

```text
effective_cell_to_wire(view) -> EffectiveCellWire
```

Avoid interfaces like:

```text
build_dict_with_transport_and_candidate_and_layer_and_style(...)
```

Prefer domain names over implementation-mechanic names.

Reject candidates that:

* create a manager/god object
* only move code without reducing caller knowledge
* increase public API surface
* preserve the same scattered policy under a new name
* hide important constraints from users
* require a broad simultaneous rewrite
* introduce pass-through methods
* make the common case harder
* force common callers to learn rare options
* expose errors that the module could eliminate or aggregate
* keep conjoined methods conjoined under new names

---

### Phase 5 — Design It Twice

Produce at least two viable designs before recommending one.

Do not treat this as a numeric scoring exercise. The purpose is to compare competing abstractions and determine which one makes the common case simplest for higher-level code.

```text
Option A:
- Summary:
- Interface:
- Interface comment draft:
- Common-case usage:
- Rare-case usage:
- What it hides:
- What it exposes:
- Pros:
- Cons:
- Failure mode:

Option B:
- Summary:
- Interface:
- Interface comment draft:
- Common-case usage:
- Rare-case usage:
- What it hides:
- What it exposes:
- Pros:
- Cons:
- Failure mode:
```

Compare the options using these questions:

| Question                                                              | Option A | Option B |
| --------------------------------------------------------------------- | -------- | -------- |
| Which interface is simpler for the common case?                       |          |          |
| Which design hides more implementation knowledge?                     |          |          |
| Which design avoids overexposing rare features?                       |          |          |
| Which design better eliminates repeated errors or special cases?      |          |          |
| Which design avoids temporal decomposition?                           |          |          |
| Which design avoids conjoined methods?                                |          |          |
| Which design keeps general-purpose and special-purpose code separate? |          |          |
| Which design is easier to explain in an interface comment?            |          |          |
| Which design has the safer migration path?                            |          |          |

Choose the design that makes the common case obvious and keeps rare cases isolated.

If neither design is attractive, do not force a recommendation. Use the weaknesses of both designs to propose a third option or stop with open questions.

---

## Architecture Report Format

Use this exact report format for review-only runs.

```markdown
## Architecture Improvement Report

### Scope

### Repository State

### Current Architecture Map

| Item | Finding |
|---|---|

### Complexity Symptoms and Red Flags

| Symptom / Red Flag | Evidence | Impact | Refactor Pressure |
|---|---|---|---|

### Scattered Knowledge Found

| Shared Knowledge | Files / Areas | Current Risk |
|---|---|---|

### Better Together / Better Apart Decision

**Bring together:**

**Keep apart:**

**Chosen boundary:**

**Reason:**

### Deep Module Candidate

**Proposed module:**

**Owns:**

**Hides:**

**Exposes:**

**Does not expose:**

**Caller responsibilities:**

**Module responsibilities:**

**Invariants:**

**Default behavior:**

**Error policy:**

**Special-case policy:**

**Non-goals:**

### Interface Comment Draft

\`\`\`text
<draft comment here>
\`\`\`

### Design Alternatives

#### Option A

#### Option B

### Recommendation

### Minimal Change Plan

Describe the smallest safe implementation path.

Use one PR if the change is narrow.

Use multiple PRs only when needed, for example:

* PR 1: introduce contract/module and migrate one production path
* PR 2: migrate remaining call sites
* PR 3: remove compatibility shim
* PR 4: update docs if public contracts changed

### Tests / Validation

### Stop Conditions

### Open Questions
```

End review-only runs with:

```text
STOPPED_AT_ARCHITECTURE_REVIEW
No code changes made.
```

---

## Implementation Mode

Only enter this section after explicit user approval.

Implementation approval examples:

```text
Implement Option A.
Apply the minimal PR plan.
Proceed with the refactor.
```

When implementing:

1. confirm repository state
2. preserve unrelated dirty work
3. create or update tests first when practical
4. add the deep module with a narrow public interface
5. migrate one call path at a time
6. keep compatibility shims only when necessary
7. remove shims in a later phase if risky
8. update docs only for public contract changes
9. run the smallest meaningful validation first
10. then run broader validation

Implementation must stay inside the approved scope.

---

## Validation Checklist

Before finalizing implementation, verify in this order:

### 1. Behavior preservation

* no unrelated behavior changed
* tests cover old and new behavior

### 2. Interface quality

* public interface is smaller than scattered prior usage
* common case became simpler
* call sites no longer know private details
* implementation complexity moved behind the module
* no hidden dependency remains undocumented
* names match the domain language
* interface comments describe non-obvious guarantees without leaking implementation details

### 3. Design principles compliance

* no new pass-through layer was introduced
* no large rewrite was smuggled in
* temporal decomposition was reduced or justified
* rare options are not exposed to common callers
* conjoined methods were eliminated, merged, or justified
* repeated exceptions or special cases were eliminated, masked, or aggregated
* general-purpose and special-purpose code are cleanly separated

---

## Final Response Contract

For review-only runs:

```text
STOPPED_AT_ARCHITECTURE_REVIEW
No code changes made.
```

For implementation runs:

```text
Final Report
- Changed:
- Tests:
- Remaining risk:
- Follow-up:
```

If blocked:

```text
BLOCKED
Reason:
Tried:
Next:
```
