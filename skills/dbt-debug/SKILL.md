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

## Conversation Principles

- NEVER ask about error codes or stack traces — parse them automatically
- ONLY ask: what were you trying to do, does this fix look right
