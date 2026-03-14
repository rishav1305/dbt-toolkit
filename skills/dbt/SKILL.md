---
name: dbt
description: "dbt project management — run, test, debug, audit, and more"
---

# dbt-toolkit Router

Single entry point for all dbt-toolkit skills.

## Behavior

1. Check if `.dbt-toolkit/config.yaml` exists alongside `dbt_project.yml`
2. If missing → invoke `dbt-toolkit:dbt-setup`
3. If present → show status + menu or parse user intent

## Status Display

When invoked with no arguments, show:

```
[dbt-toolkit] Project: {project_name} (profile: {profile_name} → {target})
  Execution: {method}
  Models: {count} models, {source_count} sources, {test_count} tests
  Last run: {status}

Available commands:
  run        Execute models with smart selection
  test       Run tests, analyze failures, coverage report
  freshness  Check source data freshness
  audit      Proactive health checks
  debug      Guided troubleshooting
  setup      Reconfigure project
  develop    Scaffold, compile, preview, lineage
  docs       Generate and serve documentation
  artifacts  Parse and compare run outputs
  seed       Seed loading, SCD snapshots
  deps       Install and manage packages
  macro      Execute dbt macros (grants, utilities)
```

## Routing Table

| Input | Skill |
|---|---|
| `setup`, `init`, `configure` | `dbt-toolkit:dbt-setup` |
| `run`, `build`, `execute` | `dbt-toolkit:dbt-run` |
| `test`, `validate data` | `dbt-toolkit:dbt-test` |
| `freshness`, `sources`, `stale` | `dbt-toolkit:dbt-freshness` |
| `debug`, `fix`, `troubleshoot` | `dbt-toolkit:dbt-debug` |
| `audit`, `health`, `check` | `dbt-toolkit:dbt-audit` |
| `develop`, `new model`, `create` | `dbt-toolkit:dbt-develop` |
| `docs`, `document`, `catalog` | `dbt-toolkit:dbt-docs` |
| `artifacts`, `results`, `manifest` | `dbt-toolkit:dbt-artifacts` |
| `seed`, `snapshot` | `dbt-toolkit:dbt-seed-snapshot` |
| `deps`, `packages`, `install` | `dbt-toolkit:dbt-deps` |
| `run-operation`, `macro`, `grant` | `dbt-toolkit:dbt-run-operation` |
| `brainstorm`, `plan change` | `dbt-toolkit:dbt-brainstorming` |
| `execute plan` | `dbt-toolkit:dbt-executing-plans` |
| `review` | `dbt-toolkit:dbt-code-review` |

For free-form input, use NLP matching to find the closest skill from the routing table.

## Conversation Principles (Mandatory)

- **NEVER ask:** CLI flags, config syntax, profile setup, connection strings, YAML formatting, env var names
- **ONLY ask:** Business intent ("which models?"), logic validation ("does this look right?"), data correctness, approval gates ("run these 6 models?")
- Auto-resolve everything else from config + project state
