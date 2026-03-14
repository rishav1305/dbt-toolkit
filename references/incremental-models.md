# Incremental Models Reference

Incremental models process only new or changed data on each run, enabling efficient pipelines for large datasets.

## Overview

An incremental model:
- On the **first run:** Creates a full table (equivalent to `--full-refresh`)
- On **subsequent runs:** Appends or upserts only new/modified data
- Returns `is_incremental()` = False on first run, True on subsequent runs

Basic structure:

```sql
{{ config(materialized='incremental') }}

SELECT ...
FROM source_table

{% if is_incremental() %}
  WHERE created_at > (SELECT MAX(created_at) FROM {{ this }})
{% endif %}
```

---

## 5 Incremental Strategies

### Strategy 1: append

Insert all selected rows into the table. No deduplication or deletion.

```yaml
{{ config(
    materialized='incremental',
    incremental_strategy='append'
) }}
```

**Pros:**
- Simplest to implement
- Fastest (single INSERT)

**Cons:**
- No dedup — duplicate rows accumulate
- Not suitable for upsert patterns
- Can lead to inflated tables

**Use case:** Immutable event logs or fact tables where duplicates are acceptable.

---

### Strategy 2: delete+insert

Delete all rows matching the new data, then insert new rows. Default for Redshift.

```yaml
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='id'
) }}
```

**How it works:**
1. Identifies rows in new/incremental data (staging table)
2. Deletes matching rows from the target table using `unique_key`
3. Inserts all rows from staging

**DELETE logic:**
```sql
WHERE unique_key IN (SELECT unique_key FROM staging_table)
```

**Pros:**
- Handles upserts and schema changes
- Industry standard for most databases
- Simple to understand

**Cons:**
- **NULL in unique_key breaks dedup:** `NULL IN (...)` never matches, so rows with NULL unique_key are never deleted → duplicates
- Two passes (delete + insert) slower than merge on some systems

**Critical gotcha:** If `unique_key` has NULL values, those rows will duplicate on each run.

**Always add a `not_null` test:**

```yaml
- name: my_incremental_model
  tests:
    - unique:
        column_name: id
    - not_null:
        column_name: id  # Ensure unique_key has no NULLs
```

---

### Strategy 3: merge

SQL MERGE statement (upsert in a single pass).

```yaml
{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='id'
) }}
```

**Pros:**
- Single atomic operation
- Handles duplicates and updates in one pass
- Industry standard for OLTP

**Cons:**
- **Not supported on Redshift** — Redshift lacks MERGE syntax
- Not all databases support it

**Supported on:** Snowflake, BigQuery, Postgres, DuckDB, etc.

---

### Strategy 4: insert_overwrite

Replace entire partitions of data. Best for date-partitioned tables.

```yaml
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by='date_column'
) }}
```

**How it works:**
1. Computes the partition key from new data (e.g., today's date)
2. Deletes all rows for that partition from the target table
3. Inserts new rows for that partition

**Example (daily data):**

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by=['date(created_at)']
) }}

SELECT *
FROM raw_events
{% if is_incremental() %}
  WHERE DATE(created_at) = CURRENT_DATE
{% endif %}
```

**Pros:**
- Efficient for time-series data
- Handles late-arriving data and corrections
- No unique_key needed

**Cons:**
- Entire partition is replaced (slower if many changes)
- Requires a partition column

**Use case:** Daily/hourly fact tables where you always recompute the latest partitions.

---

### Strategy 5: microbatch (dbt 1.9+)

Process new data in time-based batches automatically.

```yaml
{{ config(
    materialized='incremental',
    incremental_strategy='microbatch',
    event_time='created_at'
) }}
```

**How it works:**
- dbt automatically divides the data into batches (default 24 hours)
- Processes each batch through your model
- Upserts results using `unique_key`

**Pros:**
- Automatic partitioning
- Reduces memory pressure on large datasets
- dbt handles orchestration

**Cons:**
- Newer (1.9+), less widely adopted
- Requires `unique_key` and `event_time` column

---

## unique_key Configuration

The `unique_key` column(s) identify rows for dedup/upsert operations.

### Single column

```yaml
{{ config(
    materialized='incremental',
    unique_key='customer_id'
) }}
```

### Multiple columns (composite key)

```yaml
{{ config(
    materialized='incremental',
    unique_key=['customer_id', 'order_id']
) }}
```

Rows are considered duplicates only if ALL columns match.

---

## Critical: NULL in unique_key

**Problem:** `delete+insert` strategy uses `WHERE unique_key IN (...)` to delete existing rows. NULL never matches IN:

```sql
WHERE id IN (1, 2, NULL)
-- This will match id=1 and id=2, but NOT NULL values
```

**Result:** Rows with NULL in the unique_key are NEVER deleted → duplicates on every run.

**Solution:** Add `not_null` test on all unique_key columns:

```yaml
tests:
  - not_null:
      column_name: id
