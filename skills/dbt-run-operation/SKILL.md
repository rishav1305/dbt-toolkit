---
name: dbt-run-operation
description: "Execute dbt macros — grants, data masking, utility operations"
---

# dbt Run Operation — Macro Execution

Execute dbt macros directly via `dbt run-operation`.

## Capabilities

### 1. Execute Macro
- Run any macro: `dbt run-operation macro_name --args '{key: value}'`
- Parse output for success/failure
- Common macros:
  - `grant_select_on_schemas` — permission management
  - `generate_model_yaml` (codegen) — YAML generation
  - `generate_base_model` (codegen) — base model scaffolding
  - Custom project macros

### 2. Discover Macros
- List available macros from manifest.json
- Show macro signature (arguments with defaults)
- Filter by package (project macros vs dbt-utils vs custom packages)

### 3. Grant Management
Common grant operations:
- Grant SELECT on all models in schema to a role
- Grant USAGE on schema
- Revoke permissions

### 4. Data Operations
- Run custom data quality checks via macros
- Execute one-off data fixes
- Run seed-related macros

## Flow

1. Parse intent: which macro, what arguments
2. Discover available macros if user is unsure
3. Build `dbt run-operation` command with `--args` JSON
4. Execute via runner
5. Parse output
6. Report results

## Safety

- Always show the macro name and arguments before executing
- Require confirmation for macros that modify data (DELETE, UPDATE, DROP)
- Log all macro executions for audit trail

## Conversation Principles

- NEVER ask about `--args` JSON syntax
- ONLY ask: what do you want to accomplish, which macro should we use
