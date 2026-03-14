# Jinja Context Reference

dbt exposes variables and functions through Jinja templating, allowing dynamic SQL generation.

## Core Reference Functions

### ref()

Reference another model or seed by name.

```sql
SELECT * FROM {{ ref('my_model') }}
```

**Behavior:**
- Compiles to the full table/view name at execution time
- Creates a dependency edge in the DAG
- Works with both source and target schemas
- Automatically passes dependencies to `dbt compile` and `dbt run`

**In tests and analyses:**

```sql
SELECT COUNT(*) FROM {{ ref('my_model') }}
```

---

### source()

Reference a source table defined in `sources.yml`.

```sql
SELECT * FROM {{ source('my_schema', 'my_table') }}
```

**Format:** `source(source_name, table_name)` as defined in YAML.

**Example YAML:**

```yaml
sources:
  - name: raw
    tables:
      - name: customers
```

**SQL:**

```sql
SELECT * FROM {{ source('raw', 'customers') }}
```

**Behavior:**
- Creates a dependency on the source (visible in DAG)
- Supports freshness checks (`dbt source freshness`)
- Enables lineage tracking from external systems

---

### this

Reference the current model's relation (table or view).

```sql
{{ config(materialized='incremental') }}

SELECT ...
FROM {{ ref('base_model') }}

{% if execute %}
  {% set build_time = run_started_at %}
  {% do log('Building ' ~ this.name ~ ' at ' ~ build_time) %}
{% endif %}
```

**Properties:**
- `this.name` — Model name
- `this.schema` — Target schema
- `this.database` — Target database
- `this.identifier` — Full relation name

Used in incremental models, post-hooks, and snapshots.

---

## Variables

### var()

Access project or command-line variables.

```sql
SELECT * FROM my_table
WHERE year = {{ var('year') }}
```

**With defaults:**

```sql
SELECT * FROM my_table
WHERE year = {{ var('year', 2024) }}
```

**Defined in `dbt_project.yml`:**

```yaml
vars:
  year: 2024
  region: North America
```

**Override at runtime:**

```bash
dbt run --vars '{"year": 2025, "region": Europe}'
```

---

### env_var()

Access environment variables.

```sql
SELECT * FROM my_table
WHERE api_key = '{{ env_var("API_KEY") }}'
```

**With defaults:**

```sql
SELECT * FROM my_table
LIMIT {{ env_var("LIMIT", 1000) }}
```

**Set in shell before running dbt:**

```bash
export API_KEY="my-secret-key"
export LIMIT=5000
dbt run
```

---

## Execution Context

### execute

Boolean flag indicating whether Jinja is running during parsing (False) or execution (True).

```sql
{% if execute %}
  {% set table_exists = run_query("SELECT 1 FROM " ~ this.name) %}
  {% do log("Table exists: " ~ table_exists) %}
{% endif %}

SELECT * FROM {{ ref('my_model') }}
```

**Use case:** Run queries only during execution, not during parsing.

**Common pattern:**

```jinja
{% if execute %}
  -- This runs during dbt run/test/build
  {% set query_result = run_query("SELECT COUNT(*) as cnt FROM my_table") %}
  {% set row_count = query_result.rows[0]['cnt'] %}
{% endif %}
```

---

### invocation_id

Unique identifier for the current dbt invocation.

```sql
SELECT
  '{{ invocation_id }}' as run_id,
  *
FROM {{ ref('my_model') }}
```

Useful for audit trails and run tracking.

---

### run_started_at

ISO 8601 timestamp when the current dbt run started.

```sql
SELECT
  '{{ run_started_at }}' as dbt_run_started_at,
  *
FROM {{ ref('my_model') }}
```

Example: `'2024-03-15T14:32:18.123456Z'`

---

### target

Information about the active target (connection configuration).

**Properties:**
- `target.name` — Target name (e.g., `dev`, `prod`)
- `target.schema` — Target schema
- `target.database` — Target database
- `target.type` — Adapter type (e.g., `redshift`, `snowflake`)
- `target.user` — Database user
- `target.host` — Database host

**Example:**

```sql
{% if target.name == 'prod' %}
  -- Production logic
  SELECT * FROM large_table LIMIT 10000
{% else %}
  -- Development logic
  SELECT * FROM small_table LIMIT 1000
{% endif %}
```

---

### model

Metadata about the current model.

**Properties:**
- `model.name` — Model name
- `model.config` — Model config dict
- `model.path` — Path to model SQL file
- `model.tags` — List of tags
- `model.meta` — Custom metadata dict

**Example:**

```sql
SELECT
  '{{ model.name }}' as model_name,
  '{{ model.path }}' as model_path,
  *
FROM {{ ref('my_model') }}
```

**Access custom metadata:**

```yaml
# In models/my_model.sql
{{ config(
    meta={
        'owner': 'analytics',
        'sla_hours': 24
    }
) }}
```

```jinja
{% set owner = model.meta.get('owner', 'unknown') %}
SELECT '{{ owner }}' as data_owner, * FROM ...
```

---

## Database Operations

