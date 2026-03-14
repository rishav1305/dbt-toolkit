---
name: dbt-deps
description: "Install and manage dbt packages — dbt-utils, dbt-expectations, custom packages"
---

# dbt Deps — Package Management

Install, update, and manage dbt packages.

## Capabilities

### 1. Install Packages
- Execute `dbt deps` to install/update all packages from `packages.yml`
- Parse output to report installed packages and versions
- Detect version conflicts and suggest resolutions

### 2. Package Discovery
- Read `packages.yml` to list currently installed packages
- Identify commonly used packages not yet installed:
  - `dbt-utils` — generic tests, SQL helpers, cross-database macros
  - `dbt-expectations` — Great Expectations-style data tests
  - `codegen` — generate model YAML, base models from sources
  - `dbt-audit-helper` — compare query results, audit columns
  - `dbt-date` — date spine generation, fiscal calendars

### 3. Package Health
- Check for outdated packages (compare installed vs latest)
- Verify packages are compatible with current dbt version
- Flag packages that haven't been updated in 12+ months

### 4. Add Package
When user wants to add a package:
1. Identify the package (hub.getdbt.com or git URL)
2. Add entry to `packages.yml`
3. Run `dbt deps`
4. Run `dbt parse` to verify no conflicts
5. Show available macros/tests from the new package

## Flow

1. Parse intent: install, update, add, list, or audit packages
2. Read `packages.yml` for current state
3. Execute `dbt deps` if installing/updating
4. Parse output for success/failure
5. Report installed packages with versions

## Error Recovery

- If `dbt deps` fails: check network connectivity, package URL validity, version compatibility
- If version conflict: suggest compatible version ranges
- If `packages.yml` missing: create one with recommended starter packages

## Conversation Principles

- NEVER ask about package.yml syntax or version pinning format
- ONLY ask: which package do you need, what functionality are you looking for
