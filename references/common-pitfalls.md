# Common dbt Pitfalls Reference

Real-world problems and how to avoid them.

## 1. NULL in unique_key causes duplicates (delete+insert strategy)

### The Problem

The `delete+insert` incremental strategy uses `WHERE unique_key IN (...)` to delete existing rows before inserting new ones.

```sql
DELETE FROM my_table WHERE id IN (SELECT id FROM new_data);
INSERT INTO my_table SELECT * FROM new_data;
```

**Critical issue:** NULL never matches IN:

```sql
NULL IN (1, 2, NULL)  -- FALSE (not TRUE!)
```

**Result:** Rows with NULL in the unique_key are NEVER deleted. On every run, those rows duplicate.

### Example

```sql
{{ config(
    materialized='incremental',
    unique_key='customer_id'
) }}

SELECT
  customer_id,
  event_data
FROM raw_events
```

If `raw_events` has rows with `customer_id = NULL`, running this twice creates duplicates:

```
Run 1: Insert rows (including NULL customer_id)
Run 2: Delete rows WHERE customer_id IN (...)
       → NULL rows NOT deleted
       → Insert new rows (including NULL again)
       → Result: 2 copies of NULL rows
```

### Solution

**Add NOT NULL test on the unique_key column:**

```yaml
tests:
  - unique:
      column_name: customer_id
  - not_null:
      column_name: customer_id
```

Or prevent NULL in your code:

```sql
SELECT
  COALESCE(customer_id, GENERATE_UUID()) as customer_id,
  event_data
FROM raw_events
```

---

## 2. Redshift regex: \\d doesn't work

### The Problem

Redshift POSIX regex does NOT support `\d` (digit shortcut).

```sql
-- In Python/SQL: \d+ matches digits
-- Redshift: silently matches 0 rows
SELECT * FROM my_table WHERE col ~ '\d+';  -- Returns no rows!
```

Even in Jinja with double backslash:

```jinja
-- FAILS (compiles to \d which Redshift doesn't support)
WHERE col ~ '\\d+'
```

### Solution

Use character classes instead:

```sql
-- WORKS
SELECT * FROM my_table WHERE col ~ '[0-9]+';

-- In Jinja
WHERE col ~ '[0-9]+'
```

### Why this matters

Your query runs without error but returns 0 rows. You spend hours debugging, thinking the data is missing, when actually the regex is silently failing.

---

## 3. Non-interactive SSH doesn't source .bashrc

### The Problem

When running a command via SSH without a TTY (non-interactive), `.bashrc` is NOT sourced automatically:

```bash
ssh host "command"  # .bashrc not sourced
```

If environment variables are set in `.bashrc`, they won't be available:

```bash
ssh 54.157.108.162 "dbt run"
# Error: DBT_REDSHIFT_PASSWORD not found (even though it's in .bashrc)
```

### Solution

Explicitly export variables in the remote command:

```bash
ssh 54.157.108.162 "export DBT_REDSHIFT_USER='user' && export DBT_REDSHIFT_PASSWORD='pass' && dbt run"
```

Or source .bashrc manually:

```bash
ssh 54.157.108.162 "source ~/.bashrc && dbt run"
```

### In dbt projects

Add to your `profiles.yml` or set environment variables before running dbt:

```bash
export DBT_REDSHIFT_USER='mparticle_dbt_rw'
export DBT_REDSHIFT_PASSWORD='XpT4#gVnL9z2qBwK'
dbt run
```

---

## 4. dbt show: --select vs --inline mutual exclusion

### The Problem

`dbt show` has two ways to specify what to preview:

- `dbt show --select model_name` — Preview a model
- `dbt show --inline "SELECT ..."` — Preview raw SQL

**You cannot use both at the same time:**

```bash
dbt show --select my_model --inline "SELECT * FROM ..."
# Error: --select and --inline are mutually exclusive
```

### Solution

Choose one approach:

```bash
# Option 1: Preview a model
dbt show --select my_model

# Option 2: Preview raw SQL
dbt show --inline "SELECT * FROM {{ ref('my_table') }}"
```

---

## 5. dbt show doesn't support Python models

### The Problem

`dbt show` only works with SQL models:

```bash
dbt show --select my_python_model
# Error: dbt show is not supported for Python models
```

### Solution

Preview Python models by:
1. Converting to SQL (if possible)
2. Running a test that executes the model
3. Querying the output table directly in your data warehouse

---

## 6. Spectrum CTAS collision: branching pattern

### The Problem

When reading from Redshift Spectrum external tables in a branching CTE pattern:

