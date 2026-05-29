# {{PROJECT_NAME}} MCP

Per AGENTS.md, assess whether MCP can be used before related work. If no MCP is available, fall back to local files and standard verification and record that fact.

## context7

- Prioritize when latest documentation is needed, such as for new libraries or framework API usage.
- Do not copy external API examples verbatim; separate them to match project layer boundaries into application ports and adapters.

## GitLens

- Consider using when change history, regression root cause, PR review prep, or branch analysis is needed.
- Confirm history-based inference together with current file contents.

## cursor-ide-browser

- Use when UI visual verification, web documentation validation, or browser-based interaction checks are needed.

## Schema verification

- In environments where `call_mcp_tool` or `fetch_mcp_resource` must be invoked directly, check the `mcps/<server>/tools/` schema first.
- If the tool is missing or fails, record the failure reason and use a local alternative.
