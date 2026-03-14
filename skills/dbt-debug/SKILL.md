---
name: dbt-debug
description: "Systematic troubleshooting for connection, compilation, SQL, and test failures"
---

# dbt Debug

Systematic troubleshooting — guided flow, not just `dbt debug`.

## Entry Points

- User says "something broke" → ask what happened
- Invoked from run/test skill on failure → arrives with error context

## Categories

| Category | Detection | Resolution |
|---|---|---|
| Connection | `dbt debug` fails | Check profile, target, credentials, network |
| Compilation | `dbt compile` error | Show Jinja traceback, pinpoint file + line, suggest fix |
| Runtime SQL | Model fails during execution | Extract SQL error from run_results, show compiled SQL, identify root cause |
| Test failure | Test returns rows | Dispatch `test-failure-agent` for root-cause analysis |
| Performance | Model takes unusually long | Check materialization, sort/dist keys, row counts, suggest optimizations |
| Incremental drift | Unexpected row counts | Compare full-refresh vs incremental, check `unique_key` for nulls |
| Parse errors | `dbt parse` fails | YAML/Jinja syntax issues, missing refs, circular dependencies |

## Smart Features

- **Error pattern matching:** Common dbt/Redshift errors mapped to known fixes (see `references/common-pitfalls.md`)
- **Compiled SQL access:** On SQL errors, retrieve from `target/compiled/` or `run_results.json` `compiled_code` field
- **Diff against last success:** Compare current model SQL against last-succeeded version (from git)

## Error Pattern Database

Uses `scripts/error_patterns.py` to automatically match errors against 17 known patterns across 8 categories:

- **Connection:** refused, timeout, auth failure
- **Compilation:** undefined ref, missing node, circular dependency
- **Runtime SQL:** relation not found, duplicate key, missing column, disk full
- **Permission:** access denied, insufficient privileges
- **Performance:** statement timeout, serializable isolation
- **Parse:** YAML errors, Jinja template errors
- **Redshift:** Spectrum CTAS collision, MERGE not supported
- **Incremental:** schema change, full refresh needed

Each pattern provides:
- **Category** for routing to the right resolution path
- **Description** of what went wrong
- **Suggestions** — actionable steps to fix the issue

When an error is matched, show the suggestions directly instead of asking the user to investigate.

## Conversation Principles

- NEVER ask about error codes or stack traces — parse them automatically
- ONLY ask: what were you trying to do, does this fix look right