```

Or prevent NULL in the column:

```sql
SELECT
  COALESCE(id, GENERATE_UUID()) as id,
  ...
FROM source
```

---

## on_schema_change

Controls how incremental models handle schema changes in the source.

### ignore (default)

Ignore new columns in the source. They are not added to the target table.

```yaml
{{ config(
    on_schema_change='ignore'
) }}
```

**Behavior:**
- New columns in source → ignored
- Dropped columns in source → ignored
- Existing columns → used as-is

---

### append_new_columns

Add new columns to the target table with NULL for existing rows.

```yaml
{{ config(
    on_schema_change='append_new_columns'
) }}
```

**Behavior:**
- New columns → added to table
- Old rows → NULL in new columns
- Existing columns → updated with new data

---

### sync_all_columns

Sync table schema to match the SELECT statement exactly. Adds new columns, removes old ones.

```yaml
{{ config(
    on_schema_change='sync_all_columns'
) }}
```

**Behavior:**
- Columns in SELECT → added to table (or retained)
- Columns not in SELECT → removed from table
- Highest risk for data loss

---

### fail

Raise an error if the schema changes. Requires manual intervention.

```yaml
{{ config(
    on_schema_change='fail'
) }}
```

**Behavior:**
- Schema change detected → error
- No data is written
- Forces you to resolve the schema change manually

---

## When to --full-refresh

Force a full table rebuild instead of incremental processing.

```bash
dbt run --select my_incremental_model --full-refresh
```

### When you should full-refresh:

1. **Logic changed significantly** — WHERE condition or major calculation changed
   ```bash
   dbt run --select my_incremental_model --full-refresh
   ```

2. **unique_key changed** — Old unique_key no longer identifies rows uniquely
   ```bash
   # Don't: just run with new unique_key
   dbt run --select my_incremental_model --full-refresh
   ```

3. **on_schema_change: ignore** — If you ignored schema changes and now need to catch up
   ```bash
   dbt run --select my_incremental_model --full-refresh
   ```

4. **Data quality issue** — Discovered data corruption or duplicates
   ```bash
   dbt run --select my_incremental_model --full-refresh
   ```

5. **Redshift VACUUM needed** — After massive deletes, table bloats. Full refresh reclaims space.
   ```bash
   dbt run --select my_incremental_model --full-refresh
   ```

---

## Debugging Incremental Models

### Check if model ran incrementally

```bash
dbt run --select my_incremental_model --debug
```

Look for the incremental WHERE clause in compiled SQL (in `target/compiled/`).

### View last incremental state

```bash
dbt run-operation show_last_incremental_state --args '{"model": "my_incremental_model"}'
```

(If you've defined this macro.)

### Force parse without running

```bash
dbt parse --select my_incremental_model
```

Verify the model structure and config without executing.

---

## Common Patterns

### Incremental with SCD Type 2 (Slowly Changing Dimension)

```sql
{{ config(
    materialized='incremental',
    unique_key='customer_id',
    on_schema_change='append_new_columns'
) }}

SELECT
  customer_id,
  name,
  email,
  CURRENT_TIMESTAMP as effective_from,
  CAST('9999-12-31' AS TIMESTAMP) as effective_to,
  TRUE as is_current
FROM {{ source('raw', 'customers') }}

{% if is_incremental() %}
  WHERE customer_id IN (
    SELECT DISTINCT customer_id FROM {{ source('raw', 'customers') }}
    WHERE updated_at > (SELECT MAX(effective_from) FROM {{ this }})
  )
{% endif %}
```

---

### Incremental with Lookback Window

Reprocess last N days to catch late-arriving data:

```sql
{{ config(
    materialized='incremental',
    unique_key='event_id'
) }}

SELECT *
FROM {{ source('raw', 'events') }}

{% if is_incremental() %}
  WHERE created_at > (SELECT MAX(created_at) - INTERVAL '2 days' FROM {{ this }})
{% else %}
  WHERE created_at > CAST('2020-01-01' AS TIMESTAMP)
{% endif %}
```

---

### Test for duplicates in incremental model

```yaml
- name: my_incremental_model
  tests:
    - unique:
        column_name: id
    - dbt_utils.recency:
        datepart: day
        field: updated_at
        interval: 1
```

---

## Quick Reference: Strategy Comparison

| Strategy | Delete+Insert | Merge | Insert Overwrite | Append | Microbatch |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Redshift Support** | ✓ (default) | ✗ | ✓ | ✓ | ✓ (1.9+) |
| **Requires unique_key** | ✓ | ✓ | ✗ | ✗ | ✓ |
| **NULL in unique_key OK** | ✗ | ✗ | N/A | N/A | ✗ |
| **Handles updates** | ✓ | ✓ | ✓ | ✗ | ✓ |
| **Speed** | Good | Fast | Good | Very Fast | Good |
| **Complexity** | Low | Medium | Medium | Very Low | Medium |
| **Use Case** | Standard upsert | OLTP systems | Time-series | Append-only logs | Large datasets |
