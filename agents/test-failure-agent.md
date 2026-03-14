# Test Failure Agent

Specialized subagent for root-cause analysis of failing tests.

## Input

- `test_name`: The failing test unique_id
- `run_results`: Relevant portion of run_results.json with error details
- `compiled_sql`: The compiled test SQL (from `target/compiled/` or `run_results.json` `compiled_code` field)

## Method

1. **Read the compiled test SQL** to understand what assertion is being checked
2. **Identify the upstream model** from the test's `depends_on` in manifest
3. **Check git log** for recent changes to the upstream model:
   ```bash
   git log --oneline -5 -- models/path/to/model.sql
   ```
4. **Read the model SQL** to understand the transformation logic
5. **Form hypothesis:** What changed that could cause the test to fail?
6. **Suggest fix:** Concrete code change or data investigation

## Output Format

```
Test: test.proj.not_null_stg_audience__user_id
Status: FAIL (12 rows returned)

Root Cause Analysis:
  The upstream model `stg_audience_metrics` was modified 2 hours ago (commit abc123).
  The change added a LEFT JOIN to `dim_users` which can produce NULL user_ids
  when there is no matching user record.

Suggested Fix:
  Option A: Add COALESCE(u.user_id, a.user_id) to preserve the original user_id
  Option B: Change LEFT JOIN to INNER JOIN if unmatched users should be excluded

Compiled Test SQL:
  SELECT user_id FROM stg_audience_metrics WHERE user_id IS NULL
```

## Used By

- `dbt-test` — dispatched automatically on test failure
- `dbt-debug` — test failure category
