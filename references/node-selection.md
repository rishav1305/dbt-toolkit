# Node Selection Reference

dbt's selector syntax lets you target specific resources (models, tests, sources, snapshots) for execution. Used with `--select` and `--exclude` flags.

## Selection Methods

### By Name

Select a specific resource by its name.

```bash
dbt run --select my_model
dbt test --select my_test
```

Exact matches only. Partial names are not supported.

---

### By Path

Select models by their file path.

```bash
dbt run --select path:models/staging
dbt run --select path:models/staging/stg_customers.sql
```

**Behavior:**
- `path:models/staging` matches all files in the directory and subdirectories
- `path:models/staging/stg_*.sql` supports glob patterns
- Matches model path relative to `model-paths` in `dbt_project.yml`

---

### By Tag

Select resources tagged with a specific tag.

```bash
dbt run --select tag:daily
dbt test --select tag:critical
```

Tags are defined in model config:

```sql
{{ config(tags=['daily', 'critical']) }}
```

---

### By Config

Select resources by their configuration.

```bash
dbt run --select config.materialized:incremental
dbt test --select config.schema:staging
dbt run --select config.pre_hook:my_macro
```

**Common config selectors:**
- `config.materialized:table|view|incremental|ephemeral`
- `config.schema:schema_name`
- `config.tags:tag_name`

---

### By Test Type

Select tests by their classification.

```bash
dbt test --select test_type:unit
dbt test --select test_type:generic
dbt test --select test_type:singular
```

**Test types:**
- `unit` — Unit tests (dbt 1.8+) defined inline in a model
- `generic` — Generic tests (e.g., `not_null`, `unique`)
- `singular` — Singular tests (custom SQL in `tests/` directory)

---

### By Source

Select sources and their dependents.

```bash
dbt test --select source:raw.customers
dbt run --select source:analytics.events+
```

Format: `source:schema_name.table_name`

**Include dependents:** Add `+` to run all models downstream of the source:
```bash
dbt run --select source:raw.events+
```

---

### By Exposure

Select exposures (dashboards, reports, etc.) and their upstream models.

```bash
dbt test --select exposure:my_dashboard
dbt run --select exposure:my_dashboard+
```

Useful for validating all data feeding into a dashboard.

---

### By Resource Type

Select only specific resource types.

```bash
dbt ls --select resource_type:model
dbt ls --select resource_type:test
dbt ls --select resource_type:source
dbt ls --select resource_type:snapshot
```

**Resource types:** `model`, `test`, `source`, `snapshot`, `seed`, `analysis`, `macro`, `exposure`, `metric`

---

### By Package

Select resources from a specific dbt package.

```bash
dbt run --select package:dbt_utils
```

Selects all models in the `dbt_utils` package (from `dbt_packages/`).

---

### By State

Select resources based on their state in a previous run (dbt 1.6+).

```bash
dbt run --select state:modified --state path/to/manifest.json
dbt run --select state:new --state path/to/manifest.json
```

**State options:**
- `state:modified` — Resources whose definition changed since the saved state
- `state:new` — Resources that don't exist in the saved state

**Requires:** Previous `manifest.json` at `--state` path (typically from a CI pipeline).

---

### By Result

Select resources based on the result of a previous run.

```bash
dbt retry  # Re-run all errors/failures
dbt run --select result:error,result:fail
```

**Result options:**
- `result:error` — Nodes with errors (compilation or execution)
- `result:fail` — Nodes with test failures
- `result:skipped` — Nodes that were skipped (rare)

---

## Graph Operators

Graph operators traverse the DAG (directed acyclic graph) to include upstream or downstream dependencies.

### Upstream Ancestors

**`+model`** — Model + all upstream dependencies.

```bash
dbt run --select +my_model
```

Runs `my_model` and everything it depends on (transitively).

**`+model,N`** — Model + N levels of ancestors (limited depth).

```bash
dbt run --select +my_model,2
```

Runs `my_model` and up to 2 levels of upstream dependencies.

---

### Downstream Descendants

**`model+`** — Model + all downstream dependents.

