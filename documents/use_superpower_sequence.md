Role: Workflow Architect

Correct. **`/superpowers:brainstorm`, `/superpowers:write-plan`, `/superpowers:execute-plan` style descriptions are outdated as of this commit.**
Looking at the specified `b7a8f769...` tree, `commands/` has only three entries, and all three are marked **Deprecated**. Each directs you to use the new approach via the `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:executing-plans` skills. ([GitHub][1])

## 1. Cursor Installation

In Cursor Agent chat:

```text
/add-plugin superpowers
```

Per the README, this is the correct Cursor install command. You can also search for `superpowers` in the Marketplace. ([GitHub][2])

---

## 2. Core of the Current Approach

As of this commit, Superpowers is less "a tool where you type commands directly" and more:

```text
Installed plugin provides skills / agents / commands / hooks
↓
Agent invokes the appropriate skill for the situation
↓
User may explicitly request a specific skill when needed
```

The Cursor plugin manifest also registers `skills`, `agents`, `commands`, and `hooks` paths. ([GitHub][3])

The README also says "skills trigger automatically" — you do not need to do anything special. To verify installation, say something like `help me plan this feature` or `let's debug this issue` and check whether the relevant skill is invoked automatically. ([GitHub][2])

---

## 3. Actual Usage Phrases

### New Feature / Large Change

```text
Use the superpowers:brainstorming skill.

I want to build [feature description].
Do not write code yet.
Start by understanding the goal, asking questions, and proposing design options.
```

After design approval:

```text
Use the superpowers:writing-plans skill to create an implementation plan from the approved design.
```

After plan approval:

```text
Use the superpowers:executing-plans skill to execute this plan task by task.
```

### Bug Fix

```text
Use the superpowers:systematic-debugging skill.

Investigate this bug without jumping straight to a fix.
Find the root cause first, then propose the fix and verification.
```

### Verification Before Declaring Complete

```text
Use the superpowers:verification-before-completion skill.

Verify this is actually fixed before saying the task is complete.
```

### Branch Wrap-Up

```text
Use the superpowers:finishing-a-development-branch skill.

Run the required verification, then present merge / PR / keep / discard options.
```

---

## 4. Typical Usage Sequence

Per the README Basic Workflow, the order is: ([GitHub][2])

```text
1. superpowers:brainstorming
2. superpowers:using-git-worktrees
3. superpowers:writing-plans
4. superpowers:subagent-driven-development
   or superpowers:executing-plans
5. superpowers:test-driven-development
6. superpowers:requesting-code-review
7. superpowers:finishing-a-development-branch
```

In practice, use it like this:

```text
"Use superpowers:brainstorming for this feature."
↓
Design approval
↓
"Use superpowers:writing-plans."
↓
Plan approval
↓
"Use superpowers:subagent-driven-development to implement it."
```

If subagents are unavailable or limited in your Cursor environment:

```text
"Use superpowers:executing-plans instead."
```

---

## 5. Current Skill List

List from the `skills/` directory at the specified commit. ([GitHub][4])

| Skill                            | Purpose                        |
| -------------------------------- | ------------------------- |
| `using-superpowers`              | Skill system usage rules           |
| `brainstorming`                  | Requirements/design before implementation           |
| `writing-plans`                  | Convert approved design into implementation plan        |
| `executing-plans`                | Execute plan in order               |
| `subagent-driven-development`    | Per-task subagent execution + review    |
| `test-driven-development`        | Enforce RED-GREEN-REFACTOR     |
| `systematic-debugging`           | Root-cause-driven debugging              |
| `verification-before-completion` | Verify before declaring complete                |
| `requesting-code-review`         | Pre-review checklist             |
| `receiving-code-review`          | Apply review feedback                 |
| `using-git-worktrees`            | Isolated worktree/branch work     |
| `dispatching-parallel-agents`    | Parallel subagent work            |
| `finishing-a-development-branch` | merge/PR/keep/discard wrap-up |
| `writing-skills`                 | Author new skills                |

---

## 6. Important Correction

### Old Style

```text
/superpowers:brainstorm
/superpowers:write-plan
/superpowers:execute-plan
```

### Recommended (Current Commit)

```text
Use superpowers:brainstorming.
Use superpowers:writing-plans.
Use superpowers:executing-plans.
```

`commands/brainstorm.md`, `commands/write-plan.md`, and `commands/execute-plan.md` are all marked "deprecated" and scheduled for removal in the next major release. ([GitHub][5])

---

## Conclusion

As of the current baseline, the correct approach is **not memorizing slash commands, but directly instructing skill names or letting them auto-trigger**.

Minimum set to remember — these 5:

```text
superpowers:brainstorming
superpowers:writing-plans
superpowers:executing-plans
superpowers:systematic-debugging
superpowers:verification-before-completion
```

And do not use these 3 outdated ones:

```text
/superpowers:brainstorm
/superpowers:write-plan
/superpowers:execute-plan
```

[1]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/commands "superpowers/commands at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[2]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 "GitHub - obra/superpowers at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · GitHub"
[3]: https://github.com/obra/superpowers/blob/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/.cursor-plugin/plugin.json "superpowers/.cursor-plugin/plugin.json at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[4]: https://github.com/obra/superpowers/tree/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/skills "superpowers/skills at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
[5]: https://github.com/obra/superpowers/blob/b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37/commands/brainstorm.md "superpowers/commands/brainstorm.md at b7a8f76985f1e93e75dd2f2a3b424dc731bd9d37 · obra/superpowers · GitHub"
