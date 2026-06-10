# frontend AGENTS.md

## Scope

Vite/TypeScript frontend packages: recipe graph editor and graph layout engine.

## Rules

- Keep graph layout deterministic and data-driven.
- UI state must be serializable enough for tests and clipboard/fixture checks.
- Do not duplicate backend business policy in frontend code.
- Preserve accessibility for controls and keyboard workflows.
- Prefer focused package tests before broad rebuilds.

## Verify

- Use the package scripts relevant to the touched frontend package.
- For visible changes, verify in browser or screenshot when practical.