### run_query()

Execute SQL and return results (only during execution phase).

```jinja
{% if execute %}
  {% set result = run_query("SELECT MAX(date) FROM {{ ref('my_model') }}") %}
  {% set max_date = result.rows[0][0] %}
  {% do log("Max date: " ~ max_date) %}
{% endif %}

SELECT * FROM {{ ref('my_model') }}
WHERE date >= '{{ max_date }}'
```

**Key points:**
- Only works when `execute` is True
- Returns a `agate.Table` object
- Access rows: `result.rows[index][column_index]` or `result.rows[index]['column_name']`
- Always include in `{% if execute %}` block

---

### log()

Log messages to console and logs.

```jinja
{% do log("Starting execution", info=True) %}

{% if execute %}
  {% set count = run_query("SELECT COUNT(*) FROM " ~ this.name).rows[0][0] %}
  {% do log("Row count: " ~ count, info=False) %}
{% endif %}
```

**Parameters:**
- `msg` — Message string
- `info=True` — Log level (True = INFO, False = DEBUG)

---

## Filters

Apply text transformations to values.

### as_number

Convert string to number.

```jinja
{% set value = "42" | as_number %}
SELECT * FROM my_table WHERE id > {{ value }}
```

---

### as_text

Convert value to string.

```jinja
{% set id = 123 | as_text %}
SELECT * FROM my_table WHERE customer_id = '{{ id }}'
```

---

## Modules

Access Python modules through dbt's Jinja context.

### modules.datetime

Date/time operations.

```jinja
{% set now = modules.datetime.datetime.now() %}
{% set today = modules.datetime.date.today() %}

SELECT
  '{{ now }}' as execution_time,
  '{{ today }}' as execution_date,
  *
FROM {{ ref('my_model') }}
```

---

### modules.re

Regular expressions.

```jinja
{% if modules.re.search('error', log_message) %}
  -- Log contains error
{% endif %}

SELECT * FROM {{ ref('my_model') }}
WHERE {{ modules.re.sub('_old$', '_new', column_name) }} IS NOT NULL
```

**Common methods:**
- `modules.re.search(pattern, string)` — Search for pattern
- `modules.re.match(pattern, string)` — Match at string start
- `modules.re.sub(pattern, replacement, string)` — Replace occurrences
- `modules.re.findall(pattern, string)` — Find all matches

---

## Common Patterns

### Conditional Logic by Environment

```sql
{% if target.name == 'prod' %}
  SELECT * FROM large_production_table
{% else %}
  SELECT * FROM small_dev_table LIMIT 1000
{% endif %}
```

---

### Dynamic Date Filtering

```jinja
{% if execute %}
  {% set max_date = run_query("SELECT MAX(date) FROM {{ ref('facts') }}").rows[0][0] %}
{% else %}
  {% set max_date = '2024-01-01' %}
{% endif %}

SELECT * FROM {{ ref('my_model') }}
WHERE date > '{{ max_date }}'
```

---

### Model-Dependent Configuration

```yaml
# dbt_project.yml
models:
  my_project:
    marts:
      +materialized: table
    staging:
      +materialized: view
```

---

### Loop Over Multiple Models

```jinja
{%- set models = ['model1', 'model2', 'model3'] -%}

{%- for model_name in models %}
  SELECT '{{ model_name }}' as source, * FROM {{ ref(model_name) }}
  {%- if not loop.last %} UNION ALL {% endif %}
{%- endfor %}
```

---

### Use Custom Metadata

```yaml
{{ config(
    meta={
        'owner': 'analytics',
        'domain': 'finance',
        'refresh_freq': 'daily'
    }
) }}
```

```jinja
{% set owner = model.meta.get('owner', 'unknown') %}
{% set freq = model.meta.get('refresh_freq', 'unknown') %}

SELECT
  '{{ owner }}' as owner,
  '{{ freq }}' as refresh_frequency,
  *
FROM ...
```

---

## Quick Reference

| Item | Purpose |
|------|---------|
| `{{ ref('model') }}` | Reference another model |
| `{{ source('schema', 'table') }}` | Reference a source |
| `{{ this }}` | Current model relation |
| `{{ var('name', default) }}` | Project/CLI variable |
| `{{ env_var('ENV_VAR', default) }}` | Environment variable |
| `{{ execute }}` | True during execution, False during parse |
| `{{ invocation_id }}` | Unique run ID |
| `{{ run_started_at }}` | Run start timestamp |
| `{{ target.name }}` | Active target name |
| `{{ target.schema }}` | Target schema |
| `{{ target.type }}` | Adapter type |
| `{{ model.name }}` | Current model name |
| `{{ model.config }}` | Model config dict |
| `{{ run_query(sql) }}` | Execute SQL during execution |
| `{{ log(msg, info=True) }}` | Log message |
| `{{ value \| as_number }}` | Convert to number |
| `{{ value \| as_text }}` | Convert to string |
| `{{ modules.datetime.datetime.now() }}` | Current datetime |
| `{{ modules.re.search(pattern, string) }}` | Regex search |
