---
name: dbt-develop
description: "Scaffold new models, compile and preview SQL, explore lineage, refactor"
---

# dbt Develop

Model development workflow — scaffold, compile, preview, and explore.

## Capabilities

### 1. Scaffold New Model

- Ask business intent ("what does this model calculate?")
- Generate SQL with correct `ref()` and `source()` calls
- Place in correct directory based on naming convention (staging/intermediate/marts)
- Create YAML schema entry with columns and descriptions
- Use `templates/model.sql` as starting point

### 2. Compile & Preview

- `dbt compile --select model_name` — show compiled SQL without executing
- `dbt show --select model_name` — execute and show output rows
- `dbt show --inline "SELECT ..."` — run ad-hoc queries against the warehouse
- Note: `--select` and `--inline` are mutually exclusive flags

### 3. Lineage Exploration

- Dispatch `lineage-agent` to traverse manifest DAG
- Show upstream/downstream chains with materializations
- Impact analysis: "if I change model X, what breaks?"

### 4. Refactor Assistance

- Extract repeated SQL into macros
- Split large models into smaller, focused CTEs or separate models
- Convert hardcoded values to `var()` refs
- Suggest materialization changes based on usage patterns

## Conversation Principles

- NEVER ask about SQL syntax or dbt config
- ONLY ask: what does this model need to do, does the generated SQL look right