```sql
WITH spectrum_data AS (
  SELECT * FROM external_s3_table
),
branch_a AS (
  SELECT col1, col2 FROM spectrum_data
),
branch_b AS (
  SELECT col3, col4 FROM spectrum_data
)
SELECT * FROM branch_a UNION ALL SELECT * FROM branch_b;
-- ERROR: Relation already exists
```

Redshift creates duplicate internal staging relations for each branch → collision.

### Solution

Ensure the Spectrum table is scanned only once via linear CTE + CROSS JOIN unpivot:

```sql
WITH spectrum_data AS (
  SELECT * FROM external_s3_table
),
unpivoted AS (
  SELECT col1, col2, col3, col4, col5
  FROM spectrum_data
  CROSS JOIN (SELECT DISTINCT 1 AS _unused) AS marker
)
SELECT col1, col2 FROM unpivoted
UNION ALL
SELECT col3, col4 FROM unpivoted;
```

Or pre-materialize the Spectrum read:

```sql
WITH spectrum_staging AS (
  SELECT *
  FROM external_s3_table
),
branch_a AS (
  SELECT col1, col2 FROM spectrum_staging
),
branch_b AS (
  SELECT col3, col4 FROM spectrum_staging
)
SELECT * FROM branch_a UNION ALL SELECT * FROM branch_b;
```

---

## 7. Incremental model first run: is_incremental() returns False

### The Problem

On the very first run of an incremental model, the `is_incremental()` macro returns False (the table doesn't exist yet):

```sql
{{ config(materialized='incremental') }}

SELECT *
FROM source_table

{% if is_incremental() %}
  WHERE created_at > (SELECT MAX(created_at) FROM {{ this }})
{% else %}
  -- First run: loads full history
  WHERE created_at >= '2020-01-01'
{% endif %}
```

**On first run:**
- `is_incremental()` = False
- Entire source is loaded (full history since 2020)
- Table is created

**On subsequent runs:**
- `is_incremental()` = True
- Only new rows since last run are loaded
- Table is updated

This is intentional and correct behavior, but can surprise if you're not aware.

### Gotcha

If your source_table only has data from yesterday, and you expect the model to load everything on first run, make sure your WHERE clause allows it:

```sql
WHERE created_at >= '2020-01-01'  -- OK for first run
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'  -- Might miss old data on first run
```

---

## 8. dbt deps must run before dbt parse

### The Problem

If your `packages.yml` references external packages, `dbt parse` or `dbt compile` will fail if `dbt deps` hasn't been run:

```bash
dbt compile
# Error: Package my_package not found
```

### Solution

Run `dbt deps` first:

```bash
dbt deps && dbt compile
```

Or combine:

```bash
dbt build  # Automatically runs deps
```

---

## 9. Stale run_results.json persists

### The Problem

`run_results.json` persists from the last execution. If you run `dbt compile`, it does NOT update `run_results.json` (compile doesn't execute).

```bash
dbt run  # Generates run_results.json with results
dbt compile  # Parse/compile only, does NOT update run_results.json
dbt retry  # Uses stale run_results.json from last run!
```

**Scenario:**
1. `dbt run` fails on model A and model B
2. You fix model A
3. `dbt compile` passes (but doesn't update run_results.json)
4. `dbt retry` re-runs A and B (from stale results), not just A

### Solution

Only use `dbt retry` immediately after a failed `dbt run/test/build`:

```bash
dbt run --select model_a model_b  # Fails on B
# Fix model B
dbt run --select model_b  # Don't use retry; run B directly
```

Or delete the stale file:

```bash
rm target/run_results.json
dbt compile
```

---

## 10. dbt retry reads run_results.json

### The Problem

`dbt retry` targets nodes with `error` or `fail` status from the most recent `run_results.json`.

If that file is stale or from a different branch, you may retry wrong nodes:

```bash
# Main branch
dbt run --select model_a  # Succeeds, writes run_results.json

# Switch to feature branch
git checkout feature-branch  # Different models

dbt retry  # Re-runs based on MAIN branch's results!
```

### Solution

Run the full command instead of retry when switching branches:

```bash
git checkout feature-branch
dbt run --select path:models/staging
```

---

## Quick Checklist

Before running dbt in production:

- [ ] **unique_key has no NULLs** — Add `not_null` test
- [ ] **Regex uses [0-9], not \d** — Redshift doesn't support \d
- [ ] **SSH exports env vars** — Non-interactive SSH doesn't source .bashrc
- [ ] **No branching Spectrum queries** — Use linear CTE + unpivot
- [ ] **Incremental model has date filter** — For both `is_incremental()` branches
- [ ] **dbt deps ran before compile** — Packages must be installed
- [ ] **run_results.json is fresh** — Delete if stale, don't rely on retry
- [ ] **Sort keys are defined** — Redshift performance optimization
- [ ] **NOT NULL tests on key columns** — Prevent incremental duplicates