```bash
dbt run --select my_model+
```

Runs `my_model` and all models that depend on it (transitively).

**`model+N`** — Model + N levels of descendants (limited depth).

```bash
dbt run --select my_model+2
```

Runs `my_model` and up to 2 levels of downstream dependents.

---

### Both Directions

**`+model+`** — Model + ancestors + descendants.

```bash
dbt run --select +my_model+
```

Runs all models in the dependency chain (both upstream and downstream).

---

### All Relatives (AKA "The Star")

**`@model`** — Model + ancestors + descendants of ancestors.

```bash
dbt run --select @my_model
```

More conservative than `+model+`. Includes the model, its ancestors, and only the descendants of ancestors (not all descendants of the model itself).

**Useful for:** Validating an entire impact zone in CI.

---

## Set Operations

Combine selectors using spaces (union) and commas (intersection).

### Union (Space)

**`selector_a selector_b`** — Resources matching selector_a OR selector_b.

```bash
dbt run --select my_model another_model
dbt run --select tag:daily tag:critical
```

Runs all models with tag `daily` OR tag `critical`.

---

### Intersection (Comma)

**`selector_a,selector_b`** — Resources matching BOTH selector_a AND selector_b.

```bash
dbt run --select tag:daily,path:models/staging
```

Runs models tagged with `daily` AND in the `models/staging` path.

```bash
dbt test --select model_name,test_type:generic
```

Runs generic tests on a specific model.

---

### Exclusion

**`--exclude selector`** — Remove resources from the selection.

```bash
dbt run --select path:models/staging --exclude tag:skip
dbt run --select +my_model --exclude tag:experimental
```

Runs all staging models except those tagged `skip`.

---

## Named Selectors

Define reusable selector groups in `selectors.yml`.

```yaml
selectors:
  - name: daily_run
    description: All models and tests for daily execution
    definition:
      method: tag
      value: daily

  - name: staging_with_tests
    description: Staging models + their tests
    definition:
      union:
        - method: path
          value: models/staging
        - method: intersection
          selectors:
            - method: path
              value: models/staging
            - method: resource_type
              value: test

  - name: critical_path
    description: All ancestors and descendants of key models
    definition:
      method: intersection
      selectors:
        - method: path
          value: models/marts
        - method: tag
          value: critical
```

**Usage:**

```bash
dbt run --selector daily_run
dbt test --selector staging_with_tests
```

---

## Complex Examples

### Example 1: Staging models excluding experimental work

```bash
dbt run --select path:models/staging --exclude tag:experimental
```

Run all staging models except those tagged as experimental.

---

### Example 2: All upstream + downstream of a marts model

```bash
dbt run --select +marts.revenue_summary+
```

Execute the model, everything it depends on, and everything that depends on it.

---

### Example 3: All Redshift incremental models that failed in the last run

```bash
dbt retry --select config.materialized:incremental
```

Re-run failed incremental models.

---

### Example 4: Tests for modified sources (CI/CD)

```bash
dbt test --select source:* --state ci_state/manifest.json
```

Test all models and tests downstream of sources that changed.

---

### Example 5: All models tagged `daily` in the staging path

```bash
dbt run --select tag:daily,path:models/staging
```

Intersection: must be both daily and in staging.

---

## Quick Reference

| Selector | Purpose |
|----------|---------|
| `model_name` | Exact resource name |
| `path:models/staging` | By file path |
| `tag:daily` | By tag |
| `config.materialized:incremental` | By config property |
| `test_type:generic` | By test classification |
| `source:raw.customers` | By source |
| `exposure:dashboard_name` | By exposure |
| `resource_type:model` | By resource type |
| `package:dbt_utils` | By package |
| `state:modified` | By state diff (requires `--state`) |
| `result:error` | By previous run result |
| `+model` | Upstream + model |
| `model+` | Model + downstream |
| `+model+` | Upstream + model + downstream |
| `@model` | Star operator (model + ancestors + their descendants) |
| `selector_a selector_b` | Union (OR) |
| `selector_a,selector_b` | Intersection (AND) |
| `--exclude selector` | Remove from selection |
